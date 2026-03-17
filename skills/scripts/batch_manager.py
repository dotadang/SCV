#!/usr/bin/env python3
"""
SCV Batch Manager - External state manager for batchRun orchestration.

Solves the fundamental limitation of pure-prompt batch execution: the LLM
loses track of batch state mid-execution as context grows. This script acts
as a persistent state machine stored on disk (keyed by session_id), so the
orchestrating agent never has to rely on in-context memory for batch state.

Usage:
  python batch_manager.py plan     --session <id> --config <path>
  python batch_manager.py next     --session <id>
  python batch_manager.py complete --session <id> --repo <name>
  python batch_manager.py fail     --session <id> --repo <name> [--error <msg>]
  python batch_manager.py status   --session <id>
  python batch_manager.py done     --session <id>
  python batch_manager.py resume   --session <id>
  python batch_manager.py list
  python batch_manager.py cleanup  [--older-than <days>]

State file location: ~/.scv/sessions/{session_id}.json
"""

import argparse
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from git_op import extract_repo_name, prepare_repo, get_head_commit, is_git_repo
from scv_util import should_skip_analysis, write_metadata

DEFAULT_BATCH_SIZE = 5
SESSIONS_DIR = Path.home() / ".scv" / "sessions"
REPOS_DIR = Path.home() / ".scv" / "repos"


def session_path(session_id: str) -> Path:
    return SESSIONS_DIR / f"{session_id}.json"


