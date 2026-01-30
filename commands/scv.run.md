---
description: Analyze a single code repository and generate structured documentation
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Perform deep code analysis on a single repository and generate comprehensive documentation in Chinese following the SCV project's template system.

## Outline

### Step 1: Parse Arguments

Parse `$ARGUMENTS` to extract:

- **repo_path** (REQUIRED): Absolute or relative path to the repository to analyze
- **output_dir** (OPTIONAL): Directory where analysis docs will be saved (default: `<SCV_ROOT>/analysis/{repo_name}`)
- **project_name** (OPTIONAL): Custom project name (default: repository folder name)

If no arguments provided, prompt user:
```
Usage: /scv.run <repo_path> [output_dir] [project_name]

Example: /scv.run ~/my-project ~/my-projects/docs "My Awesome Project"
```

### Step 2: Validate Repository

1. Check if `repo_path` exists and is a valid directory
2. Detect if it's a version control repository (git, svn, etc.)
3. Verify readable permissions
4. Extract project name if not provided:
   - From `repo_path`: basename of the directory

If validation fails, report error and exit.

### Step 3: Load Templates and Prompts

Load from SCV project context:

- **Analyzer Prompt**: `prompts/project-analyzer.md`
- **Templates**:
  - `prompts/templates/README.template.md`
  - `prompts/templates/SUMMARY.template.md`
  - `prompts/templates/ARCHITECTURE.template.md`
  - `prompts/templates/FILE_INDEX.template.md`

### Step 4: Execute Analysis Workflow

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

Generate 4 documents in `output_dir`:

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

### Step 5: Template Processing Rules

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

### Step 6: Output Validation

After generating all 4 documents, verify:

- All required files exist in `output_dir`
- No unreplaced placeholders (except intentional `[待确认]`)
- Valid Markdown syntax
- Consistent Chinese language throughout
- All templates were properly processed

### Step 7: Report Completion

Output a summary including:

```
✅ Analysis completed for: {project_name}
📁 Repository: {repo_path}
📂 Output directory: {output_dir}

Generated documents:
  📄 README.md           - Project overview
  📄 SUMMARY.md          - 5-minute summary
  📄 ARCHITECTURE.md     - Architecture details
  📄 FILE_INDEX.md       - File index

Next steps:
  - Review generated documents
  - Open README.md to explore the project
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

- If repository doesn't exist: Error with clear message
- If repository is empty: Warn but proceed with minimal documentation
- If template missing: Use fallback structure
- If analysis fails partially: Generate what's possible and report warnings
