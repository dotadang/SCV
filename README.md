# SCV - Source Code Vault

> A powerful codebase management and analysis tool for Claude Code

[![GitHub Repository](https://img.shields.io/badge/GitHub-SCV-blue.svg)](https://github.com/ProjAnvil/SCV)

**SCV** provides three Claude Code commands for comprehensive codebase management and analysis:

- **scv.gather** - Clone and manage remote Git repositories (handles only `remote` type repos from config)
- **scv.run** - Perform deep analysis on a single codebase
- **scv.batchRun** - Batch analyze multiple codebases (auto-pulls latest code for `remote` type repos)

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Commands](#commands)
  - [scv.gather](#scvgather---git-repository-management)
  - [scv.run](#scvrun----single-codebase-analysis)
  - [scv.batchRun](#scvbatchrun---batch-codebase-analysis)
- [Configuration](#configuration)
- [Template System](#template-system)
- [Output Documents](#output-documents)
- [Workflows](#workflows)
- [Best Practices](#best-practices)
- [Git Configuration](#git-configuration)
- [Troubleshooting](#troubleshooting)

## Features

- 🔄 **Remote Repository Management**: Clone, update, and manage remote Git repositories
- 📊 **Deep Code Analysis**: Generate comprehensive documentation for any codebase
- 🚀 **Batch Processing**: Analyze multiple repositories at once
- 📝 **Multiple Output Formats**: README, Summary, Architecture, File Index
- 🤖 **Auto-Pull for Remote Repos**: Always analyze the latest code
- 🎯 **Flexible Configuration**: Support both remote and local repositories
- 📦 **Unified Config**: Single configuration file for all operations

## Installation

Ensure the command files are located in the correct directory:

```
/Users/yuhaochen/Documents/codebase/SCV/commands/
  ├── scv.gather.md
  ├── scv.run.md
  └── scv.batchRun.md
```

Create the SCV configuration directory:

```bash
mkdir -p ~/.scv
```

Copy the example configuration file:

```bash
cp config.example.json ~/.scv/config.json
```

Copy commands to Claude's directory:
```bash
cp -r commands/ ~/.claude/
```
Or create a symbolic link:
```bash
ln -s $(pwd)/commands ~/.claude/commands
```

## Quick Start

### 1. Clone a Repository

```bash
/scv.gather https://github.com/user/project.git
```

### 2. Analyze the Codebase

```bash
/scv.run ~/.scv/repos/project
```

### 3. View Generated Documentation

```bash
open ~/.scv/analysis/project/README.md
```

## Commands

### scv.gather - Git Repository Management

#### Overview

Clone remote Git repositories to `~/.scv/repos`, supporting single and batch operations, plus repository update and list management.

#### Usage

```bash
# Clone a single repository
/scv.gather <git_url> [repo_name] [branch]

# Batch clone
/scv.gather --batch [--config <path>]

# Update repository
/scv.gather --update [repo_name] | --update-all

# List all repositories
/scv.gather --list

# Remove repository
/scv.gather --remove <repo_name>
```

#### Single Repository Clone

**Parameters:**

| Parameter | Required | Description | Default |
|-----------|----------|-------------|---------|
| `git_url` | Yes | Git repository URL (HTTPS/GIT/SSH) | - |
| `repo_name` | No | Local directory name | Extracted from URL |
| `branch` | No | Specify branch | Repository default |

**Examples:**

```bash
# Basic clone
/scv.gather https://github.com/user/project.git

# Specify repository name
/scv.gather https://github.com/user/project.git my-project

# Specify branch
/scv.gather https://github.com/user/project.git my-project develop

# Use SSH URL
/scv.gather git@github.com:user/project.git
```

**Repository Location:**

All cloned repositories are stored in:
```
~/.scv/repos/
  ├── my-project/
  ├── another-repo/
  └── ...
```

#### Batch Clone

**Note:** `scv.gather --batch` only processes repositories with `type: "remote"` in the configuration file.

**Configuration File:**

Default location: `~/.scv/config.json` (shared with `scv.batchRun`)

**Configuration Example:**

```json
{
  "output_dir": "~/.scv/analysis",
  "repos": [
    {
      "type": "remote",
      "url": "https://github.com/user/project1.git",
      "project_name": "Remote Project 1",
      "branch": "main"
    },
    {
      "type": "remote",
      "url": "https://github.com/user/project2.git",
      "project_name": "Remote Project 2",
      "branch": "develop"
    },
    {
      "type": "local",
      "path": "~/local/path/to/project3",
      "project_name": "Local Project 3"
    },
    {
      "type": "local",
      "path": "~/projects/another-repo"
    }
  ],
  "parallel": false
}
```

**Notes:**
- `type: "remote"` - Remote repository managed by `scv.gather`
- `type: "local"` - Local repository (not handled by `scv.gather`, but analyzed by `scv.batchRun`)
- `output_dir` - Unified output directory for all analyses

#### Directory Name Auto-Extraction

**Remote Repositories:**
- Auto-extracted from URL: `https://github.com/user/my-project.git` → `my-project`
- Cloned to: `~/.scv/repos/my-project/`
- Analysis output to: `~/.scv/analysis/my-project/`

**Local Repositories:**
- Auto-extracted from path: `~/projects/my-app` → `my-app`
- Analysis output to: `~/.scv/analysis/my-app/`

#### Update Repositories

**Update Single Repository:**

```bash
# Update specific repository
/scv.gather --update my-project

# List repositories for selection
/scv.gather --update
```

**Update All Repositories:**

```bash
# Update all local repositories
/scv.gather --update-all
```

#### List Repositories

```bash
# List all local repositories
/scv.gather --list
```

Output example:
```
📁 Local Repositories (stored in ~/.scv/repos/)

| Name          | Branch   | Last Commit          | URL                          |
|---------------|----------|----------------------|------------------------------|
| my-app        | main     | 2025-01-15 10:30    | github.com/user/my-app.git  |
| api-service   | develop  | 2025-01-14 14:22    | github.com/user/api.git     |
| cli-tools     | master   | 2025-01-10 09:15    | github.com/user/cli.git     |

Total: 3 repositories
```

#### Remove Repository

```bash
# Remove specific repository (requires confirmation)
/scv.gather --remove my-project
```

### scv.run - Single Codebase Analysis

#### Overview

Perform deep analysis on a single codebase, generating the following documents:

- **README.md** - Project overview entry point
- **SUMMARY.md** - Project summary (understand the full project in 5 minutes)
- **ARCHITECTURE.md** - Architecture design document
- **FILE_INDEX.md** - File index

#### Usage

```bash
/scv.run <repo_path> [output_dir] [project_name]
```

#### Parameters

| Parameter | Required | Description | Default |
|-----------|----------|-------------|---------|
| `repo_path` | Yes | Codebase path (absolute or relative) | - |
| `output_dir` | No | Output directory | `<SCV_ROOT>/analysis/{repo_name}` |
| `project_name` | No | Custom project name | Codebase folder name |

#### Examples

```bash
# Basic usage
/scv.run ~/projects/my-app

# Specify output directory
/scv.run ~/projects/my-app ~/docs/my-app

# Full parameters
/scv.run ~/projects/my-app ~/docs/my-app "My Application"
```

#### Analysis Process

1. **Global Scan** - Identify technology stack, understand project structure
2. **Deep Analysis** - Parse files one by one, extract core logic
3. **Document Generation** - Generate 4 core documents based on templates

### scv.batchRun - Batch Codebase Analysis

#### Overview

Read multiple codebase configurations from a config file and batch generate analysis documents. Supports remote repositories (auto git pull) and local repositories.

**Key Features:**
- **Remote Repositories**: Automatically executes `git pull` before analysis to ensure latest code
- **Local Repositories**: Analyzes local paths directly without git operations
- **Unified Config**: Shares the same config file `~/.scv/config.json` with `scv.gather`

#### Configuration File

Location: `~/.scv/config.json` (shared with `scv.gather`)

#### Configuration Example

```json
{
  "output_dir": "~/.scv/analysis",
  "repos": [
    {
      "type": "remote",
      "url": "https://github.com/user/project1.git",
      "project_name": "Remote Project 1",
      "branch": "main"
    },
    {
      "type": "remote",
      "url": "https://github.com/user/project2.git",
      "project_name": "Remote Project 2",
      "branch": "develop"
    },
    {
      "type": "local",
      "path": "~/local/path/to/project3",
      "project_name": "Local Project 3"
    },
    {
      "type": "local",
      "path": "~/projects/another-repo"
    }
  ],
  "parallel": false,
  "fail_fast": false
}
```

#### Configuration Fields

##### Root Level Fields

| Field | Required | Description | Default |
|-------|----------|-------------|---------|
| `output_dir` | No | Output directory for all analyses | `~/.scv/analysis` |
| `parallel` | No | Parallel execution | `false` |
| `fail_fast` | No | Stop on error | `false` |

##### Repos Array (Required)

**Remote Repository:**
- **type**: `"remote"` (required)
- **url**: Git repository URL (required)
- **project_name**: Project name (optional, default: directory name extracted from URL)
- **branch**: Branch (optional, default: repository default branch)

**Local Repository:**
- **type**: `"local"` (required)
- **path**: Local path (required, supports `~` relative path)
- **project_name**: Project name (optional, default: directory name extracted from path)

#### Analysis Behavior

##### Remote Repositories (`type: "remote"`)

For remote repositories, the analysis process:

1. **Local path**: `~/.scv/repos/{name}`
2. **Auto clone**: Clone from URL if not exists
3. **Auto pull**: Execute `git pull {branch}` before analysis
4. **Analyze**: Analyze local copy
5. **Advantages**:
   - Always analyze latest code
   - No manual pull required
   - Local cache, fast access

##### Local Repositories (`type: "local"`)

For local repositories, the analysis process:

1. **Path**: Analyze directly using provided `path`
2. **No git operations**: No clone, no pull
3. **Analyze**: Analyze directory as-is
4. **Advantages**:
   - Analyze work-in-progress code
   - No network connection required
   - Full control over analysis content

#### Creating Configuration File

**Unified Configuration File** (used for both `scv.gather` and `scv.batchRun`):

1. Create config file before first use:
   ```bash
   mkdir -p ~/.scv
   cp config.example.json ~/.scv/config.json
   ```

2. Edit config file, add your codebases:
   ```bash
   vim ~/.scv/config.json
   ```

Configuration file supports two types of codebases:
- **remote**: Remote Git repositories (cloned/managed by `scv.gather`, auto-pulled by `scv.batchRun`)
- **local**: Local paths (not handled by `scv.gather`, directly analyzed by `scv.batchRun`)

#### Usage

```bash
# Analyze all codebases in config file
/scv.batchRun
```

#### Execution Modes

**Sequential Execution** (`parallel: false`, default):
- Analyze codebases one by one
- Low resource usage
- Suitable for large-scale batch analysis

**Parallel Execution** (`parallel: true`):
- Analyze multiple codebases simultaneously
- Faster
- Higher resource usage

#### Error Handling

**Continue on Error** (`fail_fast: false`, default):
- Log errors, continue analyzing other codebases
- Show summary report at the end

**Stop on Error** (`fail_fast: true`):
- Stop entire batch task on first error
- Suitable for strict validation scenarios

## Configuration

### Setup

1. Create configuration directory:
   ```bash
   mkdir -p ~/.scv
   ```

2. Create config file:
   ```bash
   cp config.example.json ~/.scv/config.json
   ```

3. Edit configuration:
   ```bash
   vim ~/.scv/config.json
   ```

### Configuration Structure

```json
{
  "output_dir": "~/.scv/analysis",
  "repos": [
    {
      "type": "remote",
      "url": "https://github.com/user/project1.git",
      "project_name": "Remote Project 1",
      "branch": "main"
    },
    {
      "type": "local",
      "path": "~/projects/local-project",
      "project_name": "Local Project"
    }
  ],
  "parallel": false,
  "fail_fast": false
}
```

## Template System

Analysis is based on predefined templates:

- `prompts/project-analyzer.md` - Analysis expert prompts
- `prompts/templates/README.template.md` - README template
- `prompts/templates/SUMMARY.template.md` - Summary template
- `prompts/templates/ARCHITECTURE.template.md` - Architecture template
- `prompts/templates/FILE_INDEX.template.md` - File index template

### Template Tags

- `{placeholder}` - Placeholder replacement
- `<!-- IF condition -->...<!-- END IF -->` - Conditional rendering
- `<!-- FOR item -->...<!-- END FOR -->` - Loop rendering

## Output Documents

### README.md

Project overview including:
- Project positioning and value
- Technology stack
- Document navigation
- Project statistics
- Core module overview
- Quick start guide

### SUMMARY.md

5-minute project quick understanding including:
- Project type and core functionality
- Technology stack panorama
- Directory structure
- Module division
- Data models
- API overview
- Configuration notes
- Important notes

### ARCHITECTURE.md

Architecture design document including:
- System architecture diagram (Mermaid)
- Technology selection rationale
- Module design
- Data flow
- Interface design
- Scalability considerations

### FILE_INDEX.md

File index including:
- Responsibility descriptions for all files
- File dependencies
- Key class/function descriptions
- Quick location guide

## Workflows

### Workflow 1: Clone and Analyze Immediately

**Goal**: Analyze a GitHub open source project

```bash
# 1. Clone remote repository
/scv.gather https://github.com/user/awesome-project.git

# 2. Analyze immediately
/scv.run ~/.scv/repos/awesome-project

# 3. View generated documentation
open ~/.scv/analysis/awesome-project/README.md
```

### Workflow 2: Team Project Documentation (Remote + Local)

**Goal**: Generate documentation for multiple team projects, including remote repos and local projects

```bash
# 1. Create unified configuration (includes remote and local)
cat > ~/.scv/config.json <<EOF
{
  "output_dir": "~/.scv/analysis",
  "repos": [
    {
      "type": "remote",
      "url": "https://github.com/team/backend-api.git",
      "project_name": "Backend API",
      "branch": "main"
    },
    {
      "type": "remote",
      "url": "https://github.com/team/web-frontend.git",
      "project_name": "Web Frontend",
      "branch": "develop"
    },
    {
      "type": "local",
      "path": "~/projects/internal-docs",
      "project_name": "Internal Docs"
    }
  ],
  "parallel": true
}
EOF

# 2. Clone all remote repositories (optional, batchRun will auto clone/pull)
/scv.gather --batch

# 3. Verify repositories
/scv.gather --list

# 4. Batch analyze (remote repos will auto-pull latest code)
/scv.batchRun
```

### Workflow 3: Periodic Project Documentation Updates

**Goal**: Keep project documentation in sync with code (recommended approach)

```bash
# 1. Configure remote and local repositories (see Workflow 2)
cat > ~/.scv/config.json <<EOF
{
  "output_dir": "~/.scv/analysis",
  "repos": [
    {
      "type": "remote",
      "url": "https://github.com/team/backend.git",
      "project_name": "Backend"
    },
    {
      "type": "remote",
      "url": "https://github.com/team/frontend.git",
      "project_name": "Frontend"
    },
    {
      "type": "local",
      "path": "~/projects/work-in-progress",
      "project_name": "Work in Progress"
    }
  ]
}
EOF

# 2. Periodic batch analysis (recommended)
# Run batchRun directly, it will auto:
# - Pull latest code for all remote repos
# - Analyze current state of local repos
# - Output all analyses to ~/.scv/analysis/
/scv.batchRun
```

### Workflow 4: Competitive Analysis

**Goal**: Analyze multiple similar projects for technical comparison

```bash
# 1. Clone competitor projects
/scv.gather https://github.com/competitor1/project.git competitor1
/scv.gather https://github.com/competitor2/project.git competitor2
/scv.gather https://github.com/competitor3/project.git competitor3

# 2. Batch analyze
cat > ~/.scv/competitor-analysis.json <<EOF
{
  "repos": [
    {"path": "~/.scv/repos/competitor1", "project_name": "Competitor 1"},
    {"path": "~/.scv/repos/competitor2", "project_name": "Competitor 2"},
    {"path": "~/.scv/repos/competitor3", "project_name": "Competitor 3"}
  ]
}
EOF

/scv.batchRun

# 3. Generate comparison report
# Manually compare SUMMARY.md and ARCHITECTURE.md of each project
```

### Workflow 5: Pre-Contribution Analysis

**Goal**: Understand project structure before submitting PR

```bash
# 1. Clone project
/scv.gather https://github.com/open-source/project.git

# 2. Analyze project
/scv.run ~/.scv/repos/project ~/contribution-analysis/project

# 3. Read ARCHITECTURE.md and FILE_INDEX.md
# Understand module division and code organization

# 4. Start contributing
cd ~/.scv/repos/project
git checkout -b my-feature
# ... develop and commit
```

## Best Practices

### Single Codebase Analysis

1. **Regular Analysis** - Re-analyze after major codebase changes
2. **Team Sharing** - Add generated documents to the project repository
3. **Continuous Updates** - Use generated documents as a base, manually supplement details

### Batch Codebase Analysis

1. **Initial Setup** - Use sequential execution mode first to ensure each codebase is configured correctly
2. **Large-Scale Analysis** - Enable parallel execution mode for speed
3. **Periodic Refresh** - Simply run `scv.batchRun`, it auto-pulls latest code from remote repos
4. **Mixed Usage** - Choose remote or local based on purpose:
   - Remote: Stable production code, need latest version
   - Local: Work-in-progress, or private code

### Configuration Management

1. **Version Control** - Add `~/.scv/config.json` to version control (exclude sensitive paths)
2. **Unified Configuration** - `scv.gather` and `scv.batchRun` share the same config file
3. **Grouped Management** - Group configurations by project, team, or purpose
4. **Type Selection** - Reasonably use remote and local types

## Git Configuration

### HTTPS Clone Configuration

If using HTTPS URLs, you may need to configure Git credentials:

```bash
# Configure user info
git config --global user.name "Your Name"
git config --global user.email "you@example.com"

# Configure credential helper (saves credentials after first clone)
git config --global credential.helper store
```

### SSH Clone Configuration

If using SSH URLs (recommended), need to configure SSH keys:

```bash
# 1. Generate SSH key
ssh-keygen -t ed25519 -C "you@example.com"

# 2. Start SSH agent
eval "$(ssh-agent -s)"

# 3. Add key to agent
ssh-add ~/.ssh/id_ed25519

# 4. Copy public key to GitHub/GitLab
cat ~/.ssh/id_ed25519.pub
# Copy output and add to GitHub Settings -> SSH and GPG keys

# 5. Test connection
ssh -T git@github.com
```

### Network Acceleration (China Users)

If clone speed is slow, you can use Git mirrors:

```bash
# Use Gitee mirror (for GitHub repos)
# GitHub: https://github.com/user/repo.git
# Gitee:  https://gitee.com/user/repo.git

# Configure Git to use proxy (if available)
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890

# Remove proxy
git config --global --unset http.proxy
git config --global --unset https.proxy
```

### Git Configuration Verification

```bash
# View current Git configuration
git config --global --list

# Verify SSH configuration
ssh -T git@github.com

# Test clone (no history download)
git clone --depth 1 https://github.com/user/test-repo.git
```

## Troubleshooting

### Common Issues

**Q: Prompt "Configuration file not found"**

A: Create `~/.scv/config.json`, refer to `config.example.json`

**Q: Git clone failed, authentication failed**

A:
1. Check Git credential configuration (see Git Configuration section above)
2. If using HTTPS, ensure `credential.helper` is configured
3. If using SSH, ensure SSH key is added to GitHub/GitLab
4. Test connection: `git ls-remote <git_url>`

**Q: Clone speed too slow**

A:
1. Use shallow clone: `git clone --depth 1 <url>`
2. Configure proxy (if available)
3. Use mirror sites (like Gitee)

**Q: Analysis output incomplete**

A: Check codebase permissions, ensure all files can be read

**Q: Template files missing**

A: Ensure all template files exist in `prompts/templates/` directory

**Q: Parallel execution insufficient resources**

A: Change `parallel: false` to sequential execution

**Q: Repository already exists, how to update**

A:
- Update single repo: `/scv.gather --update <repo_name>`
- Update all repos: `/scv.gather --update-all`
- Re-clone: Delete first then clone again

**Q: Partial failures during batch clone**

A:
1. Check if failed repository URL is valid
2. Check network connection
3. Check Git credential configuration
4. View error logs for specific reasons

### Debugging Tips

1. **Single Test** - Test single codebase with `scv.run` first
2. **View Logs** - Commands show detailed execution process
3. **Check Output** - Verify generated documents are complete
4. **Adjust Configuration** - Adjust configuration parameters based on actual situation

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.

## Links

- **Repository**: [https://github.com/ProjAnvil/SCV](https://github.com/ProjAnvil/SCV)
- **中文文档**: [docs/README_CN.md](docs/README_CN.md)
