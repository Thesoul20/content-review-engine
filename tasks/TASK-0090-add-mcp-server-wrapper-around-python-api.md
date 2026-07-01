# TASK-0090: Add MCP Server Wrapper Around Python API

## 1. 背景

当前项目已经完成 TASK-0089，新增了稳定的 Python API facade。

截至目前，项目已经具备：

1. deterministic review 主线；
2. Markdown 文件读取；
3. ReviewProfile 加载；
4. 单文件 deterministic review；
5. batch deterministic review；
6. JSON / Markdown 报告输出；
7. deterministic quality gate；
8. LLM provider boundary；
9. mock reviewer；
10. LLM runner；
11. secret resolver；
12. provider config / factory；
13. PydanticAI 真实 provider 路径；
14. `content-review llm-check`；
15. single-file / batch `--enable-llm`；
16. single-file / batch `--llm-output` raw sidecar；
17. explicit `--combined-output`；
18. combined envelope builder；
19. combined Markdown report renderer；
20. explicit opt-in `--llm-fail-on`；
21. combined envelope 中的 `llm.quality_gate` metadata；
22. combined Markdown report 中的 LLM gate result 展示；
23. 真实 LLM provider 本地 smoke 使用文档和示例；
24. Python API facade：`review_file(...)` / `review_batch(...)`；
25. shared workflow helper：CLI 与 Python API 复用同一套 workflow orchestration。

现在项目可以进入下一阶段：

> 在稳定 Python API 之上新增 MCP Server wrapper，让 Codex、Claude Code、Cursor、ChatGPT 等支持 MCP 的 Agent 可以调用本项目的内容审计能力。

本任务不是重新实现审计逻辑，也不是新增 REST API / GUI / SaaS，而是将当前已经稳定的 Python API 暴露为 MCP tools。

核心原则：

> MCP Server 只做薄包装层，必须调用 `content_review_engine.api.review_file(...)` 和 `content_review_engine.api.review_batch(...)`，不得复制 CLI 或 workflow 内部逻辑。

---

## 2. 任务目标

本任务目标是：

> 新增一个最小可用、可测试、可文档化的 MCP Server wrapper，将已有 Python API 暴露为 MCP tools，支持 Agent 通过 MCP 调用 single-file / batch 内容审计。

完成后应达到：

1. 新增 MCP Server 入口；
2. MCP tools 基于 Python API 实现；
3. 支持单文件审计 MCP tool；
4. 支持批量审计 MCP tool；
5. 默认 deterministic-only；
6. 支持 optional LLM；
7. 支持 deterministic quality gate；
8. 支持 LLM quality gate；
9. 支持返回结构化 JSON-compatible result；
10. 支持可选写出 deterministic / LLM sidecar / combined output；
11. 不通过 subprocess 调用 CLI；
12. 不复制 CLI 参数解析逻辑；
13. 不复制 workflow orchestration；
14. 不改变 CLI 行为；
15. 不改变 Python API 行为；
16. 不改变 deterministic / LLM / combined / gate 契约；
17. 提供 MCP 使用文档；
18. 提供本地启动示例；
19. 提供 Codex / Claude Code 等客户端配置示例；
20. 新增测试覆盖 MCP tool 到 Python API 的调用路径。

---

## 3. 本任务允许做什么

本任务允许完成以下内容：

1. 新增 MCP Server 模块；
2. 新增 MCP tools；
3. 新增 MCP server 入口函数；
4. 新增 MCP server CLI 启动入口或 console script；
5. 新增 MCP tool input schema；
6. 新增 MCP tool output schema；
7. MCP tool 调用 `review_file(...)`；
8. MCP tool 调用 `review_batch(...)`；
9. 支持 deterministic-only MCP 调用；
10. 支持 optional LLM MCP 调用；
11. 支持 LLM provider config 通过 tool input 传入；
12. 支持 fail-on / llm-fail-on；
13. 支持 output_path / llm_output_path / combined_output_path；
14. 支持 combined output format；
15. 返回 JSON-compatible structured result；
16. 新增 MCP 文档；
17. 新增 MCP 使用示例；
18. 新增 MCP client 配置示例；
19. 新增或更新测试；
20. 更新 `PROJECT_STATE.md`；
21. 更新 `CHANGELOG.md`；
22. 根据需要更新 `docs/ARCHITECTURE.md`；
23. 根据需要更新 `docs/DATA_MODELS.md`；
24. 根据需要更新 `docs/PYTHON_API.md`；
25. 根据需要更新 `docs/CLI.md` 或 `docs/CI.md`。

---

## 4. 本任务不允许做什么

