# Content Review Engine

[English README](README.en.md)

Content Review Engine 是一个以 Python 包为核心的 Markdown 内容审计工具。
它使用可配置的审计 profile 对 Markdown 内容进行检查，并通过 CLI、Python
API 和本地 MCP Server 返回结构化结果。

这个项目的核心原则是：审计逻辑集中在 `src/content_review_engine/`，CLI、API
和 MCP 都只是同一套核心工作流的适配层。

## 项目亮点

- 基于规则的 Markdown 内容审计，返回结构化 finding 和源码定位信息
- YAML profile 配置，支持内置模板和独立校验
- 内置规则覆盖禁用词、绝对化表述、Markdown 结构、链接与图片卫生检查
- 支持 profile 自定义 `regex_rules`，并保留稳定的 `rule_id`
- 支持单文件与批量目录审计
- 支持文本、JSON、Markdown 和 combined 输出产物
- 支持可选 LLM sidecar 审计，并明确区分 deterministic / LLM / combined 边界
- 提供稳定的 Python API，适合进程内集成
- 提供本地 MCP Server，复用同一套 Python API
- 提供统一的端到端 demo 工作区，内含 CLI、API、MCP 的提交产物

## 当前状态

项目已经不再处于初始化阶段，目前已经具备以下可用能力：

- 核心 Markdown 解析、profile 加载、规则执行、报告渲染能力
- `content-review review`、`batch`、`profile`、`llm-check` CLI 命令
- 稳定的 Python 工作流入口 `content_review_engine.api`
- 可选的本地 MCP Server 入口 `content_review_engine.mcp_server`
- 独立于 deterministic 结果的 mock / real-provider LLM 适配路径

当前最稳定、最适合自动化消费的仍然是 deterministic 审计结果层。

## 安装

环境要求：

- Python 3.13+
- `uv`

在仓库根目录安装依赖：

```bash
uv sync
```

如果你还需要 MCP Server 入口：

```bash
uv sync --extra mcp
```

验证 CLI 是否可用：

```bash
uv run content-review --help
```

## 快速开始

查看内置 profile 模板：

```bash
uv run content-review profile list
```

从模板创建一个本地 profile：

```bash
mkdir -p profiles
uv run content-review profile init \
  --template wechat-article \
  --output profiles/my-wechat.yaml
```

校验 profile：

```bash
uv run content-review profile validate profiles/my-wechat.yaml
```

审计一个 Markdown 文件：

```bash
uv run content-review review \
  examples/demo/articles/wechat-demo.md \
  --profile profiles/my-wechat.yaml
```

导出 Markdown 报告：

```bash
uv run content-review review \
  examples/demo/articles/wechat-demo.md \
  --profile profiles/my-wechat.yaml \
  --format markdown \
  --output /tmp/review-report.md
```

执行批量审计：

```bash
uv run content-review batch \
  examples/demo/articles \
  --profile profiles/my-wechat.yaml \
  --recursive
```

更完整的首次使用流程见 [docs/QUICKSTART.md](docs/QUICKSTART.md)。

## 项目当前能审计什么

当前 deterministic 审计主要覆盖：

- 配置的禁用词或风险词
- 配置的绝对化、夸张化表述
- profile 自定义正则模式
- Markdown 标题和段落结构问题
- 明显的 Markdown 链接和图片占位问题

profile 还可以进一步控制：

- 启用哪些规则
- 严重级别阈值
- allowlist
- 标题/段落长度限制
- 自定义 regex 规则

内置 profile 模板位于 [profiles/examples](profiles/examples)。

## 输出模型

项目明确区分三类产物：

- Deterministic 输出：标准 `ReviewResult` 或 `BatchReviewResult`
- 原始 LLM sidecar：标准 `LLMReviewResult` 或 `LLMSidecarResult`
- Combined 输出：显式集成产物，同时保留 deterministic 和 LLM 两层

几个重要边界：

- deterministic 输出是主自动化契约
- LLM 审计必须显式开启
- LLM findings 不会合并进 deterministic findings
- deterministic `--fail-on` 与 LLM `--llm-fail-on` 是两套独立 gate
- `--combined-output` 不会自动启用 LLM 审计

## CLI 能力

主要命令：

```bash
uv run content-review review <markdown_file> --profile <profile_file>
uv run content-review batch <input_dir> --profile <profile_file>
uv run content-review profile validate <profile_file>
uv run content-review profile init --template <template_name> --output <file>
uv run content-review profile list
uv run content-review llm-check
```

常见用法：

```bash
uv run content-review review article.md --profile profile.yaml --format json
uv run content-review review article.md --profile profile.yaml --fail-on error
uv run content-review batch articles --profile profile.yaml --recursive
uv run content-review review article.md --profile profile.yaml --format markdown --output review.md
```

