# TASK-0091: MCP Client Smoke Validation and Packaging Hardening

## 1. 背景

当前项目已经完成 TASK-0090，新增了 MCP Server wrapper。

截至目前，项目已经具备：

1. deterministic review 主线；
2. single-file / batch CLI；
3. deterministic JSON / Markdown report；
4. deterministic quality gate；
5. LLM provider boundary；
6. mock reviewer；
7. LLM runner；
8. secret resolver；
9. provider config / factory；
10. PydanticAI 真实 provider 路径；
11. `content-review llm-check`；
12. single-file / batch `--enable-llm`；
13. single-file / batch `--llm-output` raw sidecar；
14. explicit `--combined-output`；
15. combined envelope builder；
16. combined Markdown report renderer；
17. explicit opt-in `--llm-fail-on`；
18. combined envelope 中的 `llm.quality_gate` metadata；
19. combined Markdown report 中的 LLM gate result 展示；
20. 真实 LLM provider 本地 smoke 使用文档和示例；
21. Python API facade：`review_file(...)` / `review_batch(...)`；
22. shared workflow helper：CLI 与 Python API 复用同一套 workflow orchestration；
23. MCP Server wrapper；
24. `content-review-mcp` console script；
25. `python -m content_review_engine.mcp_server` 模块入口；
26. MCP tools：`content_review_file` / `content_review_batch`；
27. Codex / Claude Desktop MCP client 配置示例。

TASK-0090 已经完成 MCP Server 的主体实现，但在正式进入 REST API / 服务化入口之前，还需要做一次 MCP 实机接入验证与打包收口。

本任务目标不是新增 REST API，也不是继续扩展 MCP 大功能，而是确认：

1. MCP Server 可以被本地客户端稳定启动；
2. console script / module entry point 行为清晰；
3. Codex / Claude Desktop 配置示例可用且安全；
4. MCP 依赖与打包方式不会污染普通 CLI 使用；
5. stdio 是默认推荐路径；
6. SSE / streamable-http 等非主路径能力不会被误写成已产品化能力；
7. MCP docs、examples、tests、project state 一致；
8. MCP tool 输入输出契约与 Python API 保持一致。

---

## 2. 任务目标

本任务目标是：

> 对 MCP Server wrapper 做 client smoke validation、packaging hardening 和 release readiness audit，确保 MCP 入口可以被真实 MCP client 配置、启动、调用，并且不会引入服务化、REST API、远程部署或依赖污染等范围外能力。

完成后应达到：

1. `content-review-mcp` console script 可被验证；
2. `python -m content_review_engine.mcp_server` 可被验证；
3. MCP Server 默认 stdio 行为清晰；
4. Codex 配置示例是合法 JSON；
5. Claude Desktop 配置示例是合法 JSON；
6. 配置示例不包含真实 secret；
7. 配置示例使用占位绝对路径，不写死开发者本机路径；
8. 文档明确 MCP Server 是本地工具入口；
9. 文档明确 stdio 是默认推荐 transport；
10. 文档明确真实 LLM 会把内容发送给 provider；
11. 文档明确 MCP tool 不接受 raw API key；
12. 文档明确不会自动读取 `.env`；
13. 文档明确 batch 默认不递归；
14. 文档明确 output_path / llm_output_path / combined_output_path 的行为；
15. 文档明确 combined_output_path 不自动启用 LLM；
16. 文档明确 llm_fail_on 不自动启用 LLM；
17. MCP package dependency / optional dependency 决策清晰；
18. 普通 CLI 使用不被 MCP runtime 破坏；
19. 默认测试不依赖真实 MCP client；
20. 默认测试不依赖真实外部 LLM API；
21. `PROJECT_STATE.md` 准确记录 MCP 阶段状态；
22. `CHANGELOG.md` 记录本次 MCP 收口。

---

## 3. 本任务允许做什么

本任务允许完成以下内容：