本任务不允许完成以下内容：

1. 不允许新增 REST API；
2. 不允许新增 Web 前端；
3. 不允许新增 Tauri / desktop client；
4. 不允许新增 Supabase 集成；
5. 不允许新增用户系统；
6. 不允许新增支付系统；
7. 不允许新增数据库；
8. 不允许新增队列系统；
9. 不允许新增异步任务系统；
10. 不允许新增 SaaS 多租户能力；
11. 不允许新增审计历史存储；
12. 不允许新增权限系统；
13. 不允许新增新的真实 LLM provider；
14. 不允许实现 openai / anthropic 等 reserved provider；
15. 不允许改变当前 pydanticai provider 契约；
16. 不允许改变 Python API 函数签名，除非是非常小的兼容性修正；
17. 不允许改变 CLI 参数；
18. 不允许改变 CLI 输出；
19. 不允许改变 CLI exit code；
20. 不允许改变 deterministic output schema；
21. 不允许改变 raw LLM sidecar schema；
22. 不允许改变 combined output schema；
23. 不允许让 combined output 自动启用 LLM；
24. 不允许让 llm_fail_on 自动启用 LLM；
25. 不允许让 LLM findings 默认影响 exit code；
26. 不允许让 LLM findings 进入 deterministic `ReviewResult.findings`；
27. 不允许让 LLM findings 进入 deterministic `severity_counts`；
28. 不允许让 LLM findings 进入 deterministic `rule_counts`；
29. 不允许 MCP Server 通过 subprocess 调 CLI；
30. 不允许 MCP Server 直接调用 reader / loader / runner / report 底层模块绕过 Python API；
31. 不允许 MCP Server 复制 `workflows.py` 中的 orchestration；
32. 不允许默认测试依赖真实外部 LLM API；
33. 不允许提交真实 API Key；
34. 不允许自动读取 `.env`；
35. 不允许把原始 API key 作为 MCP tool input。

---

## 5. 需要修改的文件

预计新增：

```text
src/content_review_engine/mcp_server.py
tests/test_mcp_server.py
docs/MCP_SERVER.md
examples/mcp_server/README.md
examples/mcp_server/codex-config.example.json
examples/mcp_server/claude-desktop-config.example.json
```

如果项目更适合包结构，也可以新增：

```text
src/content_review_engine/mcp/__init__.py
src/content_review_engine/mcp/server.py
src/content_review_engine/mcp/tools.py
src/content_review_engine/mcp/models.py
```

二者择一即可，不要过度拆分。

预计可能修改：

```text
pyproject.toml
src/content_review_engine/__init__.py
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
docs/PYTHON_API.md
docs/CLI.md
docs/CI.md
PROJECT_STATE.md
CHANGELOG.md
```

如果项目已有 docs consistency tests，可能新增或修改：

```text
tests/test_mcp_server_docs.py
tests/test_python_api.py
tests/test_cli.py
```

具体文件名以当前仓库实际结构为准。

---

## 6. 实现要求

### 6.1 MCP 层定位

MCP Server 应定位为：

> Python API facade 之上的薄包装层。

推荐架构：

```text
core review engine
        ↓
workflows.py
        ↓
api.py / api_models.py
        ↓
mcp_server.py
        ↓
Codex / Claude Code / Cursor / ChatGPT / other MCP clients
```

MCP Server 不应该直接接触底层审计实现。

允许：

```python
from content_review_engine.api import review_file, review_batch
```

禁止：

```python
subprocess.run(["content-review", ...])
```

禁止绕过 Python API 直接拼装 reader、loader、runner、serializer、report、gate、LLM runner。

---

### 6.2 MCP Tools 设计

本任务至少新增两个 MCP tools：

```text
content_review_file
content_review_batch
```

也可以采用更短名称：

```text
review_file
review_batch
```

但文档中必须说明 tool 名称。

建议 tool 名称带项目语义，避免与其他 MCP server 冲突：

```text
content_review_file
content_review_batch
```

#### Tool 1: `content_review_file`

用于审计单个 Markdown / text 文件。

输入至少支持：

```text
input_path
profile_path
enable_llm
llm_provider
llm_model
llm_api_key_env
llm_base_url
llm_config_path
fail_on
llm_fail_on
include_combined_result
output_path
output_format
llm_output_path
combined_output_path
combined_output_format
```

其中：

1. `input_path` 必填；
2. `profile_path` 必填；
3. `enable_llm` 默认 `false`；
4. `include_combined_result` 默认 `false`；
5. `output_path` 可选；
6. `llm_output_path` 可选；
7. `combined_output_path` 可选；
8. `combined_output_path` 不自动启用 LLM；
9. `llm_fail_on` 不自动启用 LLM。

