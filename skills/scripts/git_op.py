#!/usr/bin/env python3
"""
SCV Git Operations Module - Centralized Git operations for repository management.

Provides reusable functions for:
- Cloning remote repositories
- Pulling updates from remote repositories
- Verifying local repository paths
- Repository name extraction from URLs and paths

Used by both batch_manager.py and gather subcommand.
"""

import subprocess
from pathlib import Path
from typing import Optional, Tuple


class GitOperationError(Exception):
    """Exception raised for Git operation failures."""

    pass


def extract_repo_name(repo_dict: dict) -> str:
    """
    Extract a normalized repository name from various sources.

    Priority:
    1. project_name (if provided)
    2. Extract from URL (remove .git suffix)
    3. Extract from path (directory name)
    4. Default to "unknown"

    Args:
        repo_dict: Dictionary with keys: project_name, url, or path

    Returns:
        Normalized repository name (lowercase, underscores for spaces)
    """
    if repo_dict.get("project_name"):
        return repo_dict["project_name"].replace(" ", "_").lower()

    if repo_dict.get("url"):
        base = repo_dict["url"].rstrip("/").split("/")[-1]
        return base.removesuffix(".git")

    if repo_dict.get("path"):
        return Path(repo_dict["path"]).name

    return "unknown"


def git_clone(
    url: str,
    target_dir: Path,
    branch: str = "main",
) -> Tuple[bool, str]:
    """
    Clone a Git repository to the target directory.

    Args:
        url: Git repository URL
        target_dir: Local directory to clone into
        branch: Branch to clone (default: "main")

    Returns:
        Tuple of (success: bool, message: str)
        - success=True: Returns success message
        - success=False: Returns error message
    """
    target_dir.parent.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        ["git", "clone", "-b", branch, url, str(target_dir)],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        error_msg = result.stderr.strip() or result.stdout.strip()
        return False, f"git clone failed: {error_msg}"

    return True, f"cloned (branch: {branch})"


def git_pull(
    repo_dir: Path,
    branch: str = "main",
) -> Tuple[bool, str]:
    """
    Pull updates from remote repository.

    Args:
        repo_dir: Local repository directory
        branch: Branch to pull (default: "main")

    Returns:
        Tuple of (success: bool, message: str)
        - success=True: Returns success message
        - success=False: Returns error message
    """
    if not repo_dir.exists():
        return False, f"Repository directory not found: {repo_dir}"

    result = subprocess.run(
        ["git", "-C", str(repo_dir), "pull", "origin", branch],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        error_msg = result.stderr.strip() or result.stdout.strip()
        return False, f"git pull failed: {error_msg}"

    return True, f"pulled (branch: {branch})"


def verify_local_path(path: str) -> Tuple[bool, Path, str]:
    """
    Verify that a local path exists.

    Args:
        path: Local file system path (supports ~ expansion)

    Returns:
        Tuple of (success: bool, resolved_path: Path, message: str)
    """
    local_path = Path(path).expanduser()

    if not local_path.exists():
        return False, local_path, f"Local path not found: {local_path}"

    return True, local_path, "local path verified"


def prepare_repo(
    repo: dict,
    repos_base_dir: Path,
    analyze_only: bool = False,
) -> Tuple[bool, str, str]:
    """
    Ensure a repository is available locally.

    For remote repos: git clone or pull (unless analyze_only=True)
    For local repos: verify path exists

    Args:
        repo: Repository dictionary with keys:
            - type: "remote" or "local"
            - url: Git URL (for remote)
            - path: Local path (for local)
            - branch: Branch name (optional, default: "main")
            - repo_name: Repository name (required)
        repos_base_dir: Base directory for storing cloned repositories
        analyze_only: If True, skip git operations and only verify existence

    Returns:
        Tuple of (success: bool, local_path: str, message: str)

    Example:
        success, path, msg = prepare_repo(
            {"type": "remote", "url": "...", "repo_name": "myrepo"},
            Path("~/.scv/repos"),
            analyze_only=False
        )
    """
    repo_type = repo.get("type", "local")

    if repo_type == "remote":
        url = repo.get("url", "")
        branch = repo.get("branch", "main")
        repo_name = repo["repo_name"]
        local_path = repos_base_dir / repo_name

        if analyze_only:
            if not local_path.exists():
                return (
                    False,
                    "",
                    f"Local repo not found: {local_path}. Run without --analyze-only to clone.",
                )
            return True, str(local_path), "exists (analyze-only)"

        repos_base_dir.mkdir(parents=True, exist_ok=True)

        if local_path.exists():
            success, message = git_pull(local_path, branch)
            return success, str(local_path) if success else "", message
        else:
            success, message = git_clone(url, local_path, branch)
            return success, str(local_path) if success else "", message

    else:  # local
        raw_path = repo.get("path", "")
        success, resolved_path, message = verify_local_path(raw_path)
        return success, str(resolved_path) if success else "", message


def get_current_branch(repo_dir: Path) -> Optional[str]:
    """
    Get the current branch name of a Git repository.

    Args:
        repo_dir: Local repository directory

    Returns:
        Branch name or None if failed
    """
    if not repo_dir.exists():
        return None

    result = subprocess.run(
        ["git", "-C", str(repo_dir), "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return None

    return result.stdout.strip()


def is_git_repo(path: Path) -> bool:
    """
    Check if a directory is a Git repository.

    Args:
        path: Directory to check

    Returns:
        True if the directory is a Git repository
    """
    if not path.exists():
        return False

    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "--git-dir"],
        capture_output=True,
        text=True,
    )

    return result.returncode == 0


def get_remote_url(repo_dir: Path, remote: str = "origin") -> Optional[str]:
    """
    Get the remote URL of a Git repository.

    Args:
        repo_dir: Local repository directory
        remote: Remote name (default: "origin")

    Returns:
        Remote URL or None if failed
    """
    if not repo_dir.exists():
        return None

    result = subprocess.run(
        ["git", "-C", str(repo_dir), "remote", "get-url", remote],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return None

    return result.stdout.strip()


def get_head_commit(repo_dir: Path) -> Optional[str]:
    """
    Get the HEAD commit hash of a Git repository.

    Args:
        repo_dir: Local repository directory

    Returns:
        Full commit hash (40 chars) or None if failed
    """
    if not repo_dir.exists():
        return None

    result = subprocess.run(
        ["git", "-C", str(repo_dir), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return None

    return result.stdout.strip()


def get_commit_info(repo_dir: Path) -> Optional[dict]:
    """
    Get detailed commit information for the HEAD commit.

    Args:
        repo_dir: Local repository directory

    Returns:
        Dictionary with commit info or None if failed:
        {
            "hash": "abc123...",
            "short_hash": "abc123",
            "message": "commit message",
            "author": "Author Name",
            "date": "2026-03-17 14:30:00"
        }
    """
    if not repo_dir.exists():
        return None

    commit_hash = get_head_commit(repo_dir)
    if not commit_hash:
        return None

    result = subprocess.run(
        [
            "git",
            "-C",
            str(repo_dir),
            "log",
            "-1",
            "--format=%H%n%h%n%s%n%an%n%ci",
            "HEAD",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return None

    lines = result.stdout.strip().split("\n")
    if len(lines) < 5:
        return None

    return {
        "hash": lines[0],
        "short_hash": lines[1],
        "message": lines[2],
        "author": lines[3],
        "date": lines[4],
    }