def load_state(session_id: str) -> dict:
    path = session_path(session_id)
    if not path.exists():
        _die(f"Session not found: {session_id}\n  Expected: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state: dict) -> None:
    path = session_path(state["session_id"])
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = _now()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _die(msg: str, code: int = 1) -> None:
    print(json.dumps({"error": msg}))
    sys.exit(code)


def _ok(data: dict) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def _find_repo(state: dict, identifier: str):
    identifier_lower = identifier.lower()
    for r in state["repos"]:
        if (
            r["project_name"].lower() == identifier_lower
            or r["repo_name"].lower() == identifier_lower
        ):
            return r
    return None


def _maybe_close_batch(state: dict) -> None:
    current_batch = next(
        (b for b in state["batches"] if b["status"] == "in_progress"), None
    )
    if current_batch is None:
        return
    repos_by_id = {r["id"]: r for r in state["repos"]}
    settled = {"done", "failed", "skipped"}
    all_settled = all(
        repos_by_id[rid]["status"] in settled for rid in current_batch["repo_ids"]
    )
    if all_settled:
        current_batch["status"] = "done"


def _summary(state: dict) -> dict:
    repos = state["repos"]
    total = len(repos)
    done = sum(1 for r in repos if r["status"] == "done")
    failed = sum(1 for r in repos if r["status"] == "failed")
    skipped = sum(1 for r in repos if r["status"] == "skipped")
    pending = sum(1 for r in repos if r["status"] == "pending")
    return {
        "total": total,
        "done": done,
        "failed": failed,
        "skipped": skipped,
        "pending": pending,
    }


def _git_prepare(repo: dict, analyze_only: bool) -> tuple[bool, str, str]:
    repo_name = repo["repo_name"]
    local_path = REPOS_DIR / repo_name
    return prepare_repo(repo, REPOS_DIR, analyze_only)


def cmd_plan(args):
    """
    Read config, run git clone/pull for all repos, build batch plan, persist to session file.

    This replaces the old `init` command. The LLM no longer needs to:
    - Parse repos from config
    - Run git operations
    - Calculate batch splits

    All of that happens here. The LLM only calls `next` to get each batch.
    """
    config_path = Path(args.config).expanduser()
    if not config_path.exists():
        _die(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    repos_raw = config.get("repos", [])
    if not repos_raw:
        _die("Config has no repos defined.")

    batch_size = config.get("batch_size", DEFAULT_BATCH_SIZE)
    analyze_only = getattr(args, "analyze_only", False)
    output_dir = config.get("output_dir", "~/.scv/analysis")

    repos = []
    git_errors = []
    skipped_repos = []

    for i, r in enumerate(repos_raw):
        repo_name = extract_repo_name(r)
        success, local_path, message = _git_prepare(
            {**r, "repo_name": repo_name}, analyze_only
        )

        current_commit = None
        skip_reason = None

        if success and local_path:
            local_path_obj = Path(local_path)
            if is_git_repo(local_path_obj):
                current_commit = get_head_commit(local_path_obj)

                if current_commit:
                    project_output_dir = Path(output_dir).expanduser() / repo_name
                    should_skip, reason = should_skip_analysis(
                        project_output_dir, current_commit
                    )

                    if should_skip:
                        skip_reason = reason
                        skipped_repos.append({"repo": repo_name, "reason": reason})

        initial_status = "pending"
        if not success:
            initial_status = "failed"
        elif skip_reason:
            initial_status = "skipped"

        entry = {
            "id": i,
            "project_name": r.get("project_name", repo_name),
            "repo_name": repo_name,
            "type": r.get("type", "local"),
            "url": r.get("url"),
            "branch": r.get("branch", "main"),
            "local_path": local_path if success else None,
            "git_message": message,
            "current_commit": current_commit,
            "status": initial_status,
            "error": None if success else message,
            "skip_reason": skip_reason,
            "completed_at": None,
        }
        repos.append(entry)

        if not success:
            git_errors.append({"repo": repo_name, "error": message})
            print(
                json.dumps({"git_warning": f"[{repo_name}] {message}"}),
                file=sys.stderr,
            )

    pending_repos = [r for r in repos if r["status"] == "pending"]

    batches = []
    pending_ids = [r["id"] for r in pending_repos]
    for batch_idx in range(math.ceil(len(pending_ids) / batch_size)):
        start = batch_idx * batch_size
        end = min(start + batch_size, len(pending_ids))
        batches.append(
            {
                "batch_num": batch_idx + 1,
                "repo_ids": pending_ids[start:end],
                "status": "pending",
            }
        )

    state = {
        "session_id": args.session,
        "created_at": _now(),
        "updated_at": _now(),
        "config_path": str(config_path),
        "batch_size": batch_size,
        "analyze_only": analyze_only,
        "parallel": config.get("parallel", True),
        "fail_fast": config.get("fail_fast", False),
        "output_dir": output_dir,
        "repos": repos,
        "batches": batches,
        "current_batch_num": 0,
    }

    save_state(state)

    _ok(
        {
            "status": "planned",
            "session_id": args.session,
            "total_repos": len(repos),
            "ready_repos": len(pending_repos),
            "failed_repos": len(git_errors),
            "skipped_repos": len(skipped_repos),
            "total_batches": len(batches),
            "batch_size": batch_size,
            "git_errors": git_errors,
            "skipped": skipped_repos,
            "state_file": str(session_path(args.session)),
        }
    )


def cmd_next(args):
    """
    Return the repos for the next pending batch and mark it in_progress.
    If the current batch is still in_progress, return those repos instead
    (idempotent - safe to call again after a crash).

    Exit code:
      0  - returned a batch (check 'repos' in JSON output)
      2  - no more batches (all done or fail_fast triggered)
    """
    state = load_state(args.session)
    batches = state["batches"]
    repos_by_id = {r["id"]: r for r in state["repos"]}

    in_progress = next((b for b in batches if b["status"] == "in_progress"), None)
    if in_progress:
        batch = in_progress
    else:
        batch = next((b for b in batches if b["status"] == "pending"), None)
        if batch is None:
            _ok({"status": "no_more_batches", "all_done": True})
            sys.exit(2)
        batch["status"] = "in_progress"
        state["current_batch_num"] = batch["batch_num"]
        save_state(state)

    batch_repos = [repos_by_id[rid] for rid in batch["repo_ids"]]
    skipped_count = sum(1 for r in state["repos"] if r["status"] == "skipped")

    _ok(
        {
            "status": "batch_ready",
            "batch_num": batch["batch_num"],
            "total_batches": len(batches),
            "batch_size": state["batch_size"],
            "output_dir": state["output_dir"],
            "skipped_count": skipped_count,
            "repos": batch_repos,
        }
    )


def cmd_complete(args):
    """Mark a single repo as done within the current batch and update metadata."""
    state = load_state(args.session)
    repo = _find_repo(state, args.repo)
    if repo is None:
        _die(f"Repo not found: {args.repo}")
        return

    repo["status"] = "done"
    repo["completed_at"] = _now()

    if repo.get("current_commit") and repo.get("local_path"):
        output_dir = Path(state["output_dir"]).expanduser() / repo["repo_name"]
        write_metadata(
            output_dir,
            repo["current_commit"],
            repo["local_path"],
        )

    _maybe_close_batch(state)
    save_state(state)
    _ok({"status": "repo_marked_done", "repo": args.repo, **_summary(state)})


def cmd_fail(args):
    """Mark a single repo as failed."""
    state = load_state(args.session)
    repo = _find_repo(state, args.repo)
    if repo is None:
        _die(f"Repo not found: {args.repo}")
        return

    repo["status"] = "failed"
    repo["error"] = args.error or "unknown error"
    repo["completed_at"] = _now()

    _maybe_close_batch(state)

    if state.get("fail_fast"):
        for r in state["repos"]:
            if r["status"] == "pending":
                r["status"] = "skipped"
        for b in state["batches"]:
            if b["status"] == "pending":
                b["status"] = "skipped"

    save_state(state)
    _ok({"status": "repo_marked_failed", "repo": args.repo, **_summary(state)})


def cmd_status(args):
    """Print a human-readable progress summary."""
    state = load_state(args.session)
    summary = _summary(state)
    current_batch = next(
        (b for b in state["batches"] if b["status"] == "in_progress"), None
    )

    _ok(
        {
            "session_id": args.session,
            "state_file": str(session_path(args.session)),
            "current_batch": current_batch["batch_num"] if current_batch else None,
            "total_batches": len(state["batches"]),
            "batch_size": state["batch_size"],
            **summary,
        }
    )


def cmd_done(args):
    """
    Check whether all repos have been processed.
    Exit 0 = all done (or fail_fast triggered).
    Exit 1 = still work remaining.
    """
    state = load_state(args.session)
    pending = [r for r in state["repos"] if r["status"] == "pending"]
    in_progress_batch = next(
        (b for b in state["batches"] if b["status"] == "in_progress"), None
    )

    if not pending and in_progress_batch is None:
        _ok({"done": True, **_summary(state)})
        sys.exit(0)
    else:
        _ok({"done": False, "pending_repos": len(pending), **_summary(state)})
        sys.exit(1)


def cmd_resume(args):
    """
    Useful after a crash: show what is still pending / in-progress.
    Does NOT modify state - purely read.
    """
    state = load_state(args.session)
    in_progress_batch = next(
        (b for b in state["batches"] if b["status"] == "in_progress"), None
    )
    pending_repos = [r for r in state["repos"] if r["status"] == "pending"]
    failed_repos = [r for r in state["repos"] if r["status"] == "failed"]

    repos_by_id = {r["id"]: r for r in state["repos"]}
    in_progress_repos = []
    if in_progress_batch:
        in_progress_repos = [
            repos_by_id[rid]
            for rid in in_progress_batch["repo_ids"]
            if repos_by_id[rid]["status"] == "pending"
        ]

    _ok(
        {
            "session_id": args.session,
            "in_progress_batch": in_progress_batch,
            "repos_still_running": in_progress_repos,
            "pending_repos": pending_repos,
            "failed_repos": failed_repos,
            **_summary(state),
        }
    )


def cmd_list(args):
    """List all sessions."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    sessions = []
    for path in sorted(SESSIONS_DIR.glob("*.json")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                s = json.load(f)
            sessions.append(
                {
                    "session_id": s["session_id"],
                    "created_at": s.get("created_at"),
                    "updated_at": s.get("updated_at"),
                    "state_file": str(path),
                    **_summary(s),
                }
            )
        except Exception as e:
            sessions.append({"state_file": str(path), "error": str(e)})

    _ok({"sessions": sessions})


def cmd_cleanup(args):
    """Remove session files older than N days (default 7)."""
    from datetime import timedelta

    max_age_days = args.older_than or 7
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    removed = []

    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    for path in SESSIONS_DIR.glob("*.json"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                s = json.load(f)
            updated_raw = s.get("updated_at") or s.get("created_at")
            if updated_raw:
                updated = datetime.fromisoformat(updated_raw)
                if updated < cutoff:
                    path.unlink()
                    removed.append(str(path))
        except Exception:
            pass

    _ok({"removed": removed, "count": len(removed)})


def main():
    parser = argparse.ArgumentParser(
        description="SCV Batch Manager - persistent state for batchRun orchestration"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_plan = sub.add_parser(
        "plan", help="Prepare repos (git clone/pull) and build batch plan"
    )
    p_plan.add_argument("--session", required=True, help="Session ID")
    p_plan.add_argument("--config", required=True, help="Path to ~/.scv/config.json")
    p_plan.add_argument(
        "--analyze-only",
        action="store_true",
        help="Skip git operations, verify local paths only",
    )

    p_next = sub.add_parser("next", help="Get the next batch of repos to process")
    p_next.add_argument("--session", required=True)

    p_complete = sub.add_parser(
        "complete", help="Mark a repo as successfully completed"
    )
    p_complete.add_argument("--session", required=True)
    p_complete.add_argument("--repo", required=True, help="project_name or repo_name")

    p_fail = sub.add_parser("fail", help="Mark a repo as failed")
    p_fail.add_argument("--session", required=True)
    p_fail.add_argument("--repo", required=True)
    p_fail.add_argument("--error", default=None, help="Error message")

    p_status = sub.add_parser("status", help="Show current progress")
    p_status.add_argument("--session", required=True)

    p_done = sub.add_parser(
        "done", help="Check if all repos are processed (exit 0=done, 1=pending)"
    )
    p_done.add_argument("--session", required=True)

    p_resume = sub.add_parser(
        "resume", help="Show what is still in-progress/pending (read-only)"
    )
    p_resume.add_argument("--session", required=True)

    sub.add_parser("list", help="List all sessions")

    p_cleanup = sub.add_parser("cleanup", help="Remove old session files")
    p_cleanup.add_argument(
        "--older-than", type=int, default=7, help="Remove sessions older than N days"
    )

    args = parser.parse_args()

    commands = {
        "plan": cmd_plan,
        "next": cmd_next,
        "complete": cmd_complete,
        "fail": cmd_fail,
        "status": cmd_status,
        "done": cmd_done,
        "resume": cmd_resume,
        "list": cmd_list,
        "cleanup": cmd_cleanup,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
