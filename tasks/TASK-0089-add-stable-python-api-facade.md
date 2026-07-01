# TASK-0089: Add Stable Python API Facade for Review Workflows

## 1. 背景

当前项目已经完成 LLM mainline integration 阶段，并通过 TASK-0088 补齐了真实 LLM provider 的本地 smoke 使用路径。

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
23. 真实 LLM provider 本地 smoke 使用文档和示例。

现在项目已经进入下一阶段：

> 将当前 CLI 中已经稳定的 review workflow 抽象为可复用的 Python API facade，为后续 MCP Server、REST API、GUI、桌面端调用做准备。

当前 CLI 已经具备较完整能力，但后续 MCP / REST / GUI 不应该直接调用 CLI 命令，也不应该复制 CLI 内部逻辑。

因此，本任务需要新增一个稳定、轻量、结构化的 Python API facade，让外部 Python 调用者可以通过函数或配置对象调用现有审计能力。

本任务不是新增 MCP Server，也不是新增 REST API，而是在它们之前抽出一层稳定的程序化调用入口。

---

## 2. 任务目标

本任务目标是：

> 新增一个稳定的 Python API facade，用于以 Python 代码方式调用 single-file / batch review workflow，并复用现有 deterministic review、optional LLM review、raw sidecar、combined envelope、quality gate 相关能力。

完成后应达到：

1. 提供清晰的 Python API 入口；
2. 支持 single-file deterministic review；
3. 支持 batch deterministic review；
4. 支持 optional LLM review；
5. 支持 raw LLM sidecar 结果在 API 层返回；
6. 支持 combined envelope 在 API 层返回；
7. 支持 deterministic quality gate 结果在 API 层返回；
8. 支持 LLM quality gate 结果在 API 层返回；
9. 支持不写文件、只返回结构化 Python 对象；
10. 支持可选写出 deterministic output / LLM sidecar / combined output；
11. 复用现有 CLI 底层逻辑或抽出的 workflow helper；
12. 避免把 CLI 参数解析逻辑暴露为 API；
13. 为后续 MCP / REST API 提供稳定调用基础；
14. 保持已有 CLI 行为不变；
15. 保持 deterministic / LLM / combined / gate 契约不变。

---

## 3. 本任务允许做什么

本任务允许完成以下内容：

1. 新增 Python API facade 模块；
2. 新增 API options / config 数据结构；
3. 新增 API result 数据结构；
4. 新增 single-file review API；
5. 新增 batch review API；
6. 在必要时从 CLI 中抽取可复用 workflow helper；
7. 让 CLI 复用新的 workflow helper；
8. 保持 CLI 外部行为不变；
9. 支持 deterministic-only API 调用；
10. 支持 `enable_llm=False` 默认行为；
11. 支持 `enable_llm=True` 时调用现有 LLM runner / provider factory；
12. 支持传入 LLM provider 配置；
13. 支持返回 raw LLM sidecar result；
14. 支持返回 combined envelope；
15. 支持返回 quality gate metadata；
16. 支持可选输出 JSON / Markdown 文件；
17. 新增 API 文档；
18. 新增 API 使用示例；
19. 新增或更新测试；
20. 更新 `PROJECT_STATE.md`；
21. 更新 `CHANGELOG.md`；
22. 根据需要更新 `docs/ARCHITECTURE.md`；
23. 根据需要更新 `docs/DATA_MODELS.md`。

---

## 4. 本任务不允许做什么

本任务不允许完成以下内容：

