# 统一 Demo 快捷手册

这个文档只保留统一 Demo 的最短使用方式。

完整说明看 [examples/demo/README.md](examples/demo/README.md)。

## 1. 安装依赖

在仓库根目录执行：

```bash
uv sync --extra mcp
```

之所以带 `mcp` extra，是因为统一 Demo 会同时生成 CLI、Python API 和
MCP 的演示产物。

## 2. 生成统一 Demo

把默认演示产物重新生成到仓库里的 `examples/demo/artifacts/`：

```bash
uv run python examples/demo/run_demo.py
```

如果你不想覆盖仓库内已有产物，可以输出到临时目录：

```bash
uv run python examples/demo/run_demo.py --output-root /tmp/content-review-demo
```

## 3. 生成后去哪里看

默认输出目录：

```text
examples/demo/artifacts/
  cli/
  api/
  mcp/
```

最常看的文件：

- `examples/demo/artifacts/cli/single-file/review.md`
- `examples/demo/artifacts/cli/single-file/combined.md`
- `examples/demo/artifacts/cli/single-file/report-index.md`
- `examples/demo/artifacts/api/single-file.workflow.json`
- `examples/demo/artifacts/mcp/single-file.response.json`

## 4. 相关命令清单

### 校验 Demo Profile

```bash
uv run python -m content_review_engine.cli profile validate \
  examples/demo/profiles/wechat-demo.yaml

uv run python -m content_review_engine.cli profile validate \
  examples/demo/profiles/technical-demo.yaml
```

### 单文件 CLI 演示

先看最基础的 deterministic 输出：

```bash
uv run python -m content_review_engine.cli review \
  examples/demo/articles/wechat-demo.md \
  --profile examples/demo/profiles/wechat-demo.yaml
```

生成 deterministic JSON、mock LLM sidecar 和 combined JSON：

```bash
uv run python -m content_review_engine.cli review \
  examples/demo/articles/wechat-demo.md \
  --profile examples/demo/profiles/wechat-demo.yaml \
  --format json \
  --output examples/demo/artifacts/cli/single-file/review.json \
  --enable-llm \
  --llm-provider mock \
  --llm-output examples/demo/artifacts/cli/single-file/llm-result.json \
  --combined-output examples/demo/artifacts/cli/single-file/combined.json \
  --combined-output-format json \
  --llm-fail-on warning
```

生成 deterministic Markdown、LLM Markdown、combined Markdown 和 report index：

```bash
uv run python -m content_review_engine.cli review \
  examples/demo/articles/wechat-demo.md \
  --profile examples/demo/profiles/wechat-demo.yaml \
  --format markdown \
  --output examples/demo/artifacts/cli/single-file/review.md \
  --enable-llm \
  --llm-provider mock \
  --llm-output examples/demo/artifacts/cli/single-file/llm-result.json \
  --llm-report examples/demo/artifacts/cli/single-file/llm-report.md \
  --combined-output examples/demo/artifacts/cli/single-file/combined.md \
  --combined-output-format markdown \
  --report-index examples/demo/artifacts/cli/single-file/report-index.md \
  --fail-on warning \
  --llm-fail-on warning
```

说明：

- 这条命令预期返回退出码 `1`，因为 deterministic 和 LLM gate 都设置成了 `warning`。
- 即使退出码为 `1`，对应 Markdown 产物仍然会先写出。

### 批量 CLI 演示

先看 deterministic batch 输出：

```bash
uv run python -m content_review_engine.cli batch \
  examples/demo/articles \
  --profile examples/demo/profiles/technical-demo.yaml \
  --pattern 'technical-*.md'
```

生成 batch JSON、mock LLM sidecar 和 combined JSON：

```bash
uv run python -m content_review_engine.cli batch \
  examples/demo/articles \
  --profile examples/demo/profiles/technical-demo.yaml \
  --pattern 'technical-*.md' \
  --format json \
  --output examples/demo/artifacts/cli/batch/review.json \
  --enable-llm \
  --llm-provider mock \
  --llm-output examples/demo/artifacts/cli/batch/llm-result.json \
  --combined-output examples/demo/artifacts/cli/batch/combined.json \
  --combined-output-format json \
  --llm-fail-on warning
```

生成 batch Markdown、LLM Markdown、combined Markdown 和 report index：

