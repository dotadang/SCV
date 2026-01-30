---
description: Batch analyze multiple code repositories from configuration
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Perform batch analysis on multiple repositories defined in user's configuration file (`~/.scv/config.json`), generating structured documentation for each repository. Supports both remote repositories (auto-pull before analysis) and local repositories.

## Outline

### Step 1: Check and Load Configuration

1. **Verify configuration file exists**:
   - Check path: `~/.scv/config.json`
   - If missing, report error and provide instructions:
     ```
     Error: Configuration file not found at ~/.scv/config.json

     Please create file with the following structure:

     {
       "output_dir": "~/.scv/analysis",
       "repos": [
         {
           "type": "remote",
           "url": "https://github.com/user/repo1.git",
           "project_name": "Remote Project 1",
           "branch": "main"
         },
         {
           "type": "local",
           "path": "~/local/path/to/repo2",
           "project_name": "Local Project 2"
         }
       ],
       "parallel": false,
       "fail_fast": false
     }

     Repository types:
       - "remote": Git URL, will be cloned to ~/.scv/repos/{extracted_name} and pulled before analysis
       - "local": Local path, analyzed directly without pulling

     Root level fields:
       - output_dir: Unified output directory for all analyses (default: ~/.scv/analysis)

     Fields for remote:
       - url: REQUIRED - Git repository URL
       - project_name: OPTIONAL - Display name (default: extracted from URL)
       - branch: OPTIONAL - Branch to pull (default: repository default)

     Fields for local:
       - path: REQUIRED - Local path (supports ~ for home directory)
       - project_name: OPTIONAL - Display name (default: extracted from path)

     Global settings:
       - parallel: Run analysis in parallel (default: false)
       - fail_fast: Stop on first error (default: false)
     ```

2. **Load and validate configuration**:
   - Parse JSON from `~/.scv/config.json`
   - Validate structure (must have `repos` array)
   - Get `output_dir` from root level (default: `~/.scv/analysis`)
   - For each repo entry:
     - Verify `type` is either `"remote"` or `"local"`

     **For remote repositories**:
     - Verify `url` is valid
     - Extract directory name from URL: `repo_name` = `basename(url)` without `.git`
     - Set local path: `~/.scv/repos/{repo_name}`
     - Set default `project_name`: `{repo_name}` (or use provided value)
     - Set default `branch` to repository default if not provided
     - Analysis output: `{output_dir}/{repo_name}/`

     **For local repositories**:
     - Verify `path` exists and is valid
     - Expand `~` to home directory
     - Extract directory name: `repo_name` = `basename(path)`
     - Set default `project_name`: `{repo_name}` (or use provided value)
     - Analysis output: `{output_dir}/{repo_name}/`

   - Set global settings:
     - `parallel`: default `false`
     - `fail_fast`: default `false`

3. **If validation fails**, report specific errors and exit.

### Step 2: Display Analysis Plan

Before starting analysis, show:

```
📋 Batch Analysis Plan

Configuration: ~/.scv/config.json
Output directory: ~/.scv/analysis
Repositories: {N} (remote: {N}, local: {N})
Parallel execution: {true/false}
Fail on error: {true/false}

Repositories to analyze:
  1. [remote] {project_name}
     URL: {url}
     Branch: {branch}
     Local path: ~/.scv/repos/{repo_name}
     Output: ~/.scv/analysis/{repo_name}

  2. [local] {project_name}
     Path: {path}
     Output: ~/.scv/analysis/{repo_name}

  ...

Total: {N} repositories
All outputs will be saved to: ~/.scv/analysis/
```

### Step 3: Load Templates and Analyzer Prompt

Load from `~/.scv/prompts/` (once, reuse for all repositories):

- **Analyzer Prompt**: `~/.scv/prompts/project-analyzer.md`
- **Templates**:
  - `~/.scv/prompts/templates/README.template.md`
  - `~/.scv/prompts/templates/SUMMARY.template.md`
  - `~/.scv/prompts/templates/ARCHITECTURE.template.md`
  - `~/.scv/prompts/templates/FILE_INDEX.template.md`

### Step 4: Execute Batch Analysis

Based on `parallel` setting:

**If parallel = true:**
- Launch analysis for all repositories concurrently
- Use background tasks if available
- Collect results from all analyses

**If parallel = false (sequential):**
- Process repositories one by one
- Wait for each to complete before starting next
- Track progress continuously

For each repository:

1. **Prepare repository path**:

   **For remote repositories**:
   - Extract directory name: `repo_name` = `basename(url)` without `.git`
   - Local path: `~/.scv/repos/{repo_name}`
   - Analysis output: `{output_dir}/{repo_name}/`
   - Check if repository exists:
     - If exists: Perform `git pull {branch}`
     - If not exists: Clone with `git clone -b {branch} {url} {repo_name}`
   - Show pull/clone result:
     ```
     🔄 Remote repo: {project_name}
     📁 Local: ~/.scv/repos/{repo_name}
     🌿 Branch: {branch}

     ✅ Git pull completed
     Latest: {commit_hash} - {commit_message}
     ```

   **For local repositories**:
   - Extract directory name: `repo_name` = `basename(path)`
   - Analysis output: `{output_dir}/{repo_name}/`
   - Path: `path` (expanded)
   - Verify path exists and is accessible
   - Show:
     ```
     📂 Local repo: {project_name}
     📁 Path: {path}
     ```

2. **Create output directory**:
   - Create directory if doesn't exist: `mkdir -p {output_dir}/{repo_name}/`
   - Verify write permissions

3. **Execute 3-phase analysis** (same as `scv.run`):
   - Phase 1: Global Scan (technology stack, project structure)
   - Phase 2: Deep File Analysis (prioritized file analysis)
   - Phase 3: Documentation Generation (4 documents from templates)

4. **Generate documentation**:
   - README.md
   - SUMMARY.md
   - ARCHITECTURE.md
   - FILE_INDEX.md

5. **Handle errors based on `fail_fast`**:
   - If `fail_fast = true`: Stop entire batch on first error
   - If `fail_fast = false`: Log error, continue with remaining repos

### Step 5: Track and Report Progress

After each repository analysis (in sequential mode) or after each completion (in parallel mode):

**For remote repository success**:
```
✅ [{N}/{total}] {project_name} completed
   Type: remote
   📁 Local: ~/.scv/repos/{repo_name}
   📂 Output: {output_dir}/{repo_name}/
   📄 4 documents generated
   🌿 Branch: {branch}
```

**For local repository success**:
```
✅ [{N}/{total}] {project_name} completed
   Type: local
   📁 Path: {path}
   📂 Output: {output_dir}/{repo_name}/
   📄 4 documents generated
```

**For remote repository pull failure**:
```
❌ [{N}/{total}] {project_name} FAILED - Git pull failed
   Type: remote
   📁 Local: ~/.scv/repos/{repo_name}
   🚫 Error: {error_message}
```

**For analysis failure**:
```
❌ [{N}/{total}] {project_name} FAILED - Analysis failed
   Type: {remote/local}
   📁 Path: {actual_path}
   🚫 Error: {error_message}
```

### Step 6: Generate Batch Summary

After all analyses complete (or stopped on error if `fail_fast = true`), generate summary:

```
╔════════════════════════════════════════════════════════════╗
║         Batch Analysis Complete                              ║
╚════════════════════════════════════════════════════════════╝

Configuration: ~/.scv/config.json
Output directory: ~/.scv/analysis
Execution: {sequential/parallel}
Duration: {X minutes Y seconds}

Results:
  ✅ Successful: {N}/{total}
  ❌ Failed: {N}/{total}
  ⏭️ Skipped: {N}/{total}

  Remote repositories: {N} analyzed
  Local repositories: {N} analyzed

Successful repositories:
  1. [remote] {project_name} → {output_dir}/{repo_name}/
  2. [local] {project_name} → {output_dir}/{repo_name}/
  ...

Failed repositories:
  1. [remote] {project_name} → {error}
  2. [local] {project_name} → {error}
  ...

Output locations:
  All analyses saved to: ~/.scv/analysis/
  Remote repos cloned to: ~/.scv/repos/
```

### Step 7: Offer Next Actions

Suggest next steps:

```
What would you like to do next?

  📖 Browse documentation
     - Open ~/.scv/analysis/ to explore generated docs

  🔍 Analyze a single repository
     - Use /scv.run <repo_path> for targeted analysis

  🌐 Gather remote repositories
     - Use /scv.gather --batch to clone/pull all remote repos

  🔄 Re-run batch analysis
     - Use /scv.batchRun to regenerate all docs (will auto-pull remote repos)

  📋 List all repositories
     - Use /scv.gather --list to see cloned remote repos
```

## Context

$ARGUMENTS

## Configuration File Schema

### ~/.scv/config.json

```json
{
  "output_dir": "~/.scv/analysis",
  "repos": [
    {
      "type": "remote",
      "url": "https://github.com/user/repo.git",
      "project_name": "自定义名称",
      "branch": "main"
    },
    {
      "type": "local",
      "path": "~/local/path/to/repo",
      "project_name": "本地项目"
    }
  ],
  "parallel": false,
  "fail_fast": false
}
```

### Field Descriptions

#### Root Level Fields