1. 不允许新增 MCP Server；
2. 不允许新增 REST API；
3. 不允许新增 Web 前端；
4. 不允许新增 Tauri / desktop client；
5. 不允许新增 Supabase 集成；
6. 不允许新增用户系统；
7. 不允许新增支付系统；
8. 不允许新增数据库；
9. 不允许新增队列系统；
10. 不允许新增异步任务系统；
11. 不允许新增新的真实 LLM provider；
12. 不允许扩展 openai / anthropic 等 reserved provider；
13. 不允许改变当前 pydanticai provider 契约；
14. 不允许改变 `--output` deterministic-only 语义；
15. 不允许改变 `--llm-output` raw sidecar schema；
16. 不允许改变 `--combined-output` explicit opt-in 语义；
17. 不允许让 `--combined-output` 自动启用 LLM；
18. 不允许让 `--llm-fail-on` 自动启用 LLM；
19. 不允许让 LLM findings 默认影响 exit code；
20. 不允许让 LLM findings 进入 deterministic `ReviewResult.findings`；
21. 不允许让 LLM findings 进入 deterministic `severity_counts`；
22. 不允许让 LLM findings 进入 deterministic `rule_counts`；
23. 不允许把 CLI 作为 subprocess 从 Python API 中调用；
24. 不允许把 Typer / argparse 命令对象作为正式 Python API；
25. 不允许引入真实 API Key；
26. 不允许让默认测试依赖真实外部 LLM API；
27. 不允许大规模重写现有 CLI。

---

## 5. 需要修改的文件

预计新增：

```text id="r4gefi"
src/content_review_engine/api.py
tests/test_python_api.py
docs/PYTHON_API.md
examples/python_api_usage/README.md
examples/python_api_usage/single_file_review.py
examples/python_api_usage/batch_review.py
```

根据实际仓库结构，也可以新增更清晰的包结构，例如：

```text id="a7q7g2"
src/content_review_engine/workflows/
src/content_review_engine/workflows/review.py
src/content_review_engine/workflows/models.py
```

如果为了避免 `api.py` 过大，可以采用：

```text id="2kfmp7"
src/content_review_engine/api/__init__.py
src/content_review_engine/api/models.py
src/content_review_engine/api/review.py
```

但本任务应保持小步，不要设计过重框架。

预计可能修改：

```text id="ymswkk"
src/content_review_engine/cli.py
src/content_review_engine/__init__.py
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
docs/CLI.md
docs/LLM_PROVIDER_USAGE.md
PROJECT_STATE.md
CHANGELOG.md
```

如已有相关测试需要复用或更新，可修改：

```text id="9j0z1w"
tests/test_cli.py
tests/test_llm_single_file_cli_integration.py
tests/test_llm_batch_cli_integration.py
tests/test_llm_provider_usage_docs.py
tests/test_llm_combined_output_docs.py
```

具体文件名以当前仓库实际结构为准。

---

## 6. API 设计要求

### 6.1 API 层定位

Python API facade 应定位为：

> 面向外部 Python 调用者的稳定入口，而不是 CLI 参数解析层的简单搬运。

它应该隐藏 CLI 细节，让调用者可以通过 Python 对象和函数调用审计能力。

禁止出现：

```python id="2qbwah"
subprocess.run(["content-review", ...])
```

也不应该要求调用者构造 CLI 参数字符串。

---

### 6.2 推荐 API 入口

建议至少提供两个主入口：

```python id="n42yai"
review_file(...)
review_batch(...)
```

例如：

```python id="zbakbz"
from content_review_engine.api import review_file, review_batch
```

其中：

```python id="cow8d9"
review_file(...)
```

用于审计单个 Markdown / text 文件。

```python id="i52d20"
review_batch(...)
```

用于审计一个目录中的多个 Markdown 文件。

具体函数签名由 Agent 根据现有代码结构设计，但必须满足：

1. 支持传入 input path；
2. 支持传入 profile path；
3. 支持 deterministic-only 默认调用；
4. 支持 optional LLM；
5. 支持 LLM provider config；
6. 支持 fail-on；
7. 支持 llm-fail-on；
8. 支持 combined result；
9. 支持可选 output path；
10. 支持可选 llm output path；
11. 支持可选 combined output path；
12. 返回结构化 Python result object。

---

### 6.3 推荐 Options 数据结构

建议新增轻量 options 数据结构，例如：

```python id="9jw3lr"
ReviewWorkflowOptions
BatchReviewWorkflowOptions
LLMWorkflowOptions
OutputWorkflowOptions
```

也可以使用更简单的设计，例如：

```python id="d09tbl"
ReviewOptions
BatchReviewOptions
LLMOptions
OutputOptions
```

不要过度设计。

