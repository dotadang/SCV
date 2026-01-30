---
description: Clone and manage remote Git repositories for analysis
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Clone remote Git repositories to `~/.scv/repos` directory, and manage them based on unified configuration file. Only processes repositories with `type: "remote"` in configuration.

## Outline

### Step 1: Initialize Repository Directory

1. **Create base directory** if not exists:
   ```bash
   mkdir -p ~/.scv/repos
   ```
2. **Verify write permissions** for directory
3. **Display repository storage location**:
   ```
   📁 Repository storage: ~/.scv/repos
   🔧 Configuration: ~/.scv/config.json
   ```

### Step 2: Parse Arguments and Determine Mode

Parse `$ARGUMENTS` to detect operation mode:

**Mode 1: Clone Single Repository**
- Arguments: `<git_url> [branch]`
- Example: `/scv.gather https://github.com/user/repo.git main`
- **Note**: This only clones, does NOT add to config file. To add to config, edit `~/.scv/config.json` manually.

**Mode 2: Batch Clone from Config**
- Arguments: `--batch` or `--config [config_path]`
- Example: `/scv.gather --batch`
- **Behavior**: Clones all repositories with `type: "remote"` from config file

**Mode 3: Update Existing Repositories**
- Arguments: `--update [repo_name]` or `--update-all`
- Example: `/scv.gather --update my-project` or `/scv.gather --update-all`
- **Behavior**: Updates repositories in `~/.scv/repos/`

**Mode 4: List Repositories**
- Arguments: `--list`
- Example: `/scv.gather --list`
- **Behavior**: Lists all cloned repositories in `~/.scv/repos/`

**Mode 5: Remove Repository**
- Arguments: `--remove <repo_name>`
- Example: `/scv.gather --remove my-project`
- **Behavior**: Removes repository from `~/.scv/repos/`

If no arguments provided, show usage:
```
Usage: /scv.gather <git_url> [branch]
       /scv.gather --batch [--config <path>]
       /scv.gather --update [repo_name] | --update-all
       /scv.gather --list
       /scv.gather --remove <repo_name>

Commands:
  Clone single repo:     /scv.gather <git_url> [branch]
  Batch clone:           /scv.gather --batch [--config <path>]
  Update repo:            /scv.gather --update [repo_name]
  Update all repos:       /scv.gather --update-all
  List repos:            /scv.gather --list
  Remove repo:            /scv.gather --remove <repo_name>

Configuration: ~/.scv/config.json

Examples:
  /scv.gather https://github.com/user/project.git
  /scv.gather https://github.com/user/project.git main
  /scv.gather --batch
  /scv.gather --update my-project
  /scv.gather --list
```

### Step 3: Execute Single Repository Clone (Mode 1)

When cloning a single repository:

1. **Validate Git URL**:
   - Check if valid Git URL (https://, git://, git@github.com:user/repo.git)
   - Extract repository name from URL: `basename(url)` without `.git` suffix
   - This extracted name will be used as the local directory name

2. **Check if repository already exists**:
   - Extract directory name: `{repo_name}` = `basename(url)` without `.git`
   - Target path: `~/.scv/repos/{repo_name}`
   - If exists: Ask user
     ```
     Repository '{repo_name}' already exists at ~/.scv/repos/{repo_name}
     Options:
       1. Pull latest changes (git pull)
       2. Remove and re-clone
       3. Skip and use existing
     Choose [1/2/3]:
     ```
   - If user chooses 1: Perform `git pull` in existing directory
   - If user chooses 2: Remove directory and re-clone
   - If user chooses 3: Skip clone, report success with existing path

3. **Clone repository**:
   ```bash
   cd ~/.scv/repos
   git clone {git_url} {repo_name}
   ```
   - If branch specified:
     ```bash
     git clone -b {branch} {git_url} {repo_name}
     ```
   - Capture and display output

4. **Verify clone success**:
   - Check if directory was created
   - Verify it's a valid Git repository
   - Show repository info:
     ```
     ✅ Repository cloned successfully
     📁 Path: ~/.scv/repos/{repo_name}
     🔗 URL: {git_url}
     🌿 Branch: {current_branch}
     📦 Latest commit: {commit_hash} - {commit_message}

     💡 Tip: To add this repo to batch analysis config, edit ~/.scv/config.json
     ```

5. **Error handling**:
   - If clone fails: Report error, clean up partial clone if needed
   - If authentication required: Guide user to configure Git credentials

### Step 4: Execute Batch Clone from Config (Mode 2)

When performing batch clone from configuration:

1. **Determine config file**:
   - Default: `~/.scv/config.json`
   - If `--config <path>` specified: Use provided path
   - If config doesn't exist: Create from example or report error

2. **Load and filter configuration**:
   ```json
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
         "type": "remote",
         "url": "https://github.com/user/repo2.git",
         "project_name": "Remote Project 2",
         "branch": "develop"
       },
       {
         "type": "local",
         "path": "~/local/repo3",
         "project_name": "Local Project 3"
       }
     ],
     "parallel": false,
     "fail_fast": false
   }
   ```
   - Load JSON from config file
   - Get `output_dir` from root level (default: `~/.scv/analysis`)
   - **Filter** only repositories with `type: "remote"`
   - Skip repositories with `type: "local"` (not processed by gather)

3. **Validate configuration**:
   - Check `repos` array exists and has items
   - For each remote repo:
     - Verify `url` is valid
     - Extract directory name from URL: `repo_name` = `basename(url)` without `.git`
     - Set default `branch` to repository default if not provided
     - If `project_name` not set, use `repo_name` as display name
   - Set `parallel` and `fail_fast` with defaults

4. **Display batch plan**:
   ```
   📋 Batch Clone Plan
   Config: ~/.scv/config.json
   Output directory: ~/.scv/analysis
   Remote repositories: {N}
   Local repositories (skipped): {N}
   Parallel: {true/false}
   Fail on error: {true/false}

   Remote repositories to clone:
     1. [Remote Project 1] https://github.com/user/repo1.git (branch: main)
        → ~/.scv/repos/repo1
     2. [Remote Project 2] https://github.com/user/repo2.git (branch: develop)
        → ~/.scv/repos/repo2

   Skipped (local):
     3. [Local Project 3] ~/local/repo3 (type: local, not cloned by gather)
   ```

5. **Execute clones**:
   - If `parallel = true`: Launch clones concurrently
   - If `parallel = false`: Process sequentially
   - For each remote repo:
     - Extract `repo_name` from URL
     - Target: `~/.scv/repos/{repo_name}`
     - Skip if exists and no update flag (or ask user)
     - Update with `git pull` if exists
     - Clone if not exists

6. **Track progress**:
   ```
   ✅ [1/2] Remote Project 1 cloned
   📁 ~/.scv/repos/repo1
   🌿 Branch: main

   ⚠️ [2/2] Remote Project 2 already exists, updated
   📁 ~/.scv/repos/repo2
   🌿 Branch: develop
   ```

7. **Generate summary**:
   ```
   ╔════════════════════════════════════════════════════════════╗
  ║         Batch Clone Complete                                  ║
   ╚════════════════════════════════════════════════════════════╝

   Config: ~/.scv/config.json
   Results:
     ✅ Cloned: {N}/{total}
     ✅ Updated: {N}/{total}
     ⚠️ Skipped: {N}/{total}
     ❌ Failed: {N}/{total}

   Remote repositories processed:
     1. Remote Project 1 → ~/.scv/repos/repo1
     2. Remote Project 2 → ~/.scv/repos/repo2

   Failed repositories:
     1. Remote Project 3 → {error}

   Next steps:
     - Run /scv.batchRun to analyze all repos (remote and local)
   ```

### Step 5: Execute Repository Update (Mode 3 & 4)

When updating repositories:

**Update single repository** (`--update [repo_name]`):

1. If `repo_name` not provided, list available repos and ask to select
2. Check if repository exists at `~/.scv/repos/{repo_name}`
3. Verify it's a Git repository
4. Perform update:
   ```bash
   cd ~/.scv/repos/{repo_name}
   git fetch origin
   git pull origin {current_branch}
   ```
5. Show update result:
   ```
   ✅ Repository updated successfully
   📁 ~/.scv/repos/{repo_name}
   🌿 Branch: {branch}
   📦 Latest commit: {commit_hash} - {commit_message}
   ```

**Update all repositories** (`--update-all`):

1. List all directories in `~/.scv/repos/`
2. For each directory:
   - Check if it's a Git repository
   - Perform `git pull` on current branch
   - Track success/failure
3. Display summary similar to batch clone

### Step 6: List Repositories (Mode 5)

When listing repositories:

1. Scan `~/.scv/repos/` directory
2. For each subdirectory:
   - Check if it's a Git repository
   - Extract: name, remote URL, current branch, last commit date
3. Display table:
   ```
   📁 Local Repositories (stored in ~/.scv/repos/)

   | Name          | Branch   | Last Commit          | URL                          |
   |---------------|----------|----------------------|------------------------------|
   | my-app        | main     | 2025-01-15 10:30    | github.com/user/my-app.git  |
   | api-service   | develop  | 2025-01-14 14:22    | github.com/user/api.git     |
   | cli-tools     | master   | 2025-01-10 09:15    | github.com/user/cli.git     |

   Total: 3 repositories
   ```

### Step 7: Remove Repository (Mode 6)

When removing a repository:

1. Verify `repo_name` is provided
2. Confirm removal:
   ```
   ⚠️  You are about to remove repository: {repo_name}
   📁 Location: ~/.scv/repos/{repo_name}

   This will DELETE the entire directory and all its contents.
   This does NOT remove the entry from ~/.scv/config.json.

   Are you sure? Type 'yes' to confirm:
   ```
3. If confirmed:
   ```bash
   rm -rf ~/.scv/repos/{repo_name}
   ```
4. Report success:
   ```
   ✅ Repository removed
   📁 ~/.scv/repos/{repo_name}
   💡 Tip: To remove from config, edit ~/.scv/config.json
   ```

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
| `output_dir` | 否 | 所有分析文档的输出目录 | `~/.scv/analysis` |
| `parallel` | 否 | 批量操作是否并行 | `false` |
| `fail_fast` | 否 | 遇到错误是否停止 | `false` |

#### repos 数组（必需）

每个代码库的配置：

**Remote Repository (远程仓库)**:
- **type**: `"remote"` (必需，标识为远程仓库)
- **url**: Git 仓库 URL (必需)
- **project_name**: 项目名称 (可选，默认: 从 URL 提取的目录名)
- **branch**: 分支 (可选，默认: 仓库默认分支)

**Local Repository (本地仓库)**:
- **type**: `"local"` (必需，标识为本地仓库)
- **path**: 本地路径 (必需，支持 `~` 相对路径)
- **project_name**: 项目名称 (可选，默认: 从 path 提取的目录名)

### Directory Name Extraction

**Remote repositories**:
- Directory name automatically extracted from URL
- URL: `https://github.com/user/my-project.git` → Directory: `my-project`
- URL: `git@github.com:user/awesome-app.git` → Directory: `awesome-app`

**Local repositories**:
- Directory name automatically extracted from path
- Path: `~/projects/my-app` → Directory: `my-app`
- Path: `~/work/feature-xyz` → Directory: `feature-xyz`

**Analysis output**:
- All repos use the same `output_dir` from root level
- Each repo's analysis: `{output_dir}/{extracted_name}/`
- Example: `~/.scv/analysis/my-project/`

## Error Handling

### Common Errors and Solutions

**Authentication required:**
```
❌ Authentication failed for {url}
Solution: Configure Git credentials
  git config --global credential.helper store
  git config --global user.name "Your Name"
  git config --global user.email "you@example.com"
```

**Invalid Git URL:**
```
❌ Invalid Git URL: {url}
Solution: Ensure URL is a valid Git repository URL
  Examples:
    https://github.com/user/repo.git
    git@github.com:user/repo.git
    git://github.com/user/repo.git
```

**Repository exists:**
```
⚠️  Repository already exists
Solution: Use --update to pull latest changes
         Or remove and re-clone manually
```

**Insufficient permissions:**
```
❌ Permission denied: ~/.scv/repos
Solution: Check directory permissions
  chmod 755 ~/.scv/repos
```

**Network error:**
```
❌ Failed to connect to {url}
Solution: Check internet connection and repository accessibility
```

## Context

$ARGUMENTS

## Integration with Other Commands

After gathering repositories, you can:

1. **Analyze single repo**:
   ```bash
   /scv.run ~/.scv/repos/my-project
   ```

2. **Batch analyze all repos (remote + local)**:
   ```bash
   /scv.batchRun
   ```
   - This will:
     - For remote repos: Run `git pull` first, then analyze
     - For local repos: Analyze directly

## Best Practices

1. **Use meaningful project names** for easier identification
2. **Specify branch** when working with specific versions
3. **Regularly update** repositories with `--update-all`
4. **Clean up** unused repositories with `--remove`
5. **Organize** by project or team in config
6. **Use shallow clone** for large repositories (add `depth: 1` to config if needed)

## Example Workflows

### Workflow 1: Clone and Analyze

```bash
# Clone a repository
/scv.gather https://github.com/user/awesome-project.git

# Analyze it immediately
/scv.run ~/.scv/repos/awesome-project
```

### Workflow 2: Complete Setup with Config

```bash
# 1. Create unified config with remote and local repos
cat > ~/.scv/config.json <<EOF
{
  "output_dir": "~/.scv/analysis",
  "repos": [
    {
      "type": "remote",
      "url": "https://github.com/team/backend.git",
      "project_name": "Backend Service",
      "branch": "main"
    },
    {
      "type": "remote",
      "url": "https://github.com/team/frontend.git",
      "project_name": "Frontend App",
      "branch": "develop"
    },
    {
      "type": "local",
      "path": "~/projects/docs",
      "project_name": "Documentation"
    }
  ],
  "parallel": true
}
EOF

# 2. Clone all remote repos
/scv.gather --batch

# 3. Verify
/scv.gather --list

# 4. Batch analyze all repos (remote + local)
# Note: batchRun will auto-pull remote repos before analyzing
/scv.batchRun
```

### Workflow 3: Keep Repositories Updated

```bash
# List all repositories
/scv.gather --list

# Update a specific repository
/scv.gather --update backend

# Update all repositories
/scv.gather --update-all

# Re-analyze after update
/scv.batchRun
```

## Notes

- `scv.gather` **only** processes repositories with `type: "remote"` in config
- `scv.batchRun` processes **both** remote and local repositories
- Directory names are **automatically extracted** from URL or path
- `project_name` is used for display in documents and reports
- All analysis outputs are stored in the **same** `output_dir` from config root