1. 审计 MCP Server 启动入口；
2. 验证 `content-review-mcp` console script；
3. 验证 `python -m content_review_engine.mcp_server` 入口；
4. 补充 MCP Server help / startup 行为测试；
5. 补充 MCP client config 示例测试；
6. 补充 Codex config 示例；
7. 补充 Claude Desktop config 示例；
8. 修正 MCP client config 示例中的路径占位符；
9. 增加 MCP manual smoke checklist；
10. 增加 MCP deterministic-only tool 调用示例；
11. 增加 MCP optional LLM tool 调用示例；
12. 增加 MCP artifact 写出示例；
13. 增加 MCP 错误排查文档；
14. 增加 MCP transport 边界说明；
15. 审计 MCP 依赖是否应为 optional dependency；
16. 在必要时调整 pyproject 中 MCP 依赖声明；
17. 在必要时调整 console script / entry point；
18. 在必要时收窄或解释非 stdio transport；
19. 新增或更新 tests；
20. 更新 `docs/MCP_SERVER.md`；
21. 更新 `examples/mcp_server/README.md`；
22. 更新 `docs/ARCHITECTURE.md`；
23. 更新 `docs/CI.md`；
24. 更新 `docs/PYTHON_API.md`；
25. 更新 `PROJECT_STATE.md`；
26. 更新 `CHANGELOG.md`。

---

## 4. 本任务不允许做什么

本任务不允许完成以下内容：

1. 不允许新增 REST API；
2. 不允许新增 FastAPI / Flask / Django 服务；
3. 不允许新增 Web 前端；
4. 不允许新增 Tauri / desktop client；
5. 不允许新增 Supabase 集成；
6. 不允许新增用户系统；
7. 不允许新增支付系统；
8. 不允许新增数据库；
9. 不允许新增队列系统；
10. 不允许新增异步任务系统；
11. 不允许新增 SaaS 多租户能力；
12. 不允许新增审计历史存储；
13. 不允许新增权限系统；
14. 不允许新增远程部署方案；
15. 不允许新增认证 / token / API key 管理系统；
16. 不允许新增新的真实 LLM provider；
17. 不允许实现 openai / anthropic 等 reserved provider；
18. 不允许改变当前 pydanticai provider 契约；
19. 不允许改变 Python API 函数签名；
20. 不允许改变 CLI 参数；
21. 不允许改变 CLI 输出；
22. 不允许改变 CLI exit code；
23. 不允许改变 MCP tool 名称；
24. 不允许改变 MCP tool 既有 input schema，除非是兼容性补充；
25. 不允许改变 MCP tool output schema；
26. 不允许改变 deterministic output schema；
27. 不允许改变 raw LLM sidecar schema；
28. 不允许改变 combined output schema；
29. 不允许让 combined_output_path 自动启用 LLM；
30. 不允许让 llm_fail_on 自动启用 LLM；
31. 不允许让 LLM findings 默认影响 exit code；
32. 不允许让 LLM findings 进入 deterministic `ReviewResult.findings`；
33. 不允许让 LLM findings 进入 deterministic `severity_counts`；
34. 不允许让 LLM findings 进入 deterministic `rule_counts`；
35. 不允许 MCP Server 通过 subprocess 调 CLI；
36. 不允许 MCP Server 绕过 Python API；
37. 不允许默认测试依赖真实外部 LLM API；
38. 不允许默认测试依赖真实 Codex / Claude Desktop 客户端；
39. 不允许提交真实 API Key；
40. 不允许自动读取 `.env`；
41. 不允许 MCP tool input 支持 raw API key。

---

## 5. 需要修改的文件

预计修改：

```text
pyproject.toml
uv.lock
docs/MCP_SERVER.md
examples/mcp_server/README.md
examples/mcp_server/codex-config.example.json
examples/mcp_server/claude-desktop-config.example.json
docs/ARCHITECTURE.md
docs/CI.md
docs/PYTHON_API.md
PROJECT_STATE.md
CHANGELOG.md
tests/test_mcp_server.py
tests/test_mcp_server_docs.py
```

预计可能新增：

```text
examples/mcp_server/manual-smoke-checklist.md
examples/mcp_server/tool-call-examples/content-review-file-deterministic.json
examples/mcp_server/tool-call-examples/content-review-batch-deterministic.json
examples/mcp_server/tool-call-examples/content-review-file-llm-mock.json
tests/test_mcp_server_packaging.py
```

如当前 `tests/test_mcp_server.py` 已经适合承载 packaging / config tests，也可以不新增测试文件，直接扩展现有测试。

如需要最小改进 MCP Server 启动行为，可能修改：

```text
src/content_review_engine/mcp_server.py
```

但本任务不应重写 MCP Server 主体逻辑。

---

## 6. 实现要求

### 6.1 MCP 启动入口收口

必须确认并测试以下入口：

```bash
uv run content-review-mcp
```

以及：

```bash
uv run python -m content_review_engine.mcp_server
```