这些 options 应尽量使用标准库 dataclass 或当前项目已有模型风格。

如果项目已经主要使用 Pydantic model，则可以沿用现有风格。

Options 至少应覆盖：

```text id="d3sm5u"
profile_path
enable_llm
llm_provider
llm_model
llm_api_key_env
llm_base_url
llm_config_path
fail_on
llm_fail_on
output_path
output_format
llm_output_path
combined_output_path
combined_output_format
recursive
pattern
```

注意：

1. API 层不要直接暴露过多 CLI 命名细节；
2. 但需要能覆盖现有 CLI workflow；
3. `enable_llm` 默认必须是 `False`；
4. `combined_output_path` 不应自动启用 LLM；
5. `llm_fail_on` 不应自动启用 LLM。

---

### 6.4 推荐 Result 数据结构

建议新增结构化结果，例如：

```python id="68orjo"
ReviewWorkflowResult
BatchReviewWorkflowResult
```

结果对象至少应包含：

```text id="o5aohg"
deterministic_result
llm_result
combined_result
deterministic_gate_result
llm_gate_result
exit_code
written_outputs
```

其中：

1. `deterministic_result` 应为现有 ReviewResult / BatchReviewResult；
2. `llm_result` 应为现有 LLMReviewResult / batch LLM sidecar 结构；
3. `combined_result` 应为现有 combined envelope；
4. `deterministic_gate_result` 应复用现有 gate 逻辑；
5. `llm_gate_result` 应复用现有 LLM gate 逻辑；
6. `exit_code` 应与 CLI 对应场景一致；
7. `written_outputs` 应记录 API 调用写出的文件路径。

如果当前项目已经有类似类型，应优先复用，不要重复定义。

---

### 6.5 Single-file API 行为要求

`review_file` 必须支持：

1. deterministic-only 默认路径；
2. optional LLM 路径；
3. raw LLM result 返回；
4. combined envelope 返回；
5. deterministic output 可选写出；
6. raw LLM sidecar 可选写出；
7. combined output 可选写出；
8. deterministic fail-on；
9. LLM fail-on；
10. 与 CLI 一致的 exit code 语义。

必须保持：

1. `enable_llm=False` 时不调用 LLM；
2. 未传入 LLM output path 时不写 raw LLM sidecar；
3. 未传入 combined output path 时不写 combined output；
4. 传入 combined output path 不自动启用 LLM；
5. 传入 llm_fail_on 不自动启用 LLM；
6. LLM findings 不进入 deterministic result；
7. LLM findings 默认不影响 exit code。

---

### 6.6 Batch API 行为要求

`review_batch` 必须支持：

1. input directory；
2. profile path；
3. recursive；
4. pattern；
5. deterministic-only 默认路径；
6. optional LLM；
7. raw batch LLM sidecar result 返回；
8. combined batch envelope 返回；
9. deterministic output 可选写出；
10. raw LLM sidecar 可选写出；
11. combined output 可选写出；
12. deterministic fail-on；
13. LLM fail-on；
14. 与 CLI 一致的 exit code 语义。

必须保持：

1. batch 文件发现行为与 CLI 一致；
2. batch deterministic result 与 CLI 一致；
3. batch LLM sidecar 结构与 CLI 一致；
4. batch combined envelope 与 CLI 一致；
5. batch combined Markdown / JSON 输出与 CLI 一致；
6. batch LLM gate 行为与 CLI 一致。

---

### 6.7 CLI 复用要求

如果当前 CLI 中已经有大量 workflow 逻辑，本任务允许最小抽取，让 CLI 与 Python API 共用同一套底层函数。

但要求：

1. CLI 外部行为不能变化；
2. CLI 参数名不能变化；
3. CLI 输出格式不能变化；
4. CLI exit code 不能变化；
5. CLI 测试必须继续通过；
6. 不要为了 API 大改 CLI；
7. 不要让 API 依赖 Typer / Click / argparse 对象；
8. CLI 应作为一层薄适配器调用 workflow，而不是被 API 反向调用。

---

### 6.8 Output 写出要求

Python API 应支持两种使用方式：

第一种，只返回对象，不写文件：