| 字段 | 必填 | 说明 | 默认值 |
|------|------|------|--------|
| `output_dir` | 否 | 所有分析的输出目录 | `~/.scv/analysis` |
| `parallel` | 否 | 并行执行 | `false` |
| `fail_fast` | 否 | 遇到错误停止 | `false` |

#### repos 数组（必需）

**Remote Repository (远程仓库)**:
- **type**: `"remote"` (必需，标识为远程仓库)
- **url**: Git 仓库 URL (必需)
- **project_name**: 项目名称 (可选，默认: 从 URL 提取的目录名)
- **branch**: 分支 (可选，默认: 仓库默认分支)

**Local Repository (本地仓库)**:
- **type**: `"local"` (必需，标识为本地仓库)
- **path**: 本地路径 (必需，支持 `~` 相对路径)
- **project_name**: 项目名称 (可选，默认: 从 path 提取的目录名)

### Directory Name Extraction and Output

**Remote repositories**:
- Directory name automatically extracted from URL
- URL: `https://github.com/user/my-project.git` → `repo_name`: `my-project`
- Local path: `~/.scv/repos/my-project/`
- Analysis output: `{output_dir}/my-project/`

**Local repositories**:
- Directory name automatically extracted from path
- Path: `~/projects/my-app` → `repo_name`: `my-app`
- Analysis output: `{output_dir}/my-app/`

**Unified output directory**:
- All repos use the **same** `output_dir` from root level
- Each repo: `{output_dir}/{repo_name}/`
- Example: `~/.scv/analysis/my-project/`

### Example Configuration

```json
{
  "output_dir": "~/.scv/analysis",
  "repos": [
    {
      "type": "remote",
      "url": "https://github.com/company/backend.git",
      "project_name": "Backend Service",
      "branch": "main"
    },
    {
      "type": "remote",
      "url": "https://github.com/company/frontend.git",
      "project_name": "Frontend App",
      "branch": "develop"
    },
    {
      "type": "local",
      "path": "~/projects/documentation",
      "project_name": "Documentation"
    },
    {
      "type": "local",
      "path": "~/work/internal-tool"
    }
  ],
  "parallel": true,
  "fail_fast": false
}
```

## Analysis Behavior

### Remote Repositories

For repositories with `type: "remote"`:

1. **Extract name**: `repo_name` = `basename(url)` without `.git`
2. **Local path**: `~/.scv/repos/{repo_name}`
3. **Output path**: `{output_dir}/{repo_name}/`
4. **Auto-clone**: If not exists, clone from `url`
5. **Auto-pull**: Before analysis, run `git pull {branch}`
6. **Analyze**: Analyze local copy at `~/.scv/repos/{repo_name}`
7. **Benefits**:
   - Always analyze latest code
   - No need to manually pull
   - Repository is cached locally for fast access

### Local Repositories

For repositories with `type: "local"`:

1. **Extract name**: `repo_name` = `basename(path)`
2. **Path**: Use provided `path` directly
3. **Output path**: `{output_dir}/{repo_name}/`
4. **No git operations**: No clone, no pull
5. **Analyze**: Analyze directory as-is
6. **Benefits**:
   - Analyze work-in-progress code
   - No internet required
   - Full control over what's analyzed

### Unified Output Directory

All repository analyses are stored in the **same** `output_dir`:

```
~/.scv/analysis/
  ├── backend/          ← Remote repo 1
  ├── frontend/         ← Remote repo 2
  ├── documentation/    ← Local repo 1
  └── internal-tool/    ← Local repo 2
```

## Error Handling

### Common Errors and Solutions

**Configuration file not found**:
```
❌ Configuration file not found: ~/.scv/config.json
Solution: Create file from config.example.json
  cp config.example.json ~/.scv/config.json
```

**Invalid repository type**:
```
❌ Invalid type "invalid", must be "remote" or "local"
Solution: Check config file and use correct type value
```

**Remote repository URL invalid**:
```
❌ Invalid Git URL for remote repo: {url}
Solution: Ensure URL is a valid Git repository URL
  Examples: https://github.com/user/repo.git, git@github.com:user/repo.git
```

**Git pull failed**:
```
❌ Failed to pull remote repo: {project_name}
Error: {git error message}
Solution:
  - Check internet connection
  - Verify URL is correct
  - Check Git credentials for private repos
  - If repo doesn't exist yet, use /scv.gather --batch to clone first
```

**Local repository path not found**:
```
❌ Local repository not found: {path}
Solution: Verify path exists and is accessible
  - Check if path is correct
  - Use absolute path or ~ for home directory
```

**Analysis failed**:
```
❌ Analysis failed for: {project_name}
Error: {error message}
Solution:
  - Check if repository is valid (not empty)
  - Verify read permissions
  - Review error message for specific issue
```

