---
description: Analyze a single code repository and generate structured documentation
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Perform deep code analysis on a single repository (remote URL or local path) and generate comprehensive documentation in Chinese following the SCV project's template system. All analysis results are stored in the unified `~/.scv/analysis` directory.

## Outline

### Step 1: Initialize SCV Directories

1. **Create base directories** if not exist:
   ```bash
   mkdir -p ~/.scv/repos
   mkdir -p ~/.scv/analysis
   ```
2. **Verify write permissions** for both directories
3. **Display storage locations**:
   ```
   📁 Repository storage: ~/.scv/repos
   📂 Analysis output: ~/.scv/analysis
   ```

### Step 2: Parse Arguments and Detect Input Type

Parse `$ARGUMENTS` to extract:

- **repo_input** (REQUIRED): Remote Git URL or local path to analyze
- **project_name** (OPTIONAL): Custom project name (default: auto-extracted)

If no arguments provided, prompt user:
```
Usage: /scv.run <repo_input> [project_name]

Examples:
  # Remote repository
  /scv.run https://github.com/user/project.git
  /scv.run https://github.com/user/project.git "My Project"

  # Local Git repository
  /scv.run ~/projects/my-project
  /scv.run ~/projects/my-project "My Project"

  # Local non-Git directory
  /scv.run ~/my-folder "My Analysis"
```

### Step 3: Determine Repository Type and Prepare Path

Detect the type of input and prepare the repository path:

**Case 1: Remote Git URL**
- Pattern: `https://`, `git://`, `git@github.com:user/repo.git`
- Extract `repo_name`: `basename(url)` without `.git` suffix
- Local path: `~/.scv/repos/{repo_name}`
- Analysis output: `~/.scv/analysis/{repo_name}/`

**Case 2: Local Git Repository**
- Check if path contains `.git` directory
- Extract `repo_name`: `basename(path)`
- **Clone local repository** to: `~/.scv/repos/{repo_name}`
- Analysis output: `~/.scv/analysis/{repo_name}/`

**Case 3: Local Non-Git Directory**
- Extract `repo_name`: `basename(path)`
- Use path directly for analysis (no copy)
- Analysis output: `~/.scv/analysis/{repo_name}/`

### Step 4: Prepare Repository for Analysis

Based on the detected type:

**For Remote Git URL:**

1. **Check if repository already exists** at `~/.scv/repos/{repo_name}`:
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
   - If user chooses 3: Skip clone, use existing

2. **Clone repository** (if not exists or user chose to re-clone):
   ```bash
   cd ~/.scv/repos
   git clone {git_url} {repo_name}
   ```
   - If branch specified in URL format: `git clone -b {branch} {git_url} {repo_name}`
   - Capture and display output

3. **Verify clone success**:
   - Check if directory was created
   - Verify it's a valid Git repository
   - Show repository info:
     ```
     ✅ Repository cloned successfully
     📁 Path: ~/.scv/repos/{repo_name}
     🔗 URL: {git_url}
     🌿 Branch: {current_branch}
     📦 Latest commit: {commit_hash} - {commit_message}
     ```

**For Local Git Repository:**

1. **Check if repository already exists** at `~/.scv/repos/{repo_name}`:
   - If exists: Ask user (same options as remote)
   - If not exists: Clone the local repository

2. **Clone local repository**:
   ```bash
   cd ~/.scv/repos
   git clone {local_path} {repo_name}
   ```
   - This creates a copy in `~/.scv/repos/{repo_name}`
   - Capture and display output

3. **Verify clone success**:
   ```
   ✅ Local repository cloned successfully
   📁 Source: {local_path}
   📁 Destination: ~/.scv/repos/{repo_name}
   ```

**For Local Non-Git Directory:**

1. **Verify directory exists** and is accessible
2. **Verify readable permissions**
3. Show confirmation:
   ```
   ✅ Local directory confirmed
   📁 Path: {local_path}
   Type: Non-Git directory (analyzing directly)
   ```

### Step 5: Finalize Paths and Names

After repository preparation:

1. **Determine analysis path**:
   - Remote URL: `~/.scv/repos/{repo_name}`
   - Local Git: `~/.scv/repos/{repo_name}`
   - Local non-Git: Original path