```python id="k8oxuj"
result = review_file(...)
```

第二种，返回对象并可选写文件：

```python id="g3k6fm"
result = review_file(
    ...,
    output_path="review.json",
    llm_output_path="review.llm.json",
    combined_output_path="review.combined.md",
)
```

写出行为必须与 CLI 保持一致：

```text id="f6ure1"
output_path -> deterministic output
llm_output_path -> raw LLM sidecar
combined_output_path -> combined output
```

不要引入新的隐式行为。

---

### 6.9 LLM 配置要求

Python API 必须支持当前已经稳定的真实 LLM provider 配置方式。

至少应支持：

```text id="vx7d7o"
llm_provider="pydanticai"
llm_model="openai:gpt-4o-mini"
llm_api_key_env="OPENAI_API_KEY"
llm_base_url=None
llm_config_path=None
```

也应支持 mock / test model 路径，以便测试不依赖真实外部 API。

必须保持：

1. 不支持原始 API key 直接传入；
2. 不自动读取 `.env`；
3. 不支持专门的 model 环境变量；
4. 不支持在 review profile 中配置 model；
5. 缺失 model 时应有明确错误；
6. 缺失 API key env 时应有明确错误；
7. 默认测试不调用真实 API。

---

## 7. 测试要求

必须新增或更新测试。

### 7.1 API deterministic single-file 测试

覆盖：

1. `review_file` 可以完成 deterministic-only review；
2. 返回现有 ReviewResult；
3. 不启用 LLM 时不会调用 LLM provider；
4. deterministic findings 与 CLI 对应场景一致；
5. 可选 deterministic output 写出正常。

---

### 7.2 API deterministic batch 测试

覆盖：

1. `review_batch` 可以完成 deterministic-only batch review；
2. 文件发现行为与 CLI 一致；
3. 返回现有 BatchReviewResult；
4. 不启用 LLM 时不会调用 LLM provider；
5. 可选 deterministic output 写出正常。

---

### 7.3 API LLM single-file 测试

覆盖：

1. `review_file(enable_llm=True)` 可以使用 mock / test provider；
2. 返回 raw LLM result；
3. raw LLM sidecar 可选写出；
4. combined result 可选返回；
5. combined output 可选写出；
6. LLM findings 不进入 deterministic result；
7. LLM findings 默认不影响 exit code；
8. `llm_fail_on` 显式传入后才影响 exit code。

---

### 7.4 API LLM batch 测试

覆盖：

1. `review_batch(enable_llm=True)` 可以使用 mock / test provider；
2. 返回 batch raw LLM result；
3. raw batch LLM sidecar 可选写出；
4. combined batch result 可选返回；
5. combined batch output 可选写出；
6. batch LLM findings 不进入 deterministic result；
7. batch LLM findings 默认不影响 exit code；
8. `llm_fail_on` 显式传入后才影响 exit code。

---

### 7.5 API output contract 测试

覆盖：

1. `output_path` 只写 deterministic output；
2. `llm_output_path` 只写 raw LLM sidecar；
3. `combined_output_path` 只写 combined output；
4. `combined_output_path` 不自动启用 LLM；
5. `llm_fail_on` 不自动启用 LLM；
6. raw LLM sidecar schema 不被 gate metadata 污染；
7. combined result 可以包含 LLM gate metadata。

---

### 7.6 API 与 CLI 行为一致性测试

至少覆盖几个关键场景：

1. single-file deterministic API result 与 CLI JSON output 等价；
2. batch deterministic API result 与 CLI JSON output 等价；
3. single-file combined API output 与 CLI combined output 等价；
4. batch combined API output 与 CLI combined output 等价；
5. API exit code 与 CLI exit code 对齐。

不要求覆盖全部 CLI 参数组合，但必须覆盖主路径。

---

### 7.7 API docs 测试

如项目已有 docs consistency tests，应新增或更新测试，确认：

1. `docs/PYTHON_API.md` 存在；
2. 文档包含 `review_file`；
3. 文档包含 `review_batch`；
4. 文档说明 `enable_llm=False` 是默认行为；
5. 文档说明 API 不接受原始 API key；
6. 文档说明 `.env` 不会自动读取；
7. 文档说明 Python API 是后续 MCP / REST / GUI 的基础；
8. 示例文件存在并可被静态检查。