测试不应让 stdio server 永久阻塞。

可以通过以下方式之一测试：

1. `--help`；
2. `--version`，如果已有；
3. import / build server；
4. entry point metadata 检查；
5. 短生命周期 smoke helper；
6. 当前 MCP SDK 推荐的测试方式。

如当前缺少安全可测试的 help/version 行为，可以最小补充。

不要为了测试启动行为引入复杂 daemon、HTTP server 或后台进程管理。

---

### 6.2 MCP Transport 边界

本任务必须明确：

1. stdio 是默认推荐 transport；
2. 本地 MCP client 应优先使用 stdio；
3. 远程 HTTP / SSE / streamable-http 不属于当前产品化能力；
4. 如 MCP SDK 暴露了 `sse` 或 `streamable-http`，文档必须说明它们不是本阶段推荐路径；
5. 不新增远程部署说明；
6. 不新增公网服务化示例；
7. 不新增认证 / 权限 / 反向代理说明；
8. 不新增 REST API 语义。

如果当前实现中主动暴露了非 stdio transport，Agent 需要判断：

1. 是否是 MCP SDK 默认能力；
2. 是否会增加维护成本；
3. 是否应在本任务中收窄为 stdio-only；
4. 或者仅在文档中标记为非主路径 / experimental。

保持小步，不要在本任务中产品化 HTTP/SSE。

---

### 6.3 MCP Client Config 示例收口

必须检查并测试：

```text
examples/mcp_server/codex-config.example.json
examples/mcp_server/claude-desktop-config.example.json
```

要求：

1. JSON 语法合法；
2. 不包含真实 API key；
3. 不包含真实用户主目录；
4. 不包含开发者本机绝对路径；
5. 使用明确占位符，例如 `/ABSOLUTE/PATH/TO/content-review-engine`；
6. 命令使用当前项目真实可用的启动方式；
7. 推荐使用 `uv run --directory /ABSOLUTE/PATH/TO/content-review-engine content-review-mcp`；
8. 文档解释用户需要替换绝对路径；
9. 文档解释 Windows / macOS / Linux 路径差异；
10. 文档解释配置后需要重启 MCP client。

---

### 6.4 MCP Tool Call 示例

新增或更新 tool call 示例。

至少提供：

1. deterministic single-file；
2. deterministic batch；
3. optional LLM mock；
4. artifact 写出；
5. combined output。

示例必须使用 JSON-compatible input。

示例中不得包含真实 secret。

示例中不得使用 raw API key 字段。

示例中应使用当前真实字段名，例如：

```json
{
  "markdown_path": "examples/real_llm_usage/single-file-smoke.md",
  "profile_path": "profiles/examples/general-basic.yaml",
  "enable_llm": false,
  "include_combined_result": true
}
```

batch 示例应明确：

```json
{
  "input_dir": "examples/real_llm_usage/batch",
  "profile_path": "profiles/examples/general-basic.yaml",
  "recursive": false,
  "pattern": "*.md"
}
```

---

### 6.5 Manual Smoke Checklist

新增或更新手工验证清单。

建议新增：

```text
examples/mcp_server/manual-smoke-checklist.md
```

内容至少包括：

1. 安装依赖；
2. 本地运行测试；
3. 启动 MCP server；
4. 配置 Codex；
5. 配置 Claude Desktop；
6. deterministic single-file tool 调用；
7. deterministic batch tool 调用；
8. optional LLM mock tool 调用；
9. optional real LLM tool 调用；
10. 常见错误排查；
11. 如何确认没有调用真实 LLM；
12. 如何确认真实 LLM 调用会发送内容给 provider；
13. 如何确认 output artifact 写出；
14. 如何确认 combined_output_path 不自动启用 LLM；
15. 如何确认 llm_fail_on 不自动启用 LLM。

注意：

1. 默认自动测试不需要执行这个 checklist；
2. checklist 可以作为人工 release smoke；
3. 真实 LLM smoke 必须标记为 local manual only；
4. 不要把真实 LLM smoke 放入默认 CI。

---

### 6.6 MCP Packaging / Dependency 收口

需要审计 `pyproject.toml` 中 MCP dependency 的放置方式。

Agent 需要明确判断：

1. MCP 依赖当前是普通 dependency 还是 optional dependency；
2. 是否会影响普通 `content-review` CLI 使用；
3. 是否会显著增加默认安装体积；
4. 是否需要提供 extras，例如：

```text
content-review-engine[mcp]
```