完整命令说明，包括 `--combined-output`、`--report-index`、
`--llm-output`、`--llm-report`、`--llm-fail-on`，见
[docs/CLI.md](docs/CLI.md)。

## Python API

稳定的进程内入口：

```python
from content_review_engine.api import review_batch, review_file
```

示例：

```python
from content_review_engine.api import review_file

result = review_file(
    "examples/demo/articles/wechat-demo.md",
    "examples/demo/profiles/wechat-demo.yaml",
)

print(result.review_result.summary.finding_count)
```

Python API 也支持直接写出 deterministic、原始 LLM 和 combined 产物，
无需通过 CLI shell out。

详细说明见 [docs/PYTHON_API.md](docs/PYTHON_API.md)。

## MCP Server

仓库提供了一个基于同一套 Python API 的本地 MCP Server 适配层。

启动方式：

```bash
uv run content-review-mcp
uv run python -m content_review_engine.mcp_server
```

当前 MCP Server 的定位是本地工具适配层，不是托管式 Web 服务。

工具名、JSON schema 和客户端接入说明见
[docs/MCP_SERVER.md](docs/MCP_SERVER.md)。

## 可选 LLM 审计

LLM 层是 deterministic 流水线之外的辅助适配层，不是替代层。

当前行为边界：

- 不配置 LLM 也可以完成 deterministic 审计
- LLM 审计必须显式开启
- 本地安全测试 provider 包括 `mock` 和 `pydantic-ai-testmodel`
- 真实 provider 当前通过 `pydanticai` 路径接入
- CLI 不会自动读取 `.env`
- CLI 参数不直接接收原始 API key

本地 mock 示例：

```bash
uv run content-review review article.md \
  --profile profile.yaml \
  --enable-llm \
  --llm-provider mock \
  --llm-output /tmp/article.llm.json
```

真实 provider 的配置和排查见
[docs/LLM_PROVIDER_USAGE.md](docs/LLM_PROVIDER_USAGE.md)。

## Demo 工作区

主要端到端 demo 位于 [examples/demo](examples/demo)。

它包含：

- demo 文章与 demo profile
- 一个可重放的脚本，用于生成提交过的产物
- CLI 的 deterministic 和 mock-LLM 产物
- Python API workflow 产物
- MCP 请求与响应快照

重放 demo：

```bash
uv run python examples/demo/run_demo.py
```

输出到自定义目录：

```bash
uv run python examples/demo/run_demo.py --output-root /tmp/content-review-demo
```

完整演示说明见 [examples/demo/README.md](examples/demo/README.md)。

## 仓库结构

```text
src/content_review_engine/   核心包、CLI、API、MCP、规则、报告
docs/                        面向使用者的文档
profiles/examples/           内置 profile 模板
examples/demo/               统一端到端 demo 工作区
examples/llm_review_artifacts/ LLM 参考产物
tests/                       自动化测试
tasks/                       任务式项目记录
decisions/                   架构决策记录
```

## 架构概览

当前适配层结构：

```text
CLI / Python API / MCP
        ↓
Shared workflow helpers
        ↓
Core review package
        ↓
Rules / Reports / Optional LLM adapter
```

核心包负责：

- Markdown 输入处理
- profile 加载与校验
- deterministic 审计执行
- quality gate 评估
- 结构化结果模型
- 报告渲染

适配层不应该复制核心审计逻辑。

更详细的架构说明见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)。

## 限制与边界

- 当前只审计 Markdown
- deterministic 规则是显式、可配置、profile 驱动的
- LLM 审计默认是 advisory，除非你显式开启它自己的 gate
- 项目不保证法律、医疗、广告、监管或平台合规
- MCP 支持当前以本地 `stdio` 使用为主

## 开发

安装开发依赖：

```bash
uv sync --extra mcp --group dev
```

运行测试：

```bash
uv run pytest
```

项目开发上下文见：

- [AGENTS.md](AGENTS.md)
- [PROJECT_STATE.md](PROJECT_STATE.md)
- [ROADMAP.md](ROADMAP.md)

## 文档导航

- [docs/QUICKSTART.md](docs/QUICKSTART.md)
- [docs/CLI.md](docs/CLI.md)
- [docs/PYTHON_API.md](docs/PYTHON_API.md)
- [docs/MCP_SERVER.md](docs/MCP_SERVER.md)
- [docs/RULES.md](docs/RULES.md)
- [docs/DATA_MODELS.md](docs/DATA_MODELS.md)
- [docs/LLM_PROVIDER_USAGE.md](docs/LLM_PROVIDER_USAGE.md)
- [examples/demo/README.md](examples/demo/README.md)