#### Tool 2: `content_review_batch`

用于审计目录。

输入至少支持：

```text
input_dir
profile_path
recursive
pattern
enable_llm
llm_provider
llm_model
llm_api_key_env
llm_base_url
llm_config_path
fail_on
llm_fail_on
include_combined_result
output_path
output_format
llm_output_path
combined_output_path
combined_output_format
```

其中：

1. `input_dir` 必填；
2. `profile_path` 必填；
3. `recursive` 默认 `false`；
4. `pattern` 默认应与 Python API / CLI 保持一致；
5. `enable_llm` 默认 `false`；
6. `include_combined_result` 默认 `false`。

---

### 6.3 MCP Output 设计

MCP tools 必须返回 JSON-compatible 结构。

不要只返回自然语言字符串。

返回内容至少应包含：

```text
ok
exit_code
deterministic
llm
combined
quality_gate
artifacts
errors
```

推荐结构：

```json
{
  "ok": true,
  "exit_code": 0,
  "deterministic": {
    "schema_version": "...",
    "summary": {},
    "findings": []
  },
  "llm": null,
  "combined": null,
  "quality_gate": {
    "deterministic": {},
    "llm": null
  },
  "artifacts": {
    "output_path": null,
    "llm_output_path": null,
    "combined_output_path": null
  },
  "errors": []
}
```

注意：

1. `deterministic` 应来自现有 ReviewResult / BatchReviewResult 序列化；
2. `llm` 应来自现有 LLM sidecar 结构；
3. `combined` 应来自现有 combined envelope；
4. `quality_gate.deterministic` 应来自 deterministic gate；
5. `quality_gate.llm` 应来自 LLM gate；
6. `artifacts` 应记录实际写出的文件；
7. 如果发生错误，应返回结构化 error，或按照 MCP 框架推荐方式抛出 tool error；
8. 不要把 Python 对象直接返回给 MCP client；
9. 不要返回不可 JSON 序列化对象。

---

### 6.4 错误处理要求

MCP tools 应提供清晰错误信息。

至少覆盖：

1. input file 不存在；
2. input dir 不存在；
3. profile file 不存在；
4. profile 加载失败；
5. deterministic review 失败；
6. batch 文件发现失败；
7. LLM provider config 缺失；
8. LLM model 缺失；
9. API key env 缺失；
10. API key env 为空；
11. LLM provider 不支持；
12. LLM response validation failed；
13. output 写出失败；
14. combined output 写出失败。

错误不得泄露 secret。

如果 `llm_api_key_env` 指向的环境变量存在真实 API key，错误信息中只能出现环境变量名，不得出现 secret value。

---

### 6.5 LLM 配置要求

MCP tools 必须继承 TASK-0088 的真实 LLM 使用边界：

1. 支持 `llm_provider="pydanticai"`；
2. 支持 `llm_model="openai:gpt-4o-mini"` 这类 model name；
3. 支持 `llm_api_key_env="OPENAI_API_KEY"`；
4. 支持 `llm_base_url`；
5. 支持 `llm_config_path`；
6. 不支持 raw API key 直接传入；
7. 不自动读取 `.env`；
8. 不支持专门的 model 环境变量；
9. 不支持在 review profile 中配置 model；
10. 缺失 model 时应有明确错误；
11. 缺失 API key env 时应有明确错误；
12. 默认测试不调用真实 API。

---

### 6.6 Dependency / Entry Point 要求

如果项目当前尚未引入 MCP 依赖，本任务允许最小引入 MCP 相关依赖。

但要求：

1. 优先作为 optional dependency；
2. 不应影响默认 deterministic CLI 使用；
3. 不应让普通 `content-review` CLI 依赖 MCP runtime；
4. 不应让默认测试依赖外部 MCP 服务；
5. 如果新增 console script，名称建议清晰，例如：

```text
content-review-mcp
```

也可以采用：

```bash
python -m content_review_engine.mcp_server
```

或：

```bash
uv run content-review mcp
```

但不要为了 MCP 大改现有 CLI。若要新增 `content-review mcp` 子命令，必须保持原 CLI 行为不变。

推荐优先级：

1. 最小 server module；
2. console script；
3. 文档说明如何启动；
4. 暂不强行塞进主 CLI。

---

### 6.7 Transport 要求

本任务优先支持 MCP stdio transport。

也就是适合本地 Agent 客户端启动：

```bash
uv run content-review-mcp
```

或：

```bash
uv run python -m content_review_engine.mcp_server
```

