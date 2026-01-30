# SCV - Source Code Vault

> 专为 Claude Code 设计的强大代码库管理和分析工具

[![GitHub Repository](https://img.shields.io/badge/GitHub-SCV-blue.svg)](https://github.com/ProjAnvil/SCV)

**SCV** 提供三个 Claude Code 命令用于全面的代码库管理和分析：

- **scv.gather** - 克隆和管理远程 Git 仓库（仅处理配置文件中的 `remote` 类型仓库）
- **scv.run** - 对单个代码库进行深度分析
- **scv.batchRun** - 批量分析多个代码库（自动拉取 `remote` 类型仓库的最新代码）

## 📖 语言 / Language

- [English](../README.md) | [中文文档](./README_CN.md)

## 目录

- [特性](#特性)
- [安装](#安装)
- [快速开始](#快速开始)
- [命令说明](#命令说明)
  - [scv.gather](#scv-gather---git-仓库管理)
  - [scv.run](#scv-run----单个代码库分析)
  - [scv.batchRun](#scv-batchrun---批量代码库分析)
- [配置文件](#配置文件)
- [模板系统](#模板系统)
- [输出文档说明](#输出文档说明)
- [工作流程](#工作流程)
- [最佳实践](#最佳实践)
- [Git 配置](#git-配置)
- [故障排除](#故障排除)

## 特性

- 🔄 **远程仓库管理**：克隆、更新和管理远程 Git 仓库
- 📊 **深度代码分析**：为任何代码库生成全面的文档
- 🚀 **批量处理**：一次性分析多个仓库
- 📝 **多种输出格式**：README、摘要、架构、文件索引
- 🤖 **远程仓库自动拉取**：始终分析最新代码
- 🎯 **灵活配置**：支持远程和本地仓库
- 📦 **统一配置**：单一配置文件用于所有操作

## 安装

您可以选择使用安装脚本快速安装，或手动安装。

### 选项 1：快速安装（推荐）

运行安装脚本：

```bash
# 默认（英文提示词）
./install.sh

# 或直接指定语言
./install.sh --lang=en
./install.sh --lang=zh-cn

# 查看帮助
./install.sh --help
```

该脚本将：
- 创建 `~/.scv` 配置目录
- 复制配置文件
- 复制所选语言的提示词模板（默认：英文）
- 复制命令文件到 Claude 目录

### 选项 2：手动安装

确保项目文件位于正确的位置：

```
/Users/yuhaochen/Documents/codebase/SCV/
  ├── commands/
  │   ├── scv.gather.md
  │   ├── scv.run.md
  │   └── scv.batchRun.md
  ├── prompts/
  │   ├── zh-cn/
  │   │   ├── project-analyzer.md
  │   │   └── templates/
  │   │       ├── README.template.md
  │   │       ├── SUMMARY.template.md
  │   │       ├── ARCHITECTURE.template.md
  │   │       └── FILE_INDEX.template.md
  │   └── en/
  │       ├── project-analyzer.md
  │       └── templates/
  │           ├── README.template.md
  │           ├── SUMMARY.template.md
  │           ├── ARCHITECTURE.template.md
  │           └── FILE_INDEX.template.md
  └── config.example.json
```

创建 SCV 配置目录：

```bash
mkdir -p ~/.scv
```

复制示例配置文件：

```bash
cp config.example.json ~/.scv/config.json
```

复制提示词模板到 SCV 主目录（选择您使用的语言）：

```bash
# 中文版本
cp -r prompts/zh-cn ~/.scv/prompts

# 英文版本
cp -r prompts/en ~/.scv/prompts
```

将命令文件复制到 Claude Code 命令目录：
```bash
cp -r commands/ ~/.claude/
```
或者创建符号链接：
```bash
ln -s $(pwd)/commands ~/.claude/commands
```

## 快速开始

### 1. 克隆仓库

```bash
/scv.gather https://github.com/user/project.git
```

### 2. 分析代码库

```bash
/scv.run ~/.scv/repos/project
```

### 3. 查看生成的文档

```bash
open ~/.scv/analysis/project/README.md
```

## 命令说明

### scv.gather - Git 仓库管理

#### 概述

从远程 Git 仓库克隆代码到本地 `~/.scv/repos` 目录，支持单个仓库操作和批量操作，以及仓库更新和列表管理。

#### 使用方法

```bash
# 克隆单个仓库
/scv.gather <git_url> [repo_name] [branch]

# 批量克隆
/scv.gather --batch [--config <path>]

# 更新仓库
/scv.gather --update [repo_name] | --update-all

# 列出所有仓库
/scv.gather --list

# 删除仓库
/scv.gather --remove <repo_name>
```

#### 单个仓库克隆

##### 参数说明

| 参数 | 必填 | 说明 | 默认值 |
|------|------|------|--------|
| `git_url` | 是 | Git 仓库 URL（HTTPS/GIT/SSH） | - |
| `repo_name` | 否 | 本地目录名称 | 从 URL 提取 |
| `branch` | 否 | 指定分支 | 仓库默认分支 |

##### 示例

```bash
# 基本克隆
/scv.gather https://github.com/user/project.git

# 指定仓库名称
/scv.gather https://github.com/user/project.git my-project

# 指定分支
/scv.gather https://github.com/user/project.git my-project develop

# 使用 SSH URL
/scv.gather git@github.com:user/project.git
```

##### 仓库位置

所有克隆的仓库统一存储在：
```
~/.scv/repos/
  ├── my-project/
  ├── another-repo/
  └── ...
```

#### 批量克隆

**注意**：`scv.gather --batch` 只处理配置文件中 `type: "remote"` 的仓库。

##### 配置文件

默认配置文件位置：`~/.scv/config.json`（与 `scv.batchRun` 共享同一配置文件）

##### 配置示例

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

**说明**：
- `type: "remote"` - 由 `scv.gather` 克隆和管理的远程仓库
- `type: "local"` - 本地仓库，`scv.gather` 不会处理，但 `scv.batchRun` 会分析
- `output_dir` - 统一的输出目录，所有分析都放在这里

##### 目录名自动提取

**Remote 仓库**：
- 从 URL 自动提取：`https://github.com/user/my-project.git` → `my-project`
- 克隆到：`~/.scv/repos/my-project/`
- 分析输出到：`~/.scv/analysis/my-project/`

**Local 仓库**：
- 从路径自动提取：`~/projects/my-app` → `my-app`
- 分析输出到：`~/.scv/analysis/my-app/`

#### 更新仓库

##### 更新单个仓库

```bash
# 更新指定仓库
/scv.gather --update my-project

# 不指定名称则列出仓库供选择
/scv.gather --update
```

##### 更新所有仓库

```bash
# 更新所有本地仓库
/scv.gather --update-all
```

#### 列出仓库

```bash
# 列出所有本地仓库
/scv.gather --list
```

输出示例：
```
📁 Local Repositories (stored in ~/.scv/repos/)

| Name          | Branch   | Last Commit          | URL                          |
|---------------|----------|----------------------|------------------------------|
| my-app        | main     | 2025-01-15 10:30    | github.com/user/my-app.git  |
| api-service   | develop  | 2025-01-14 14:22    | github.com/user/api.git     |
| cli-tools     | master   | 2025-01-10 09:15    | github.com/user/cli.git     |

Total: 3 repositories
```

#### 删除仓库

```bash
# 删除指定仓库（需要确认）
/scv.gather --remove my-project
```

### scv.run - 单个代码库分析

#### 概述

对一个代码库进行深度分析，生成以下文档：

- **README.md** - 项目总览入口
- **SUMMARY.md** - 项目摘要（5分钟了解项目全貌）
- **ARCHITECTURE.md** - 架构设计文档
- **FILE_INDEX.md** - 文件索引

#### 使用方法

```bash
/scv.run <repo_path> [output_dir] [project_name]
```

#### 参数说明

| 参数 | 必填 | 说明 | 默认值 |
|------|------|------|--------|
| `repo_path` | 是 | 代码库路径（绝对或相对路径） | - |
| `output_dir` | 否 | 输出目录 | `<SCV_ROOT>/analysis/{repo_name}` |
| `project_name` | 否 | 自定义项目名称 | 代码库文件夹名称 |

#### 示例

```bash
# 基本用法
/scv.run ~/projects/my-app

# 指定输出目录
/scv.run ~/projects/my-app ~/docs/my-app

# 完整参数
/scv.run ~/projects/my-app ~/docs/my-app "我的应用"
```

#### 分析流程

1. **全局扫描** - 识别技术栈、理解项目结构
2. **深度分析** - 逐文件解析，提取核心逻辑
3. **文档生成** - 按模板生成4个核心文档

### scv.batchRun - 批量代码库分析

#### 概述

从配置文件读取多个代码库配置，批量生成分析文档。支持远程仓库（自动 git pull）和本地仓库。

**重要特性**：
- **Remote 仓库**：分析前自动执行 `git pull`，确保分析最新代码
- **Local 仓库**：直接分析本地路径，不执行 git 操作
- **统一配置**：与 `scv.gather` 共享同一配置文件 `~/.scv/config.json`

#### 配置文件

配置文件位置：`~/.scv/config.json`（与 `scv.gather` 共享）

#### 配置示例

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

#### 配置字段说明

##### 根层级字段

| 字段 | 必填 | 说明 | 默认值 |
|------|------|------|--------|
| `output_dir` | 否 | 所有分析的输出目录 | `~/.scv/analysis` |
| `parallel` | 否 | 并行执行 | `false` |
| `fail_fast` | 否 | 遇到错误是否停止 | `false` |

##### repos 数组（必需）

**Remote Repository (远程仓库)**:
- **type**: `"remote"` (必需)
- **url**: Git 仓库 URL (必需)
- **project_name**: 项目名称 (可选，默认: 从 URL 提取的目录名)
- **branch**: 分支 (可选，默认: 仓库默认分支)

**Local Repository (本地仓库)**:
- **type**: `"local"` (必需)
- **path**: 本地路径 (必需，支持 `~` 相对路径)
- **project_name**: 项目名称 (可选，默认: 从 path 提取的目录名)

#### 分析行为

##### Remote 仓库（`type: "remote"`）

对于远程仓库，分析流程：

1. **本地路径**：`~/.scv/repos/{name}`
2. **自动克隆**：如果不存在，从 URL 克隆
3. **自动拉取**：分析前执行 `git pull {branch}`
4. **分析**：分析本地副本
5. **优势**：
   - 始终分析最新代码
   - 无需手动拉取
   - 本地缓存，访问快速

##### Local 仓库（`type: "local"`）

对于本地仓库，分析流程：

1. **路径**：使用提供的 `path` 直接分析
2. **无 git 操作**：不克隆，不拉取
3. **分析**：按原样分析目录
4. **优势**：
   - 分析进行中的代码
   - 无需网络连接
   - 完全控制分析内容

#### 创建配置文件

**统一配置文件**（用于 `scv.gather` 和 `scv.batchRun`）：

1. 首次使用前，创建配置文件：
   ```bash
   mkdir -p ~/.scv
   cp config.example.json ~/.scv/config.json
   ```

2. 编辑配置文件，添加你的代码库：
   ```bash
   vim ~/.scv/config.json
   ```

配置文件支持两种类型的代码库：
- **remote**: 远程 Git 仓库（`scv.gather` 克隆管理，`scv.batchRun` 自动拉取）
- **local**: 本地路径（`scv.gather` 不处理，`scv.batchRun` 直接分析）

#### 使用方法

```bash
# 分析配置文件中的所有代码库
/scv.batchRun
```

#### 执行模式

**顺序执行**（`parallel: false`，默认）：
- 逐个分析代码库
- 资源占用低
- 适合大规模批量分析

**并行执行**（`parallel: true`）：
- 同时分析多个代码库
- 速度更快
- 资源占用较高

#### 错误处理

**遇到错误继续**（`fail_fast: false`，默认）：
- 记录错误，继续分析其他代码库
- 最后显示汇总报告

**遇到错误停止**（`fail_fast: true`）：
- 第一个错误时停止整个批量任务
- 适合严格的验证场景

## 配置文件

### 设置

1. 创建配置目录：
   ```bash
   mkdir -p ~/.scv
   ```

2. 创建配置文件：
   ```bash
   cp config.example.json ~/.scv/config.json
   ```

3. 编辑配置：
   ```bash
   vim ~/.scv/config.json
   ```

### 配置结构

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

## 模板系统

分析基于预定义的模板：

- `prompts/project-analyzer.md` - 分析专家提示词
- `prompts/templates/README.template.md` - README 模板
- `prompts/templates/SUMMARY.template.md` - 摘要模板
- `prompts/templates/ARCHITECTURE.template.md` - 架构模板
- `prompts/templates/FILE_INDEX.template.md` - 文件索引模板

### 模板标记

- `{placeholder}` - 占位符替换
- `<!-- IF condition -->...<!-- END IF -->` - 条件渲染
- `<!-- FOR item -->...<!-- END FOR -->` - 循环渲染

## 输出文档说明

### README.md

项目总览，包含：
- 项目定位和价值
- 技术栈
- 文档导航
- 项目统计
- 核心模块速览
- 快速开始指南

### SUMMARY.md

5分钟快速了解项目，包含：
- 项目类型和核心功能
- 技术栈全景
- 目录结构
- 模块划分
- 数据模型
- API 概览
- 配置说明
- 注意事项

### ARCHITECTURE.md

架构设计文档，包含：
- 系统架构图（Mermaid）
- 技术选型说明
- 模块设计
- 数据流
- 接口设计
- 扩展性考虑

### FILE_INDEX.md

文件索引，包含：
- 所有文件的职责说明
- 文件依赖关系
- 关键类/函数说明
- 快速定位指南

## 工作流程

### 流程 1：克隆并立即分析

**目标**：分析 GitHub 上的一个开源项目

```bash
# 1. 克隆远程仓库
/scv.gather https://github.com/user/awesome-project.git

# 2. 立即分析
/scv.run ~/.scv/repos/awesome-project

# 3. 查看生成的文档
open ~/.scv/analysis/awesome-project/README.md
```

### 流程 2：团队项目文档化（远程 + 本地）

**目标**：为团队的多个项目生成文档，包括远程仓库和本地项目

```bash
# 1. 创建统一配置（包含 remote 和 local）
cat > ~/.scv/config.json <<EOF
{
  "output_dir": "~/.scv/analysis",
  "repos": [
    {
      "type": "remote",
      "url": "https://github.com/team/backend-api.git",
      "project_name": "后端 API",
      "branch": "main"
    },
    {
      "type": "remote",
      "url": "https://github.com/team/web-frontend.git",
      "project_name": "前端应用",
      "branch": "develop"
    },
    {
      "type": "local",
      "path": "~/projects/internal-docs",
      "project_name": "内部文档"
    }
  ],
  "parallel": true
}
EOF

# 2. 克隆所有远程仓库（可选，batchRun 会自动克隆/拉取）
/scv.gather --batch

# 3. 验证仓库
/scv.gather --list

# 4. 批量分析（remote 仓库会自动拉取最新代码）
/scv.batchRun
```

### 流程 3：定期更新项目文档

**目标**：保持项目文档与代码同步（推荐方式）

```bash
# 1. 配置好远程和本地仓库（参考流程 2）
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

# 2. 定期批量分析（推荐）
# 直接运行 batchRun，它会自动：
# - 拉取所有 remote 仓库的最新代码
# - 分析 local 仓库的当前状态
# - 所有分析输出到 ~/.scv/analysis/
/scv.batchRun
```

### 流程 4：竞品分析

**目标**：分析多个同类项目，进行技术对比

```bash
# 1. 克隆竞品项目
/scv.gather https://github.com/competitor1/project.git competitor1
/scv.gather https://github.com/competitor2/project.git competitor2
/scv.gather https://github.com/competitor3/project.git competitor3

# 2. 批量分析
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

# 3. 生成对比报告
# 手动对比各项目的 SUMMARY.md 和 ARCHITECTURE.md
```

### 流程 5：开源项目贡献前分析

**目标**：在提交 PR 前了解项目结构

```bash
# 1. 克隆项目
/scv.gather https://github.com/open-source/project.git

# 2. 分析项目
/scv.run ~/.scv/repos/project ~/contribution-analysis/project

# 3. 阅读 ARCHITECTURE.md 和 FILE_INDEX.md
# 了解模块划分和代码组织

# 4. 开始贡献
cd ~/.scv/repos/project
git checkout -b my-feature
# ... 开发和提交
```

## 最佳实践

### 单个代码库分析

1. **定期分析** - 在代码库重大变更后重新分析
2. **团队共享** - 将生成的文档添加到项目仓库
3. **持续更新** - 使用生成的文档作为基础，手动补充细节

### 批量代码库分析

1. **首次配置** - 使用顺序执行模式，确保每个代码库配置正确
2. **大规模分析** - 启用并行执行模式加速
3. **定期刷新** - 直接运行 `scv.batchRun`，它会自动拉取远程仓库最新代码
4. **混合使用** - 根据用途选择 remote 或 local：
   - Remote：稳定的生产代码，需要最新版本
   - Local：进行中的工作，或私有代码

### 配置管理

1. **版本控制** - 将 `~/.scv/config.json` 加入版本控制（排除敏感路径）
2. **统一配置** - `scv.gather` 和 `scv.batchRun` 共享同一配置文件
3. **分组管理** - 按项目、团队或用途分组配置
4. **类型选择** - 合理使用 remote 和 local 类型

## Git 配置

### HTTPS 克隆配置

如果使用 HTTPS URL，可能需要配置 Git 凭证：

```bash
# 配置用户信息
git config --global user.name "Your Name"
git config --global user.email "you@example.com"

# 配置凭证助手（首次克隆后保存凭证）
git config --global credential.helper store
```

### SSH 克隆配置

如果使用 SSH URL（推荐），需要配置 SSH 密钥：

```bash
# 1. 生成 SSH 密钥
ssh-keygen -t ed25519 -C "you@example.com"

# 2. 启动 SSH agent
eval "$(ssh-agent -s)"

# 3. 添加密钥到 agent
ssh-add ~/.ssh/id_ed25519

# 4. 复制公钥到 GitHub/GitLab
cat ~/.ssh/id_ed25519.pub
# 复制输出并添加到 GitHub Settings -> SSH and GPG keys

# 5. 测试连接
ssh -T git@github.com
```

### 网络加速（中国用户）

如果克隆速度慢，可以使用 Git 镜像：

```bash
# 使用 Gitee 镜像（适用于 GitHub 仓库）
# GitHub: https://github.com/user/repo.git
# Gitee:  https://gitee.com/user/repo.git

# 配置 Git 使用代理（如果有）
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890

# 取消代理
git config --global --unset http.proxy
git config --global --unset https.proxy
```

### Git 配置验证

```bash
# 查看当前 Git 配置
git config --global --list

# 验证 SSH 配置
ssh -T git@github.com

# 测试克隆（不下载历史）
git clone --depth 1 https://github.com/user/test-repo.git
```

## 故障排除

### 常见问题

**Q: 提示 "Configuration file not found"**

A: 创建 `~/.scv/config.json`，参考 `config.example.json`

**Q: Git 克隆失败，提示 authentication failed**

A:
1. 检查 Git 凭证配置（见上方 Git 配置章节）
2. 如果使用 HTTPS，确保已配置 `credential.helper`
3. 如果使用 SSH，确保 SSH 密钥已添加到 GitHub/GitLab
4. 测试连接：`git ls-remote <git_url>`

**Q: 克隆速度太慢**

A:
1. 使用浅克隆：`git clone --depth 1 <url>`
2. 配置代理（如果有）
3. 使用镜像站点（如 Gitee）

**Q: 分析输出不完整**

A: 检查代码库权限，确保可以读取所有文件

**Q: 模板文件缺失**

A: 确保 `prompts/templates/` 目录下有所有模板文件

**Q: 并行执行资源不足**

A: 修改 `parallel: false` 改为顺序执行

**Q: 仓库已存在，如何更新**

A:
- 更新单个仓库：`/scv.gather --update <repo_name>`
- 更新所有仓库：`/scv.gather --update-all`
- 重新克隆：先删除再克隆

**Q: 批量克隆时部分失败**

A:
1. 检查失败仓库的 URL 是否有效
2. 检查网络连接
3. 检查 Git 凭证配置
4. 查看错误日志了解具体原因

### 调试技巧

1. **单个测试** - 先用 `scv.run` 测试单个代码库
2. **查看日志** - 命令会显示详细执行过程
3. **检查输出** - 验证生成的文档是否完整
4. **调整配置** - 根据实际情况调整配置参数

## 贡献

欢迎贡献！请随时提交 Pull Request。

## 许可证

本项目采用 MIT 许可证。

## 链接

- **仓库地址**：[https://github.com/ProjAnvil/SCV](https://github.com/ProjAnvil/SCV)
- **English README**: [../README.md](../README.md)