## Integration with Other Commands

### Typical Workflow

```bash
# 1. Set up configuration with remote and local repos
cat > ~/.scv/config.json <<EOF
{
  "output_dir": "~/.scv/analysis",
  "repos": [
    {"type": "remote", "url": "https://github.com/team/backend.git", "project_name": "Backend"},
    {"type": "local", "path": "~/projects/docs", "project_name": "Docs"}
  ]
}
EOF

# 2. Clone all remote repos (optional, batchRun will auto-clone/pull)
/scv.gather --batch

# 3. Batch analyze all repos (remote + local)
# Note: Remote repos will be auto-pulled before analysis
/scv.batchRun
```

### Command Summary

| Command | Purpose | Repos Processed | Output Directory |
|---------|---------|-----------------|------------------|
| `scv.gather` | Clone/pull remote repos | Only `type: "remote"` | N/A |
| `scv.run` | Analyze single repo | Any path (remote or local) | Specified in command |
| `scv.batchRun` | Batch analyze multiple repos | Both `type: "remote"` and `type: "local"` | Unified `{output_dir}` |

## Analysis Principles

Same as `scv.run`:

1. **Code is truth** - Base analysis on actual code
2. **Naming reveals intent** - Good naming is best documentation
3. **Dependencies expose architecture** - Imports reveal dependencies
4. **Tests document behavior** - Tests are accurate usage examples
5. **Configuration defines boundaries** - Configs reveal integration points
6. **Progressive deep dive** - Global → local, skeleton → flesh

## Best Practices

1. **Use unified output directory** for all analyses
2. **Use meaningful project names** for easier identification
3. **Specify branch** when working with specific versions
4. **Mix remote and local** appropriately:
   - Use `remote` for stable production code
   - Use `local` for work-in-progress or private code
5. **Regular updates**:
   - Run `/scv.gather --update-all` to update all remote repos
   - Or just run `/scv.batchRun` - it will auto-pull before analysis
6. **Check status**:
   - Use `/scv.gather --list` to see all cloned remote repos
   - Use `scv.batchRun` to analyze both remote and local repos

## Resource Management

- **Memory**: Consider repository sizes when using `parallel = true`
- **Disk space**: Ensure sufficient space in output directory and `~/.scv/repos/`
- **CPU**: Parallel execution may use multiple cores
- **Network**: Remote repos require internet for git pull
- **Permissions**: Ensure read access to all local repos

## Example Workflows

### Workflow 1: Analyze Team Repositories

```bash
# 1. Configure team repos (remote + local)
cat > ~/.scv/config.json <<EOF
{
  "output_dir": "~/.scv/analysis",
  "repos": [
    {"type": "remote", "url": "https://github.com/company/backend.git", "project_name": "Backend Service"},
    {"type": "remote", "url": "https://github.com/company/frontend.git", "project_name": "Frontend App"},
    {"type": "local", "path": "~/projects/internal-docs", "project_name": "Internal Docs"}
  ],
  "parallel": true
}
EOF

# 2. First time: Clone remote repos
/scv.gather --batch

# 3. Analyze all repos (remote will auto-pull latest)
/scv.batchRun

# 4. Regular updates: Just re-run batchRun (auto-pulls)
/scv.batchRun
```

### Workflow 2: Mixed Remote and Local Analysis

```bash
# Configure mix of open-source projects and local work
cat > ~/.scv/config.json <<EOF
{
  "output_dir": "~/.scv/analysis",
  "repos": [
    {"type": "remote", "url": "https://github.com/vuejs/vue.git", "project_name": "Vue.js"},
    {"type": "remote", "url": "https://github.com/nodejs/node.git", "project_name": "Node.js"},
    {"type": "local", "path": "~/projects/my-app", "project_name": "My App"},
    {"type": "local", "path": "~/work/experiments/feature-x", "project_name": "Feature X"}
  ],
  "parallel": false
}
EOF

# Analyze everything (remote will pull latest)
/scv.batchRun
```

### Workflow 3: Keep Documentation Updated

```bash
# Configure all repos to monitor
cat > ~/.scv/config.json <<EOF
{
  "output_dir": "~/.scv/analysis",
  "repos": [
    {"type": "remote", "url": "https://github.com/project/repo.git"},
    {"type": "local", "path": "~/active-project"}
  ]
}
EOF

# Set up periodic job (e.g., in cron):
# Weekly analysis:
# 0 0 * * 0 cd ~/SCV && scv.batchRun

# This will:
# 1. Pull latest from remote repos
# 2. Analyze current state of local repos
# 3. Generate up-to-date documentation in ~/.scv/analysis/
```