本任务不要求实现 HTTP / SSE / streamable HTTP transport。

不允许在本任务中做远程部署、认证、反向代理、VPS 服务化。

---

### 6.8 安全与路径要求

MCP tools 接收路径参数时，应注意：

1. 文档中必须说明 MCP Server 会在本地机器上读取传入路径；
2. 用户应只传入自己信任的文件路径；
3. 不要默认扫描用户整个磁盘；
4. batch 默认不要 recursive，除非显式传入；
5. 不要自动读取 `.env`；
6. 不要在返回结果中泄露 secret；
7. 不要把审计内容上传到额外服务，除非用户显式启用 LLM provider；
8. 启用真实 LLM 时，文档必须说明内容会被发送给对应 provider。

---

### 6.9 Docs / Examples 要求

新增 `docs/MCP_SERVER.md`。

文档至少包含：

1. MCP Server 定位；
2. 与 CLI / Python API 的关系；
3. MCP tool 列表；
4. `content_review_file` 输入字段；
5. `content_review_file` 输出结构；
6. `content_review_batch` 输入字段；
7. `content_review_batch` 输出结构；
8. deterministic-only 使用示例；
9. optional LLM 使用示例；
10. raw sidecar / combined output 使用说明；
11. quality gate 行为说明；
12. 启动方式；
13. Codex 配置示例；
14. Claude Desktop 配置示例；
15. 安全注意事项；
16. 不支持项；
17. 测试方式；
18. 与后续 REST API / GUI 的关系。

新增 `examples/mcp_server/README.md`。

其中至少提供：

1. 本地启动命令；
2. deterministic single-file tool 调用示例；
3. deterministic batch tool 调用示例；
4. optional LLM tool 调用示例；
5. MCP client config 示例说明。

---

## 7. 测试要求

必须新增或更新测试。

### 7.1 MCP Server 注册测试

覆盖：

1. MCP Server 可以被构建；
2. `content_review_file` tool 已注册；
3. `content_review_batch` tool 已注册；
4. server module 可 import；
5. server entry point 不触发真实 review；
6. import MCP server 不要求真实 API key。

---

### 7.2 MCP single-file deterministic 测试

覆盖：

1. 调用 `content_review_file` 可完成 deterministic-only review；
2. 默认 `enable_llm=False`；
3. 不启用 LLM 时不会调用 LLM provider；
4. 返回 JSON-compatible result；
5. 返回 deterministic summary；
6. 返回 deterministic findings；
7. 返回 deterministic gate result；
8. `exit_code` 与 Python API 对应场景一致。

---

### 7.3 MCP batch deterministic 测试

覆盖：

1. 调用 `content_review_batch` 可完成 deterministic-only batch review；
2. 文件发现行为与 Python API / CLI 一致；
3. 默认 `recursive=False`；
4. 返回 JSON-compatible result；
5. 返回 batch summary；
6. 返回 deterministic gate result；
7. `exit_code` 与 Python API 对应场景一致。

---

### 7.4 MCP optional LLM 测试

使用 mock / test provider，不调用真实外部 API。

覆盖：

1. `content_review_file(enable_llm=True)` 可返回 LLM result；
2. `content_review_batch(enable_llm=True)` 可返回 batch LLM result；
3. LLM findings 不进入 deterministic result；
4. LLM findings 默认不影响 exit code；
5. 显式 `llm_fail_on` 后才影响 exit code；
6. 缺失 model 的错误清晰；
7. 缺失 API key env 的错误清晰；
8. secret value 不出现在错误信息里。

---

### 7.5 MCP output artifact 测试

覆盖：

1. `output_path` 只写 deterministic output；
2. `llm_output_path` 只写 raw LLM sidecar；
3. `combined_output_path` 只写 combined output；
4. `combined_output_path` 不自动启用 LLM；
5. `llm_fail_on` 不自动启用 LLM；
6. raw sidecar schema 不被 gate metadata 污染；
7. combined result 可以包含 LLM gate metadata；
8. artifacts 返回实际写出的路径。

---

### 7.6 MCP 与 Python API 一致性测试

至少覆盖：

1. MCP single-file deterministic result 与 `review_file(...)` 对应结果一致；
2. MCP batch deterministic result 与 `review_batch(...)` 对应结果一致；
3. MCP single-file combined result 与 Python API 对应结果一致；
4. MCP batch combined result 与 Python API 对应结果一致；
5. MCP exit_code 与 Python API 对齐。

---

### 7.7 MCP docs 测试

如项目已有 docs consistency tests，应新增或更新测试，确认：