如果当前项目已经接受 MCP 作为核心能力，可以保留普通 dependency，但必须在文档中说明原因。

如果更适合 optional dependency，可以在本任务中最小调整为 optional extras。

无论选择哪种，都必须确保：

1. `content-review` CLI 仍可正常使用；
2. `content-review-mcp` 入口可正常使用；
3. 默认测试通过；
4. 文档说明安装方式；
5. 不引入 dependency conflict。

不要为了 dependency 优化做大规模 packaging 重构。

---

### 6.7 MCP Error Troubleshooting

文档中必须补充常见错误排查。

至少包括：

1. `content-review-mcp` 命令找不到；
2. `uv` 命令找不到；
3. `--directory` 路径错误；
4. MCP client 配置 JSON 格式错误；
5. MCP client 没有重启；
6. `markdown_path` 不存在；
7. `profile_path` 不存在；
8. batch `input_dir` 不存在；
9. LLM model 缺失；
10. API key env 缺失；
11. API key env 为空；
12. 真实 LLM provider 网络错误；
13. output_path 无写权限；
14. combined_output_path 不生成 LLM 内容的原因；
15. llm_fail_on 不生效的原因。

所有错误说明不得泄露 secret。

---

### 6.8 安全说明

文档必须明确：

1. MCP Server 是本地工具入口；
2. MCP client 会让 Agent 读取用户提供的本地路径；
3. 用户应只传入信任的文件路径；
4. batch 默认不递归；
5. 不要传入整个用户目录作为 batch input；
6. 不自动读取 `.env`；
7. 不接受 raw API key；
8. 启用真实 LLM 时，待审计内容会发送给对应 provider；
9. mock provider 不会调用真实外部 API；
10. output artifact 可能包含原文片段和 findings，应注意保存位置；
11. config 示例不得写入真实 secret。

---

## 7. 测试要求

必须新增或更新测试。

### 7.1 MCP Packaging / Entry Point 测试

覆盖：

1. `content-review-mcp` console script 在 pyproject 中存在；
2. module entry point 可 import；
3. MCP server module import 不触发 server 阻塞；
4. MCP server module import 不要求真实 API key；
5. `python -m content_review_engine.mcp_server --help` 或等价方式可测试；
6. 普通 CLI tests 仍然通过。

---

### 7.2 MCP Client Config 示例测试

覆盖：

1. Codex config 示例是合法 JSON；
2. Claude Desktop config 示例是合法 JSON；
3. 示例中包含 `content-review-mcp`；
4. 示例中包含 `/ABSOLUTE/PATH/TO/content-review-engine` 或等价占位路径；
5. 示例中不包含真实用户目录；
6. 示例中不包含真实 API key；
7. 示例中不包含 raw secret；
8. 示例中使用的 command / args 与文档一致。

---

### 7.3 MCP Tool Call 示例测试

覆盖：

1. deterministic single-file 示例存在；
2. deterministic batch 示例存在；
3. optional LLM mock 示例存在；
4. 示例 JSON 合法；
5. 示例字段属于当前 MCP tool 支持字段；
6. 示例不包含 raw API key；
7. 示例不自动启用 LLM，除非显式 `enable_llm=true`；
8. 示例中 `combined_output_path` 不被描述为自动启用 LLM。

---

### 7.4 MCP Docs Consistency 测试

覆盖：

1. `docs/MCP_SERVER.md` 存在；
2. 文档说明 MCP Server 调用 Python API；
3. 文档说明不通过 subprocess 调 CLI；
4. 文档说明 stdio 是默认推荐 transport；
5. 文档说明非 stdio transport 不是本阶段产品化远程服务；
6. 文档说明默认 deterministic-only；
7. 文档说明 batch 默认不递归；
8. 文档说明不接受 raw API key；
9. 文档说明不自动读取 `.env`；
10. 文档说明启用真实 LLM 会发送内容给 provider；
11. 文档说明 combined_output_path 不自动启用 LLM；
12. 文档说明 llm_fail_on 不自动启用 LLM；
13. 文档包含 troubleshooting；
14. 文档包含 Codex 配置；
15. 文档包含 Claude Desktop 配置。

---

### 7.5 MCP Behavior Regression 测试

保留并回归：

1. MCP tool 注册测试；
2. MCP single-file deterministic 测试；
3. MCP batch deterministic 测试；
4. MCP optional LLM mock 测试；
5. MCP artifact output 测试；
6. MCP 与 Python API 一致性测试；
7. MCP 错误脱敏测试。

