#!/bin/bash

# SCV Installation Script - Installs SCV (Source Code Vault) for Codex or Claude Code
# Supports Windows (Git Bash, MSYS2, Cygwin), macOS, and Linux

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

detect_os() {
    if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        echo "windows"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    else
        echo "linux"
    fi
}

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --lang=LANG, --lang LANG        Set language (en or zh-cn, default: en)"
    echo "  --target=TARGET, --target TARGET"
    echo "                                  Install target: codex, claude, or all (default: claude)"
    echo "  --platform=TARGET               Alias for --target"
    echo "  -h, --help                      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                              # Install English skill for Claude Code"
    echo "  $0 --lang=zh-cn                 # Install Chinese skill for Claude Code"
    echo "  $0 --target=codex               # Install for Codex"
    echo "  $0 --target=all --lang=zh-cn    # Install Chinese skill for both"
}

OS_TYPE=$(detect_os)
SKILL_LANG="en"
INSTALL_TARGET="claude"

while [[ $# -gt 0 ]]; do
    case $1 in
        --lang=*)
            SKILL_LANG="${1#*=}"
            shift
            ;;
        --lang)
            SKILL_LANG="$2"
            shift 2
            ;;
        --target=*)
            INSTALL_TARGET="${1#*=}"
            shift
            ;;
        --target)
            INSTALL_TARGET="$2"
            shift 2
            ;;
        --platform=*)
            INSTALL_TARGET="${1#*=}"
            shift
            ;;
        --platform)
            INSTALL_TARGET="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

if [[ "$SKILL_LANG" != "en" && "$SKILL_LANG" != "zh-cn" ]]; then
    echo -e "${RED}Error: Unsupported language '$SKILL_LANG'${NC}"
    echo "Supported languages: en, zh-cn"
    exit 1
fi

if [[ "$INSTALL_TARGET" != "codex" && "$INSTALL_TARGET" != "claude" && "$INSTALL_TARGET" != "all" ]]; then
    echo -e "${RED}Error: Unsupported target '$INSTALL_TARGET'${NC}"
    echo "Supported targets: codex, claude, all"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -f "$SCRIPT_DIR/config.example.json" ]; then
    echo -e "${RED}Please run this script from the SCV project root directory${NC}"
    exit 1
fi

SCV_SKILL_SRC="$SCRIPT_DIR/skills/$SKILL_LANG"
SCV_SCRIPTS_SRC="$SCRIPT_DIR/skills/scripts"
SCV_AGENT_SRC="$SCRIPT_DIR/agents/$SKILL_LANG/project-analyzer.md"

SCV_DATA_DIR="$HOME/.scv"
SCV_SCRIPTS_DATA_DIR="$SCV_DATA_DIR/scripts"

CLAUDE_DIR="$HOME/.claude"
CLAUDE_SKILLS_DIR="$CLAUDE_DIR/skills"
CLAUDE_AGENTS_DIR="$CLAUDE_DIR/agents"
CLAUDE_SKILL_TARGET_DIR="$CLAUDE_SKILLS_DIR/scv"

CODEX_SKILLS_DIR="${CODEX_SKILLS_DIR:-$HOME/.agents/skills}"
CODEX_SKILL_TARGET_DIR="$CODEX_SKILLS_DIR/scv"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  SCV (Source Code Vault) Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}OS Detected:${NC} $OS_TYPE"
echo -e "${GREEN}Language:${NC} $SKILL_LANG"
echo -e "${GREEN}Target:${NC} $INSTALL_TARGET"
echo -e "${GREEN}Source:${NC}"
echo "  Skill: $SCV_SKILL_SRC"
echo "  Scripts: $SCV_SCRIPTS_SRC"
echo "  Analyzer: $SCV_AGENT_SRC"
echo -e "${GREEN}Data:${NC} $SCV_DATA_DIR"
echo ""

