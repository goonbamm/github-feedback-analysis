# 🚀 GitHub 反馈分析工具

一个用于分析 GitHub 仓库活动并自动生成深度洞察报告的命令行工具。支持 GitHub.com 和 GitHub Enterprise，具备基于 LLM 的自动审查功能。

简体中文 | [한국어](../README.md) | [English](README_EN.md) | [日本語](README_JA.md) | [Español](README_ES.md)

## ✨ 核心功能

- 📊 **仓库分析**：按时间段聚合和分析提交、议题和审查活动
- 🤖 **基于 LLM 的反馈**：详细分析提交信息、PR 标题、审查语气和议题质量
- 🎯 **自动 PR 审查**：自动审查已认证用户的 PR 并生成集成回顾报告
- 🏆 **成就可视化**：根据贡献自动生成奖项和亮点
- 💡 **仓库发现**：列出可访问的仓库并推荐活跃仓库
- 🎨 **交互模式**：用户友好的仓库直接选择界面

## 📋 前置要求

- Python 3.11 或更高版本
- [uv](https://docs.astral.sh/uv/) 或您喜欢的包管理器
- GitHub Personal Access Token（个人访问令牌）
  - 私有仓库：需要 `repo` 权限
  - 公共仓库：需要 `public_repo` 权限
- LLM API 端点（OpenAI 兼容格式）

<details>
<summary><b>🔑 生成 GitHub Personal Access Token</b></summary>

使用本工具需要 GitHub Personal Access Token（PAT）。

### 生成步骤

1. **访问 GitHub 设置**
   - 前往 [GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)](https://github.com/settings/tokens)
   - 或：GitHub 个人资料 → Settings → Developer settings → Personal access tokens

2. **生成新令牌**
   - 点击 "Generate new token" → "Generate new token (classic)"
   - Note：输入令牌用途（例如："GitHub Feedback Analysis"）
   - Expiration：设置过期时间（建议：90天或自定义）

3. **选择权限**
   - **仅公共仓库**：勾选 `public_repo`
   - **包含私有仓库**：勾选整个 `repo`
   - 其他权限不需要

4. **生成并复制令牌**
   - 点击 "Generate token"
   - 复制生成的令牌（以 ghp_ 开头）并安全保存
   - ⚠️ **重要**：离开此页面后将无法再次查看令牌

5. **使用令牌**
   - 运行 `gfa init` 时输入复制的令牌

### 使用细粒度 Personal Access Token（可选）

使用更新的细粒度令牌：
1. 前往 [Personal access tokens → Fine-grained tokens](https://github.com/settings/personal-access-tokens/new)
2. Repository access：选择要分析的仓库
3. 设置权限：
   - **Contents**：Read-only（必需）
   - **Metadata**：Read-only（自动选择）
   - **Pull requests**：Read-only（必需）
   - **Issues**：Read-only（必需）

### 面向 GitHub Enterprise 用户

如果您在组织中使用 GitHub Enterprise：
1. **访问企业服务器令牌页面**
   - `https://github.your-company.com/settings/tokens`（替换为您公司的域名）
   - 或：个人资料 → Settings → Developer settings → Personal access tokens

2. **权限设置相同**
   - 私有仓库：`repo` 权限
   - 公共仓库：`public_repo` 权限

3. **初始设置时指定企业主机**
   ```bash
   gfa init --enterprise-host https://github.your-company.com
   ```

4. **联系管理员**
   - 某些企业环境可能限制 PAT 生成
   - 如遇问题，请联系您的 GitHub 管理员

### 参考资料

- [GitHub 文档：管理 Personal Access Tokens](https://docs.github.com/zh/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
- [GitHub 文档：细粒度 PAT](https://docs.github.com/zh/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#fine-grained-personal-access-tokens)
- [GitHub Enterprise Server 文档](https://docs.github.com/en/enterprise-server@latest/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)

</details>

## 🔧 安装

```bash
# 克隆仓库
git clone https://github.com/goonbamm/github-feedback-analysis.git
cd github-feedback-analysis

# 创建并激活虚拟环境
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装包
uv pip install -e .
```

## 🚀 快速入门

### 1️⃣ 初始化配置

```bash
gfa init
```

出现提示时，请输入以下信息：
- GitHub Personal Access Token（安全存储在系统密钥环中）
- LLM 端点（例如：`http://localhost:8000/v1/chat/completions`）
- LLM 模型（例如：`gpt-4`）
- GitHub Enterprise 主机（可选，仅当不使用 github.com 时）

### 2️⃣ 分析仓库

```bash
gfa feedback --repo goonbamm/github-feedback-analysis
```

分析完成后，将在 `reports/` 目录中生成以下文件：
- `metrics.json` - 分析数据
- `report.md` - Markdown 报告
- `report.html` - HTML 报告（包含可视化图表）
- `charts/` - SVG 图表文件
- `prompts/` - LLM 提示文件

### 3️⃣ 查看结果

```bash
cat reports/report.md
```

## 📚 命令参考

<details>
<summary><b>🎯 `gfa init` - 初始化配置</b></summary>

存储 GitHub 访问信息和 LLM 设置。

#### 基本用法（交互式）

```bash
gfa init
```

#### 示例：GitHub.com + 本地 LLM

```bash
gfa init \
  --pat ghp_xxxxxxxxxxxxxxxxxxxx \
  --llm-endpoint http://localhost:8000/v1/chat/completions \
  --llm-model gpt-4 \
  --months 12
```

#### 示例：GitHub Enterprise

```bash
gfa init \
  --pat ghp_xxxxxxxxxxxxxxxxxxxx \
  --enterprise-host https://github.company.com \
  --llm-endpoint http://localhost:8000/v1/chat/completions \
  --llm-model gpt-4
```

#### 选项说明

| 选项 | 描述 | 必需 | 默认值 |
|------|------|------|--------|
| `--pat` | GitHub Personal Access Token | ✅ | - |
| `--llm-endpoint` | LLM API 端点 | ✅ | - |
| `--llm-model` | LLM 模型标识符 | ✅ | - |
| `--months` | 默认分析周期（月） | ❌ | 12 |
| `--enterprise-host` | GitHub Enterprise 主机 | ❌ | github.com |

</details>

<details>
<summary><b>📊 `gfa feedback` - 仓库分析</b></summary>

分析仓库并生成详细反馈报告。

#### 基本用法

```bash
gfa feedback --repo owner/repo-name
```

#### 交互模式

无需直接指定仓库，可从推荐列表中选择仓库。

```bash
gfa feedback --interactive
```

或

```bash
gfa feedback  # 不使用 --repo 选项运行
```

#### 示例

```bash
# 分析公共仓库
gfa feedback --repo torvalds/linux

# 分析个人仓库
gfa feedback --repo myusername/my-private-repo

# 分析组织仓库
gfa feedback --repo microsoft/vscode

# 交互模式选择仓库
gfa feedback --interactive
```

#### 选项说明

| 选项 | 描述 | 必需 | 默认值 |
|------|------|------|--------|
| `--repo`, `-r` | 仓库（owner/name） | ❌ | - |
| `--output`, `-o` | 输出目录 | ❌ | reports |
| `--interactive`, `-i` | 交互式仓库选择 | ❌ | false |

#### 生成的报告

分析完成后，将在 `reports/` 目录中创建以下文件：

```
reports/
├── metrics.json              # 📈 原始分析数据
├── report.md                 # 📄 Markdown 报告
├── report.html               # 🎨 HTML 报告（包含可视化图表）
├── charts/                   # 📊 可视化图表（SVG）
│   ├── quality.svg          # 质量指标图表
│   ├── activity.svg         # 活动指标图表
│   ├── engagement.svg       # 参与度图表
│   └── ...                  # 其他特定领域图表
└── prompts/
    ├── commit_feedback.txt   # 💬 提交信息质量分析
    ├── pr_feedback.txt       # 🔀 PR 标题分析
    ├── review_feedback.txt   # 👀 审查语气分析
    └── issue_feedback.txt    # 🐛 议题质量分析
```

#### 分析内容

- ✅ **活动聚合**：统计提交、PR、审查和议题数量
- 🎯 **质量分析**：提交信息、PR 标题、审查语气、议题描述质量
- 🏆 **奖项**：根据贡献自动授予奖项
- 📈 **趋势**：每月活动趋势和速度分析

</details>

<details>
<summary><b>🎯 `gfa feedback` - 自动 PR 审查</b></summary>

自动审查已认证用户（PAT 所有者）的 PR 并生成集成回顾报告。

#### 基本用法

```bash
gfa feedback --repo owner/repo-name
```

#### 示例

```bash
# 审查你创建的所有 PR
gfa feedback --repo myusername/my-project
```

#### 选项说明

| 选项 | 描述 | 必需 | 默认值 |
|------|------|------|--------|
| `--repo` | 仓库（owner/name） | ✅ | - |

#### 执行过程

1. **PR 搜索** 🔍
   - 检索 PAT 认证用户创建的 PR 列表

2. **生成单独审查** 📝
   - 收集每个 PR 的代码更改和审查评论
   - 使用 LLM 生成详细审查
   - 保存到 `reviews/owner_repo/pr-{number}/` 目录

3. **集成回顾报告** 📊
   - 综合所有 PR 生成洞察
   - 保存到 `reviews/owner_repo/integrated_report.md`

#### 生成的文件

```
reviews/
└── owner_repo/
    ├── pr-123/
    │   ├── artefacts.json          # PR 原始数据
    │   ├── review_summary.json     # LLM 分析结果
    │   └── review.md               # Markdown 审查
    ├── pr-456/
    │   └── ...
    └── integrated_report.md        # 集成回顾报告
```

</details>

<details>
<summary><b>⚙️ `gfa config` - 配置管理</b></summary>

查看或修改配置设置。

#### `gfa config show` - 查看配置

查看当前存储的配置。

```bash
gfa config show
```

**示例输出：**

```
┌─────────────────────────────────────┐
│ GitHub Feedback Configuration       │
├─────────────┬───────────────────────┤
│ Section     │ Values                │
├─────────────┼───────────────────────┤
│ auth        │ pat = <set>           │
├─────────────┼───────────────────────┤
│ server      │ api_url = https://... │
│             │ web_url = https://... │
├─────────────┼───────────────────────┤
│ llm         │ endpoint = http://... │
│             │ model = gpt-4         │
└─────────────┴───────────────────────┘
```

> **注意：**`gfa show-config` 命令已弃用，已被 `gfa config show` 替代。

#### `gfa config set` - 设置配置值

修改单个配置值。

```bash
gfa config set <key> <value>
```

**示例：**

```bash
# 更改 LLM 模型
gfa config set llm.model gpt-4

# 更改 LLM 端点
gfa config set llm.endpoint http://localhost:8000/v1/chat/completions

# 更改默认分析周期
gfa config set defaults.months 6
```

#### `gfa config get` - 获取配置值

检索特定配置值。

```bash
gfa config get <key>
```

**示例：**

```bash
# 检查 LLM 模型
gfa config get llm.model

# 检查默认分析周期
gfa config get defaults.months
```

</details>

<details>
<summary><b>🔍 `gfa list-repos` - 仓库列表</b></summary>

列出可访问的仓库。

```bash
gfa list-repos
```

#### 示例

```bash
# 列出仓库（默认：最近更新的 20 个）
gfa list-repos

# 更改排序标准
gfa list-repos --sort stars --limit 10

# 按特定组织筛选
gfa list-repos --org myorganization

# 按创建日期排序
gfa list-repos --sort created --limit 50
```

#### 选项说明

| 选项 | 描述 | 默认值 |
|------|------|--------|
| `--sort`, `-s` | 排序标准（updated、created、pushed、full_name） | updated |
| `--limit`, `-l` | 最大显示数量 | 20 |
| `--org`, `-o` | 按组织名称筛选 | - |

</details>

<details>
<summary><b>💡 `gfa suggest-repos` - 仓库推荐</b></summary>

推荐适合分析的活跃仓库。

```bash
gfa suggest-repos
```

自动选择具有最近活动的仓库。综合考虑星标、分支、议题和最近更新。

#### 示例

```bash
# 默认推荐（最近 90 天内，10 个仓库）
gfa suggest-repos

# 推荐最近 30 天内活跃的 5 个仓库
gfa suggest-repos --limit 5 --days 30

# 按星标排序
gfa suggest-repos --sort stars

# 按活动分数排序（综合评估）
gfa suggest-repos --sort activity
```

#### 选项说明

| 选项 | 描述 | 默认值 |
|------|------|--------|
| `--limit`, `-l` | 最大推荐数量 | 10 |
| `--days`, `-d` | 最近活动周期（天） | 90 |
| `--sort`, `-s` | 排序标准（updated、stars、activity） | activity |

</details>

<details>
<summary><b>📁 配置文件</b></summary>

配置存储在 `~/.config/github_feedback/config.toml` 中，运行 `gfa init` 时自动创建。

### 配置文件示例

```toml
[version]
version = "1.0.0"

[auth]
# PAT 安全存储在系统密钥环中（不存储在此文件中）

[server]
api_url = "https://api.github.com"
graphql_url = "https://api.github.com/graphql"
web_url = "https://github.com"

[llm]
endpoint = "http://localhost:8000/v1/chat/completions"
model = "gpt-4"
timeout = 60
max_files_in_prompt = 10
max_retries = 3

[defaults]
months = 12
```

### 手动配置编辑

如需要，可以直接编辑配置文件或使用 `gfa config` 命令：

```bash
# 方法 1：使用 config 命令（推荐）
gfa config set llm.model gpt-4
gfa config show

# 方法 2：直接编辑
nano ~/.config/github_feedback/config.toml
```

</details>

<details>
<summary><b>📊 生成的文件结构</b></summary>

### `gfa feedback` 输出

```
reports/
├── metrics.json              # 📈 原始分析数据
├── report.md                 # 📄 Markdown 报告
├── report.html               # 🎨 HTML 报告（包含可视化图表）
├── charts/                   # 📊 可视化图表（SVG）
│   ├── quality.svg          # 质量指标图表
│   ├── activity.svg         # 活动指标图表
│   ├── engagement.svg       # 参与度图表
│   └── ...                  # 其他特定领域图表
└── prompts/
    ├── commit_feedback.txt   # 💬 提交信息质量分析
    ├── pr_feedback.txt       # 🔀 PR 标题分析
    ├── review_feedback.txt   # 👀 审查语气分析
    └── issue_feedback.txt    # 🐛 议题质量分析
```

### `gfa feedback` 输出

```
reviews/
└── owner_repo/
    ├── pr-123/
    │   ├── artefacts.json          # 📦 PR 原始数据（代码、审查等）
    │   ├── review_summary.json     # 🤖 LLM 分析结果（结构化数据）
    │   └── review.md               # 📝 Markdown 审查报告
    ├── pr-456/
    │   └── ...
    └── integrated_report.md        # 🎯 集成回顾报告（所有 PR 综合）
```

</details>

<details>
<summary><b>💡 使用示例</b></summary>

### 示例 1：快速入门 - 交互模式

```bash
# 1. 配置（仅首次）
gfa init

# 2. 获取仓库推荐
gfa suggest-repos

# 3. 使用交互模式分析
gfa feedback --interactive

# 4. 查看报告
cat reports/report.md
```

### 示例 2：开源项目分析

```bash
# 1. 配置（仅首次）
gfa init

# 2. 分析热门开源项目
gfa feedback --repo facebook/react

# 3. 查看报告
cat reports/report.md
```

### 示例 3：个人项目回顾

```bash
# 查看我的仓库列表
gfa list-repos --sort updated --limit 10

# 分析我的项目
gfa feedback --repo myname/my-awesome-project

# 自动审查我的 PR
gfa feedback --repo myname/my-awesome-project

# 查看集成回顾报告
cat reviews/myname_my-awesome-project/integrated_report.md
```

### 示例 4：团队项目绩效审查

```bash
# 查看组织仓库列表
gfa list-repos --org mycompany --limit 20

# 设置分析周期（最近 6 个月）
gfa config set defaults.months 6

# 分析组织仓库
gfa feedback --repo mycompany/product-service

# 审查团队成员 PR（每人使用自己的 PAT 运行）
gfa feedback --repo mycompany/product-service
```

</details>

<details>
<summary><b>🎯 奖项系统</b></summary>

根据仓库活动自动授予奖项：

### 基于提交的奖项
- 💎 **代码传奇**（1000+ 次提交）
- 🏆 **代码大师**（500+ 次提交）
- 🥇 **代码铁匠**（200+ 次提交）
- 🥈 **代码工匠**（100+ 次提交）
- 🥉 **代码学徒**（50+ 次提交）

### 基于 PR 的奖项
- 💎 **发布传奇**（200+ 个 PR）
- 🏆 **部署上将**（100+ 个 PR）
- 🥇 **发布船长**（50+ 个 PR）
- 🥈 **发布领航员**（25+ 个 PR）
- 🥉 **部署水手**（10+ 个 PR）

### 基于审查的奖项
- 💎 **知识传播者**（200+ 次审查）
- 🏆 **指导大师**（100+ 次审查）
- 🥇 **审查专家**（50+ 次审查）
- 🥈 **成长导师**（20+ 次审查）
- 🥉 **代码支持者**（10+ 次审查）

### 特殊奖项
- ⚡ **闪电开发者**（每月 50+ 次提交）
- 🤝 **协作大师**（每月 20+ 次 PR+审查）
- 🏗️ **大规模架构师**（5000+ 行更改）
- 📅 **坚持大师**（6 个月以上持续活动）
- 🌟 **多才多艺**（各领域均衡贡献）

</details>

<details>
<summary><b>🐛 故障排除</b></summary>

### PAT 权限错误

```
Error: GitHub API rejected the provided PAT
```

**解决方案**：验证 PAT 具有适当的权限
- 私有仓库：需要 `repo` 权限
- 公共仓库：需要 `public_repo` 权限
- 在 [GitHub Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens) 检查

### LLM 端点连接失败

```
Warning: Detailed feedback analysis failed: Connection refused
```

**解决方案**：
1. 验证 LLM 服务器正在运行
2. 验证端点 URL 正确（`gfa config show`）
3. 如需要，重新初始化配置：`gfa init`

### 仓库未找到

```
Error: Repository not found
```

**解决方案**：
- 验证仓库名称格式：`owner/repo`（例如：`torvalds/linux`）
- 对于私有仓库，验证 PAT 权限
- 对于 GitHub Enterprise，验证 `--enterprise-host` 配置

### 分析周期内无数据

```
No activity detected during analysis period.
```

**解决方案**：
- 尝试增加分析周期：`gfa init --months 24`
- 验证仓库是否活跃

</details>

<details>
<summary><b>👩‍💻 开发者指南</b></summary>

### 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/goonbamm/github-feedback-analysis.git
cd github-feedback-analysis

# 以开发模式安装（包括测试依赖）
uv pip install -e .[test]

# 运行测试
pytest

# 运行特定测试
pytest tests/test_analyzer.py -v

# 检查覆盖率
pytest --cov=github_feedback --cov-report=html
```

### 代码结构

```
github_feedback/
├── cli.py              # 🖥️  CLI 入口点和命令
├── collector.py        # 📡 GitHub API 数据收集
├── analyzer.py         # 📊 指标分析和计算
├── reporter.py         # 📄 报告生成（brief）
├── reviewer.py         # 🎯 PR 审查逻辑
├── review_reporter.py  # 📝 集成审查报告
├── llm.py             # 🤖 LLM API 客户端
├── config.py          # ⚙️  配置管理
├── models.py          # 📦 数据模型
└── utils.py           # 🔧 实用函数
```

</details>

## 🔒 安全

- **PAT 存储**：GitHub 令牌安全存储在系统密钥环中（不存储在明文文件中）
- **配置备份**：覆盖配置前自动创建备份
- **输入验证**：验证所有用户输入（PAT 格式、URL 格式、仓库格式）

## 📄 许可证

本项目采用 MIT 许可证。

## 🤝 贡献

随时欢迎错误报告、功能建议和 PR！

1. Fork 仓库
2. 创建您的功能分支（`git checkout -b feature/amazing-feature`）
3. 提交您的更改（`git commit -m 'Add amazing feature'`）
4. 推送到分支（`git push origin feature/amazing-feature`）
5. 开启一个 Pull Request

## 💬 反馈

如果您有问题或建议，请在 [Issues](https://github.com/goonbamm/github-feedback-analysis/issues) 中注册！