确保本任务没有破坏 TASK-0090 已有行为。

---

## 8. 文档更新要求

必须更新：

```text
docs/MCP_SERVER.md
examples/mcp_server/README.md
PROJECT_STATE.md
CHANGELOG.md
```

根据实际情况更新：

```text
docs/ARCHITECTURE.md
docs/CI.md
docs/PYTHON_API.md
docs/CLI.md
docs/LLM_PROVIDER_USAGE.md
pyproject.toml
```

如新增示例，必须添加：

```text
examples/mcp_server/manual-smoke-checklist.md
examples/mcp_server/tool-call-examples/
```

文档中必须清楚区分：

```text
CLI
Python API
MCP Server
MCP client config
deterministic-only MCP call
optional LLM MCP call
mock LLM
real LLM
stdio transport
non-stdio transport
manual smoke
default CI
```

---

## 9. 验收标准

完成后应满足：

1. `content-review-mcp` 入口可验证；
2. `python -m content_review_engine.mcp_server` 入口可验证；
3. MCP server import 不阻塞；
4. MCP server import 不要求真实 API key；
5. Codex config 示例合法；
6. Claude Desktop config 示例合法；
7. MCP tool call 示例合法；
8. MCP docs 说明 stdio 是默认推荐路径；
9. MCP docs 没有把 HTTP / SSE 当成已产品化 REST 服务；
10. MCP docs 说明 MCP Server 调用 Python API；
11. MCP docs 说明不通过 subprocess 调 CLI；
12. MCP docs 说明不接受 raw API key；
13. MCP docs 说明不自动读取 `.env`；
14. MCP docs 说明 batch 默认不递归；
15. MCP docs 说明真实 LLM 会发送内容给 provider；
16. MCP docs 包含 troubleshooting；
17. MCP manual smoke checklist 存在；
18. MCP dependency / optional dependency 决策清晰；
19. 普通 CLI 行为保持不变；
20. Python API 行为保持不变；
21. MCP tool 行为保持不变；
22. deterministic schema 保持不变；
23. raw LLM sidecar schema 保持不变；
24. combined output schema 保持不变；
25. `combined_output_path` 不自动启用 LLM；
26. `llm_fail_on` 不自动启用 LLM；
27. 默认测试不依赖真实外部 LLM API；
28. 默认测试不依赖真实 Codex / Claude Desktop；
29. 不提交真实 API Key；
30. `uv run pytest` 全量通过；
31. `PROJECT_STATE.md` 准确记录 MCP 收口状态；
32. `CHANGELOG.md` 记录本次变更；
33. 未新增 REST / GUI / Supabase / user system / SaaS 能力。

---

## 10. 风险与注意事项

本任务最容易出现的风险：

1. 把 MCP client smoke 做成真实 Codex / Claude Desktop 自动化测试；
2. 默认测试依赖本机安装的 Codex / Claude Desktop；
3. 为了验证 MCP 而引入后台进程管理；
4. 把 SSE / streamable-http 包装成 REST API；
5. 开始写远程部署方案；
6. 开始设计认证系统；
7. 开始设计用户系统；
8. 开始设计审计历史数据库；
9. 改动 Python API 签名；
10. 改动 MCP tool schema；
11. 改动 CLI 行为；
12. 把 raw API key 放进 config 示例；
13. 把真实本机路径放进 config 示例；
14. 把 `.env` 自动读取写成支持能力；
15. 文档暗示 mock provider 会调用真实 LLM；
16. 文档没有说明真实 LLM 会把内容发送给 provider；
17. dependency 改动过大，破坏普通 CLI 安装；
18. 只更新文档，不加 config / examples / docs consistency 测试。

本任务应保持为 MCP release readiness hardening，不进入服务化开发。

---

## 11. 完成后需要运行的命令

至少运行：

```bash
uv run pytest
```

如果新增或修改相关测试，应额外运行：

```bash
uv run pytest tests/test_mcp_server.py
uv run pytest tests/test_mcp_server_docs.py
uv run pytest tests/test_mcp_server_packaging.py
uv run pytest tests/test_python_api.py
uv run pytest tests/test_cli.py
```

如果没有新增 `tests/test_mcp_server_packaging.py`，则无需运行该文件。

默认验证不得依赖真实外部 LLM API。

默认验证不得依赖真实 Codex / Claude Desktop 客户端。

---