if [ "$OS_TYPE" = "windows" ]; then
    echo -e "${YELLOW}Windows Detected${NC}"
    echo -e "${YELLOW}Note: On Windows, files will be copied instead of linked.${NC}"
    echo -e "${YELLOW}You'll need to re-run this script after making changes to skills.${NC}"
    echo ""
fi

if [ ! -d "$SCV_SKILL_SRC" ]; then
    echo -e "${RED}Error: Skill not found: $SCV_SKILL_SRC${NC}"
    echo "Available languages:"
    find "$SCRIPT_DIR/skills" -mindepth 1 -maxdepth 1 -type d -not -name scripts -exec basename {} \;
    exit 1
fi

if [ ! -f "$SCV_AGENT_SRC" ]; then
    echo -e "${RED}Error: Analyzer prompt not found: $SCV_AGENT_SRC${NC}"
    echo "Available languages:"
    find "$SCRIPT_DIR/agents" -mindepth 1 -maxdepth 1 -type d -exec basename {} \;
    exit 1
fi

create_dir() {
    local dir=$1
    if [ ! -d "$dir" ]; then
        echo -e "${YELLOW}Creating directory:${NC} $dir"
        mkdir -p "$dir"
    else
        echo -e "${GREEN}Directory exists:${NC} $dir"
    fi
}

link_or_copy() {
    local source=$1
    local target=$2
    local name=$3

    if [ "$OS_TYPE" = "windows" ]; then
        if [ -e "$target" ]; then
            echo -e "${YELLOW}Updating:${NC} $name"
            rm -rf "$target"
        else
            echo -e "${GREEN}Installing:${NC} $name"
        fi
        if [ -d "$source" ]; then
            cp -r "$source" "$target"
        else
            cp "$source" "$target"
        fi
        return
    fi

    if [ -L "$target" ]; then
        local current_target
        current_target=$(readlink "$target")
        if [ "$current_target" = "$source" ]; then
            echo -e "${GREEN}Already linked:${NC} $name"
        else
            echo -e "${YELLOW}Updating link:${NC} $name"
            rm "$target"
            ln -s "$source" "$target"
        fi
    elif [ -e "$target" ]; then
        echo -e "${RED}Conflict:${NC} $target exists and is not a symlink"
        echo -e "${YELLOW}Please manually remove or backup:${NC} $target"
        return 1
    else
        echo -e "${GREEN}Linking:${NC} $name"
        ln -s "$source" "$target"
    fi
}