1. `docs/MCP_SERVER.md` 存在；
2. 文档包含 `content_review_file`；
3. 文档包含 `content_review_batch`；
4. 文档说明 MCP Server 调用 Python API；
5. 文档说明不通过 subprocess 调 CLI；
6. 文档说明默认 deterministic-only；
7. 文档说明 `combined_output_path` 不自动启用 LLM；
8. 文档说明 `llm_fail_on` 不自动启用 LLM；
9. 文档说明不接受 raw API key；
10. 文档说明不自动读取 `.env`；
11. 文档说明真实 LLM 会把内容发送给 provider；
12. examples/mcp_server 文件存在。

---

## 8. 文档更新要求

必须新增：

```text
docs/MCP_SERVER.md
examples/mcp_server/README.md
```

必须更新：

```text
PROJECT_STATE.md
CHANGELOG.md
```

根据实际实现更新：

```text
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
docs/PYTHON_API.md
docs/CLI.md
docs/CI.md
docs/LLM_PROVIDER_USAGE.md
pyproject.toml
```

文档中必须清楚区分：

```text
CLI
Python API
MCP Server
deterministic review
optional LLM review
raw LLM sidecar
combined output
deterministic quality gate
LLM quality gate
local-only real provider smoke
default CI
```

---

## 9. 验收标准

完成后应满足：

1. 存在 MCP Server wrapper；
2. MCP Server 可以本地启动；
3. MCP Server 暴露 single-file review tool；
4. MCP Server 暴露 batch review tool；
5. MCP tools 调用 Python API；
6. MCP tools 不通过 subprocess 调 CLI；
7. MCP tools 不复制 workflow orchestration；
8. MCP tools 默认 deterministic-only；
9. MCP tools 支持 optional LLM；
10. MCP tools 支持 output_path / llm_output_path / combined_output_path；
11. MCP tools 支持 deterministic gate；
12. MCP tools 支持 LLM gate；
13. MCP tools 返回 JSON-compatible result；
14. MCP output 与 Python API 主路径一致；
15. CLI 行为保持不变；
16. Python API 行为保持不变；
17. deterministic schema 保持不变；
18. raw LLM sidecar schema 保持不变；
19. combined output schema 保持不变；
20. `combined_output_path` 不自动启用 LLM；
21. `llm_fail_on` 不自动启用 LLM；
22. LLM findings 默认不影响 exit code；
23. LLM findings 不进入 deterministic result；
24. 默认测试不依赖真实外部 LLM API；
25. 不提交真实 API Key；
26. 文档完整；
27. examples 存在；
28. `uv run pytest` 全量通过；
29. `PROJECT_STATE.md` 准确记录当前阶段；
30. `CHANGELOG.md` 记录本次变更；
31. 未新增 REST / GUI / Supabase / user system / SaaS 能力。

---

## 10. 风险与注意事项

本任务最容易出现的风险：

1. MCP Server 直接调用 CLI subprocess；
2. MCP Server 复制 Python API / workflow 逻辑；
3. MCP tool 返回自然语言而不是结构化结果；
4. MCP tool 返回不可 JSON 序列化对象；
5. MCP tool 输入字段与 Python API 不一致；
6. MCP tool output 与 Python API schema 漂移；
7. 为了 MCP 大改 CLI；
8. 为了 MCP 大改 Python API；
9. 把 REST API 或 HTTP Server 混入本任务；
10. 把 GUI / Supabase / 用户系统混入本任务；
11. 默认启用 recursive batch 扫描；
12. 默认启用 LLM；
13. `combined_output_path` 隐式启用 LLM；
14. `llm_fail_on` 隐式启用 LLM；
15. LLM findings 默认影响 exit code；
16. 真实 LLM API 进入默认测试；
17. tool input 支持 raw API key；
18. 错误信息泄露 secret；
19. 文档示例使用了当前实现不支持的配置字段；
20. MCP client config 示例中写入真实路径或真实 secret。

本任务应保持“小而稳定”的 MCP wrapper。先让 Agent 能通过 MCP 调用审计能力，后续再考虑更复杂的远程服务化、鉴权、前端或团队协作能力。

---

## 11. 完成后需要运行的命令

至少运行：

```bash
uv run pytest
```

如果新增或修改相关测试，应额外运行：

```bash
uv run pytest tests/test_mcp_server.py
uv run pytest tests/test_python_api.py
uv run pytest tests/test_cli.py
```

如果新增 docs consistency tests，应运行：

```bash
uv run pytest tests/test_mcp_server_docs.py
```

如果项目已有 lint / type check 命令，也应根据仓库规则运行。

默认验证不得依赖真实外部 LLM API。

---