2. **Determine output path**: Always `~/.scv/analysis/{repo_name}/`

3. **Determine project name**:
   - Use user-provided `project_name` if specified
   - Otherwise use `repo_name`

4. **Create output directory**:
   ```bash
   mkdir -p ~/.scv/analysis/{repo_name}
   ```

5. **Display analysis plan**:
   ```
   📋 Analysis Plan

   Project name: {project_name}
   Repository type: {remote/local-git/local-non-git}

   Repository location:
   {analysis_path}

   Output directory:
   ~/.scv/analysis/{repo_name}/

   Generating 4 documents:
     📄 README.md
     📄 SUMMARY.md
     📄 ARCHITECTURE.md
     📄 FILE_INDEX.md
   ```

### Step 6: Load Templates and Prompts

Load from SCV project context:

- **Analyzer Prompt**: `prompts/project-analyzer.md`
- **Templates**:
  - `prompts/templates/README.template.md`
  - `prompts/templates/SUMMARY.template.md`
  - `prompts/templates/ARCHITECTURE.template.md`
  - `prompts/templates/FILE_INDEX.template.md`

### Step 7: Execute Analysis Workflow

Execute the 3-phase analysis as defined in `project-analyzer.md`:

**Phase 1: Global Scan (全局扫描)**

1. Identify technology stack using fingerprint patterns:
   - Scan for package.json, pom.xml, go.mod, requirements.txt, Cargo.toml, etc.
   - Detect framework markers (@SpringBootApplication, FastAPI(), React hooks, etc.)
   - Determine primary programming language

2. Map project structure:
   - Build directory tree (depth 4-5 levels)
   - Count file types and distributions
   - Locate entry points (main.*, index.*, App.*)
   - List configuration files
   - Identify test file locations

**Phase 2: Deep File Analysis (深度文件分析)**

Analyze files by priority:

- **Priority 1 (Deep Dive)**:
  - Entry files
  - Configuration files (*.yml, *.toml, settings.py)
  - Route definitions (urls.py, router.*, routes/*)
  - Core business logic (services/*, domain/*, core/*)
  - Data models (models/*, entities/*, schemas/*)

- **Priority 2 (Selective)**:
  - Utilities, middleware, type definitions

- **Priority 3 (Quick Browse)**:
  - Test files, static assets, generated files

For each analyzed file, extract:
- Basic info: path, type, line count
- Core content: responsibility (1-sentence), exports, key implementation
- Dependencies: internal, external, dependents

**Phase 3: Documentation Generation (文档生成)**

Generate 4 documents in `~/.scv/analysis/{repo_name}/`:

1. **README.md** - Project overview entry point
2. **SUMMARY.md** - 5-minute project summary
3. **ARCHITECTURE.md** - Architecture and design decisions
4. **FILE_INDEX.md** - File responsibility index

For each document:
- Use the corresponding template from `prompts/templates/`
- Replace placeholders `{xxx}` with actual analysis results
- Respect conditional rendering: `<!-- IF xxx -->`, `<!-- END IF -->`
- Handle loop rendering: `<!-- FOR xxx -->`, `<!-- END FOR -->`
- Generate appropriate Mermaid diagrams
- Output in Chinese

### Step 8: Template Processing Rules

**Placeholder Replacement:**
- All `{xxx}` placeholders must be replaced with actual content
- Mark uncertain items with `[待确认]`

**Conditional Rendering:**
- Check condition (e.g., `has_links`, `has_modules`)
- Include content between `<!-- IF xxx -->` and `<!-- END IF -->` only if condition is true
- Remove entire conditional block if condition is false

**Loop Rendering:**
- Identify arrays of items (modules, requirements, links, etc.)
- Repeat the content between `<!-- FOR xxx -->` and `<!-- END FOR -->` for each item
- Replace loop-specific placeholders within the block

**Format Preservation:**
- Maintain Markdown formatting exactly
- Preserve table structures
- Keep code block styles
- Use Chinese for all user-facing text

### Step 9: Output Validation

After generating all 4 documents, verify:

- All required files exist in `~/.scv/analysis/{repo_name}/`
- No unreplaced placeholders (except intentional `[待确认]`)
- Valid Markdown syntax
- Consistent Chinese language throughout
- All templates were properly processed

### Step 10: Report Completion

Output a summary including:

```
✅ Analysis completed for: {project_name}

Repository information:
  📁 Type: {remote/local-git/local-non-git}
  📂 Location: {analysis_path}
  🌿 Branch: {branch} (for Git repositories)
  📦 Latest commit: {commit_hash} - {commit_message} (for Git repositories)

Output directory:
  📂 ~/.scv/analysis/{repo_name}/

Generated documents:
  📄 README.md           - Project overview
  📄 SUMMARY.md          - 5-minute summary
  📄 ARCHITECTURE.md     - Architecture details
  📄 FILE_INDEX.md       - File index

Next steps:
  - Review generated documents
  - Open README.md to explore the project: open ~/.scv/analysis/{repo_name}/README.md

Repository management:
  - To update this repo: /scv.gather --update {repo_name}
  - To list all repos: /scv.gather --list
  - To remove this repo: /scv.gather --remove {repo_name}
```

## Context

$ARGUMENTS

## Analysis Principles

1. **Code is truth** - Base analysis on actual code, not potentially outdated comments
2. **Naming reveals intent** - Good naming is the best documentation
3. **Dependencies expose architecture** - Import statements reveal true dependencies
4. **Tests document behavior** - Test cases are the most accurate usage examples
5. **Configuration defines boundaries** - Config files reveal system integration points
6. **Progressive deep dive** - Start global, then local; start skeleton, then flesh

## Error Handling

**Remote URL errors:**
- If URL is invalid: Report error and suggest correct format
- If clone fails: Check network connection and Git credentials
- If authentication required: Guide user to configure Git credentials

**Local Git repository errors:**
- If path doesn't exist: Report error with path
- If clone fails: Check if directory is a valid Git repository
- If permissions denied: Check directory read permissions

**Local non-Git directory errors:**
- If path doesn't exist: Report error with path
- If not accessible: Check directory read permissions
- If directory is empty: Warn but proceed with minimal documentation

**Analysis errors:**
- If template missing: Use fallback structure
- If analysis fails partially: Generate what's possible and report warnings
- If repository is empty: Warn but proceed with minimal documentation

**Directory errors:**
- If cannot create `~/.scv/repos`: Check permissions
- If cannot create `~/.scv/analysis`: Check permissions
- If insufficient disk space: Report error and suggest cleanup

## Integration with Other Commands

After running `scv.run`, the repository will be available for other SCV commands:

**For remote or local Git repositories:**
- Repository is stored in `~/.scv/repos/{repo_name}`
- Can be updated with: `/scv.gather --update {repo_name}`
- Can be listed with: `/scv.gather --list`
- Can be removed with: `/scv.gather --remove {repo_name}`
- Can be included in batch analysis by adding to `~/.scv/config.json`

**For local non-Git directories:**
- Repository is not copied to `~/.scv/repos`
- Analysis output is still in `~/.scv/analysis/{repo_name}/`
- Cannot be managed by `scv.gather` (not a Git repository)
- Can still be included in batch analysis as `type: "local"` in config

**Typical workflow:**

```bash
# 1. Analyze a remote repository
/scv.run https://github.com/user/project.git

# 2. Repository is now in ~/.scv/repos/project
# Analysis is in ~/.scv/analysis/project/

# 3. Update repository later
/scv.gather --update project

# 4. Re-analyze after update
/scv.run ~/.scv/repos/project
```

```bash
# 1. Analyze a local Git repository
/scv.run ~/projects/my-app

# 2. Repository is now cloned to ~/.scv/repos/my-app
# Analysis is in ~/.scv/analysis/my-app/

# 3. Update original local repo
cd ~/projects/my-app
git pull

# 4. Re-clone to update cached copy
/scv.gather --update my-app
```

```bash
# 1. Analyze a local non-Git directory
/scv.run ~/my-folder

# 2. Analysis is in ~/.scv/analysis/my-folder/
# No copy is made to ~/.scv/repos

# 3. To add to batch analysis config:
cat >> ~/.scv/config.json <<EOF
{
  "type": "local",
  "path": "~/my-folder",
  "project_name": "My Folder"
}
EOF

# 4. Now can batch analyze with other repos
/scv.batchRun
```