install_skill_files() {
    local target_dir=$1
    local label=$2

    create_dir "$target_dir"

    shopt -s nullglob
    local skill_files=("$SCV_SKILL_SRC"/*)
    shopt -u nullglob

    for skill_file in "${skill_files[@]}"; do
        local file_name
        file_name=$(basename "$skill_file")
        link_or_copy "$skill_file" "$target_dir/$file_name" "$label/$file_name"
    done

    if [ -d "$SCV_SCRIPTS_SRC" ]; then
        link_or_copy "$SCV_SCRIPTS_SRC" "$target_dir/scripts" "$label/scripts"
    else
        echo -e "${YELLOW}No scripts directory found, skipping${NC}"
    fi
}

install_codex() {
    echo -e "\n${BLUE}Installing Codex skill${NC}"
    create_dir "$CODEX_SKILLS_DIR"
    install_skill_files "$CODEX_SKILL_TARGET_DIR" "codex scv"
    link_or_copy "$SCV_AGENT_SRC" "$CODEX_SKILL_TARGET_DIR/project-analyzer.md" "codex scv/project-analyzer.md"
}

install_claude() {
    echo -e "\n${BLUE}Installing Claude Code skill and agent${NC}"
    create_dir "$CLAUDE_DIR"
    create_dir "$CLAUDE_SKILLS_DIR"
    create_dir "$CLAUDE_AGENTS_DIR"
    install_skill_files "$CLAUDE_SKILL_TARGET_DIR" "claude scv"
    link_or_copy "$SCV_AGENT_SRC" "$CLAUDE_AGENTS_DIR/project-analyzer.md" "claude project-analyzer.md"
}

echo -e "\n${BLUE}Step 1: Creating SCV data directory${NC}"
create_dir "$SCV_DATA_DIR"
create_dir "$SCV_DATA_DIR/repos"
create_dir "$SCV_DATA_DIR/analysis"
create_dir "$SCV_DATA_DIR/sessions"

if [ -f "$SCV_DATA_DIR/config.json" ]; then
    echo -e "${GREEN}config.json already exists, skipping${NC}"
else
    cp "$SCRIPT_DIR/config.example.json" "$SCV_DATA_DIR/config.json"
    echo -e "${GREEN}Installed:${NC} config.json"
fi

if [ -d "$SCV_SCRIPTS_SRC" ]; then
    link_or_copy "$SCV_SCRIPTS_SRC" "$SCV_SCRIPTS_DATA_DIR" "shared scripts (~/.scv/scripts)"
fi

case "$INSTALL_TARGET" in
    codex)
        install_codex
        ;;
    claude)
        install_claude
        ;;
    all)
        install_codex
        install_claude
        ;;
esac

echo -e "\n${BLUE}Verification${NC}"

if [[ "$INSTALL_TARGET" == "codex" || "$INSTALL_TARGET" == "all" ]]; then
    echo -e "\n${YELLOW}Codex skill:${NC} $CODEX_SKILL_TARGET_DIR"
    if [ -d "$CODEX_SKILL_TARGET_DIR" ]; then
        find "$CODEX_SKILL_TARGET_DIR" -maxdepth 1 -mindepth 1 -exec basename {} \; | sort | sed 's/^/  /'
    else
        echo -e "${RED}  skill directory not found${NC}"
    fi
fi

if [[ "$INSTALL_TARGET" == "claude" || "$INSTALL_TARGET" == "all" ]]; then
    echo -e "\n${YELLOW}Claude Code skill:${NC} $CLAUDE_SKILL_TARGET_DIR"
    if [ -d "$CLAUDE_SKILL_TARGET_DIR" ]; then
        find "$CLAUDE_SKILL_TARGET_DIR" -maxdepth 1 -mindepth 1 -exec basename {} \; | sort | sed 's/^/  /'
    else
        echo -e "${RED}  skill directory not found${NC}"
    fi

    echo -e "\n${YELLOW}Claude Code analyzer agent:${NC}"
    if [ -e "$CLAUDE_AGENTS_DIR/project-analyzer.md" ]; then
        echo -e "${GREEN}  installed${NC} $CLAUDE_AGENTS_DIR/project-analyzer.md"
    else
        echo -e "${RED}  not installed${NC}"
    fi
fi

echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}SCV installation complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}Configuration:${NC}"
echo "  Language: $SKILL_LANG"
echo "  Target: $INSTALL_TARGET"
echo "  Data directory: $SCV_DATA_DIR"
echo "  Shared scripts: $SCV_SCRIPTS_DATA_DIR"
if [[ "$INSTALL_TARGET" == "codex" || "$INSTALL_TARGET" == "all" ]]; then
    echo "  Codex skill: $CODEX_SKILL_TARGET_DIR"
fi
if [[ "$INSTALL_TARGET" == "claude" || "$INSTALL_TARGET" == "all" ]]; then
    echo "  Claude skill: $CLAUDE_SKILL_TARGET_DIR"
    echo "  Claude agent: $CLAUDE_AGENTS_DIR/project-analyzer.md"
fi
echo ""
echo -e "${GREEN}Use SCV by asking your agent:${NC}"
echo "  /scv run <path|url>     - Analyze a single repository"
echo "  /scv batchRun           - Batch analyze configured repositories"
echo "  /scv gather <options>   - Clone and manage repositories"
echo ""
echo -e "${GREEN}For more information, see README.md${NC}"