---

## 8. 文档更新要求

必须新增：

```text id="s67dk9"
docs/PYTHON_API.md
```

该文档至少包含：

1. Python API facade 的定位；
2. 与 CLI 的关系；
3. 为什么 MCP / REST / GUI 应复用 Python API；
4. `review_file` 用法；
5. `review_batch` 用法；
6. deterministic-only 示例；
7. optional LLM 示例；
8. raw LLM sidecar 示例；
9. combined output 示例；
10. quality gate 示例；
11. LLM 配置说明；
12. 不支持原始 API key 直接传入；
13. 不自动读取 `.env`；
14. 不调用真实 LLM 的测试建议；
15. 与 CLI 输出语义一致性的说明。

必须更新：

```text id="9u4qqd"
PROJECT_STATE.md
CHANGELOG.md
```

根据实际实现更新：

```text id="k7r268"
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
docs/CLI.md
docs/LLM_PROVIDER_USAGE.md
```

如果新增 examples，必须新增或更新：

```text id="bwb99b"
examples/python_api_usage/README.md
```

---

## 9. 验收标准

完成后应满足：

1. 存在稳定 Python API facade；
2. 可以通过 Python 调用 single-file deterministic review；
3. 可以通过 Python 调用 batch deterministic review；
4. 可以通过 Python 调用 optional LLM review；
5. API 不调用 CLI subprocess；
6. API 不依赖 CLI 参数解析对象；
7. CLI 外部行为保持不变；
8. deterministic output 语义保持不变；
9. raw LLM sidecar schema 保持不变；
10. combined output explicit opt-in 语义保持不变；
11. `combined_output_path` 不自动启用 LLM；
12. `llm_fail_on` 不自动启用 LLM；
13. LLM findings 默认不影响 exit code；
14. LLM findings 不进入 deterministic result；
15. API 支持返回结构化 result object；
16. API 支持可选写出 output 文件；
17. API docs 完整；
18. API examples 存在；
19. 测试覆盖 single-file / batch / LLM / combined / gate 主路径；
20. `uv run pytest` 全量通过；
21. `PROJECT_STATE.md` 准确记录当前阶段；
22. `CHANGELOG.md` 记录本次变更；
23. 未新增 MCP / REST / GUI / Supabase / user system。

---

## 10. 风险与注意事项

本任务最容易出现的风险：

1. 把 CLI 参数解析层直接当成 Python API；
2. API 内部通过 subprocess 调 CLI；
3. 为了 API 大改 CLI 行为；
4. 让 API 和 CLI 分叉实现两套 workflow；
5. 让 MCP / REST / GUI 提前混入本任务；
6. 过度设计 options / result 类型；
7. 重新定义已有 ReviewResult / BatchReviewResult / LLMReviewResult；
8. 让 raw LLM sidecar schema 被 gate metadata 污染；
9. 让 combined output 自动启用 LLM；
10. 让 llm_fail_on 自动启用 LLM；
11. 让 LLM findings 默认影响 exit code；
12. 让真实 API 调用进入默认测试；
13. 暴露原始 API key 参数；
14. 自动读取 `.env`，导致行为不透明；
15. 文档写了 API 但测试没覆盖；
16. examples 使用了当前 API 不支持的参数。

本任务应保持“小而稳定”的 API facade，不追求一次性解决所有产品接口问题。

---

## 11. 完成后需要运行的命令

至少运行：

```bash id="r4kmm5"
uv run pytest
```

如果新增或修改相关测试，应额外运行：

```bash id="kblb66"
uv run pytest tests/test_python_api.py
uv run pytest tests/test_cli.py
uv run pytest tests/test_llm_single_file_cli_integration.py
uv run pytest tests/test_llm_batch_cli_integration.py
uv run pytest tests/test_llm_combined_output_docs.py
```

如果项目已有 lint / type check 命令，也应根据仓库规则运行。

默认验证不得依赖真实外部 LLM API。

---