```bash
uv run python -m content_review_engine.cli batch \
  examples/demo/articles \
  --profile examples/demo/profiles/technical-demo.yaml \
  --pattern 'technical-*.md' \
  --format markdown \
  --output examples/demo/artifacts/cli/batch/review.md \
  --enable-llm \
  --llm-provider mock \
  --llm-output examples/demo/artifacts/cli/batch/llm-result.json \
  --llm-report examples/demo/artifacts/cli/batch/llm-report.md \
  --combined-output examples/demo/artifacts/cli/batch/combined.md \
  --combined-output-format markdown \
  --report-index examples/demo/artifacts/cli/batch/report-index.md \
  --fail-on warning \
  --llm-fail-on warning
```

说明：

- 这条命令同样预期返回退出码 `1`。
- `examples/demo/run_demo.py` 内部也是按这个行为生成并保留产物。

### 一键回放统一 Demo

```bash
uv run python examples/demo/run_demo.py
```

写到自定义目录：

```bash
uv run python examples/demo/run_demo.py --output-root /tmp/content-review-demo
```

### Python API 演示入口

如果你要对照代码入口而不是直接跑 CLI，统一 Demo 复用的是：

```python
from content_review_engine.api import review_batch, review_file
from content_review_engine.llm import LLMProviderConfig
```

对应实现文件：

- `examples/demo/run_demo.py`
- `src/content_review_engine/api.py`

### MCP 演示入口

统一 Demo 的 MCP 回放依赖本地 stdio server，对应入口：

```bash
uv run content-review-mcp
```

或：

```bash
uv run python -m content_review_engine.mcp_server
```

### 用新加入文章Agent 上下文管理（公众号优化稿）测试当前审计效果

如果你要直接拿新加入的这篇文章做单文件测试，推荐先用
`profiles/examples/wechat-article.yaml`，因为它除了基础规则，还包含更贴近公众号场景的
`regex_rules`。

先校验 profile：

```bash
uv run content-review profile validate profiles/examples/wechat-article.yaml
```

最短测试命令：

```bash
uv run content-review review \
  'Agent 上下文管理（公众号优化稿）.md' \
  --profile profiles/examples/wechat-article.yaml
```

看结构化 JSON 输出：

```bash
uv run content-review review \
  'Agent 上下文管理（公众号优化稿）.md' \
  --profile profiles/examples/wechat-article.yaml \
  --format json
```

生成可读性更好的 Markdown 报告：

```bash
uv run content-review review \
  'Agent 上下文管理（公众号优化稿）.md' \
  --profile profiles/examples/wechat-article.yaml \
  --format markdown \
  --output /tmp/agent-context-review.md
```

如果你想对比更严格但规则面不同的模板，也可以再跑一次：

```bash
uv run content-review review \
  'Agent 上下文管理（公众号优化稿）.md' \
  --profile profiles/examples/wechat-strict.yaml
```

如果你还想顺手看本地 mock LLM 的辅助层产物：

```bash
uv run content-review review \
  'Agent 上下文管理（公众号优化稿）.md' \
  --profile profiles/examples/wechat-article.yaml \
  --enable-llm \
  --llm-provider mock \
  --llm-output /tmp/agent-context.llm.json \
  --llm-report /tmp/agent-context.llm.md \
  --combined-output /tmp/agent-context.combined.md \
  --combined-output-format markdown
```

说明：

- deterministic 输出仍然是主审计结果。
- `mock` LLM 只适合看产物格式和接线路径，不代表真实语义审计能力。
- 这篇文章的结果会明显受所选 profile 影响。

## 5. 推荐查看顺序

1. 先看 CLI 的 deterministic 报告：
   `examples/demo/artifacts/cli/single-file/review.md`
2. 再看 combined 报告，理解 deterministic 和 LLM 的边界：
   `examples/demo/artifacts/cli/single-file/combined.md`
3. 再看 Python API 的 workflow JSON：
   `examples/demo/artifacts/api/single-file.workflow.json`
4. 最后看 MCP 请求和响应快照：
   `examples/demo/artifacts/mcp/single-file.request.json`
   `examples/demo/artifacts/mcp/single-file.response.json`

## 6. 说明

- 这个统一 Demo 默认使用本地 `mock` LLM 路径。
- 不需要真实 API Key。
- 不依赖 `.env` 自动加载。
- deterministic 输出仍然是主审计结果。
