# TASK-0088: Real LLM Provider Usage Smoke Test and Documentation

## 1. 背景

当前项目已经完成 LLM mainline integration release readiness audit。

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
10. PydanticAI 测试模型路径；
11. `content-review llm-check` smoke check；
12. single-file / batch `--enable-llm`；
13. single-file / batch `--llm-output` raw sidecar；
14. explicit `--combined-output`；
15. combined envelope builder；
16. combined Markdown report renderer；
17. explicit opt-in `--llm-fail-on`；
18. combined envelope 中的 `llm.quality_gate` metadata；
19. combined Markdown report 中的 LLM quality gate 展示；
20. LLM mainline integration release readiness audit。

现在项目已经不再是“LLM 能力是否接入”的阶段，而是进入：

> 真实 LLM Provider 使用验证与对外接口化准备阶段。

前面已经发现一个关键问题：

> 仅配置 API Key 不够，真实 LLM 调用通常还需要明确 provider、model name，以及可能的 base URL / endpoint / provider-specific 参数。

因此，本任务需要补齐真实 LLM Provider 的使用说明、最小 smoke test 流程、配置示例和相关测试，确保用户可以拿自己的 LLM API 做一次最小可验证调用。

本任务不是新增 MCP、Python API、REST API 或前端，也不是引入复杂 provider 矩阵，而是让当前已有 LLM CLI 能力具备清晰、稳定、可复现的真实 provider 使用路径。

---

## 2. 任务目标

本任务目标是：

> 补齐真实 LLM Provider 的最小使用验证路径，明确 API Key、model name、provider config、secret resolver、`llm-check`、`--enable-llm`、`--llm-output`、`--combined-output` 的真实使用方式，并通过测试和文档固定契约。

完成后应达到：

1. 文档明确说明真实 LLM 调用需要哪些配置；
2. 文档明确说明 API Key 与 model name 的关系；
3. 文档明确说明如何通过环境变量提供 secret；
4. 文档明确说明如何运行 `content-review llm-check`；
5. 文档明确说明如何运行一次 single-file LLM 审计；
6. 文档明确说明如何运行一次 batch LLM 审计；
7. 文档明确说明如何输出 raw LLM sidecar；
8. 文档明确说明如何输出 combined JSON / Markdown；
9. 文档明确说明真实 API smoke test 不应进入默认 CI；
10. 测试覆盖 provider config、model name、secret resolver、错误提示和文档示例；
11. 不提交任何真实 API Key；
12. 不改变 deterministic review 默认行为；
13. 不改变 0083–0087 已经收口的 LLM output / combined output / gate 契约。

---

## 3. 本任务允许做什么

本任务允许完成以下内容：

1. 审计当前真实 LLM provider runtime configuration 是否清晰；
2. 补齐真实 LLM provider 使用文档；
3. 补齐 `llm-check` 真实使用示例；
4. 补齐 single-file `--enable-llm` 真实使用示例；
5. 补齐 batch `--enable-llm` 真实使用示例；
6. 补齐 `--llm-output` raw sidecar 真实使用示例；
7. 补齐 `--combined-output` 真实使用示例；
8. 明确 model name 必须如何配置；
9. 明确 API Key 必须如何配置；
10. 明确 secret resolver 支持和不支持的方式；
11. 明确 provider config / factory 的最小契约；
12. 在必要时改进缺失 model name 时的错误提示；
13. 在必要时改进缺失 API Key 时的错误提示；
14. 在必要时改进 provider config validation；
15. 新增或更新文档测试；
16. 新增或更新 provider config / secret resolver / CLI smoke check 相关测试；
17. 新增不含真实 secret 的示例文件；
18. 更新 `PROJECT_STATE.md`；
19. 更新 `CHANGELOG.md`。

---

## 4. 本任务不允许做什么

本任务不允许完成以下内容：

1. 不允许新增 MCP Server；
2. 不允许新增 Python API facade；
3. 不允许新增 REST API；
4. 不允许新增 Web 前端；
5. 不允许新增 Tauri / desktop client；
6. 不允许新增 Supabase 集成；
7. 不允许新增用户系统；
8. 不允许新增支付系统；
9. 不允许把真实 API Key 写入仓库；
10. 不允许提交 `.env` 中的真实 secret；
11. 不允许让默认测试依赖真实外部 LLM API；
12. 不允许让默认 CI 调用真实 LLM API；
13. 不允许改变 `--output` deterministic-only 主输出语义；
14. 不允许改变 `--llm-output` raw sidecar schema；
15. 不允许改变 `--combined-output` explicit opt-in 语义；
16. 不允许让 `--combined-output` 自动启用 LLM；
17. 不允许让 `--llm-fail-on` 自动启用 LLM；
18. 不允许让 LLM findings 默认影响 exit code；
19. 不允许让 LLM findings 进入 deterministic `ReviewResult.findings`；
20. 不允许让 LLM findings 进入 deterministic `severity_counts`；
21. 不允许让 LLM findings 进入 deterministic `rule_counts`；
22. 不允许引入新的复杂 provider abstraction；
23. 不允许一次性支持大量 provider-specific 行为；
24. 不允许重构整个 CLI；
25. 不允许重写已有 combined envelope / report / quality gate 主线。

---

## 5. 需要修改的文件

预计包括但不限于：

```text
docs/LLM_PROVIDER_USAGE.md
docs/CLI.md
docs/CI.md
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
PROJECT_STATE.md
CHANGELOG.md
```

如当前已有示例目录，可以更新：

```text
examples/llm_review_artifacts/README.md
examples/llm_review_artifacts/single-file/
examples/llm_review_artifacts/batch/
```

如需要新增真实 provider 使用示例，可以新增：

```text
examples/real_llm_usage/README.md
examples/real_llm_usage/.env.example
examples/real_llm_usage/single-file-smoke.md
```

如发现 provider config / secret resolver / smoke check 缺少必要测试，可以更新或新增：

```text
tests/test_llm_provider_config.py
tests/test_llm_provider_factory.py
tests/test_llm_secret_resolver.py
tests/test_llm_smoke_check.py
tests/test_llm_provider_usage_docs.py
tests/test_cli.py
```

如确实需要改进错误提示或配置校验，可以最小修改：

```text
src/content_review_engine/llm/config.py
src/content_review_engine/llm/secrets.py
src/content_review_engine/llm/smoke_check.py
src/content_review_engine/llm/factory.py
src/content_review_engine/cli.py
```

具体文件名以当前仓库实际结构为准。

---

## 6. 实现要求

### 6.1 真实 LLM 配置说明

文档中必须明确说明：

1. 真实 LLM 调用通常至少需要：

   * provider；
   * model name；
   * API key；
   * 可选 base URL / endpoint；
   * 可选 provider-specific 参数。

2. API Key 只解决认证问题，不等于已经指定模型。

3. model name 必须显式配置或通过当前项目已有配置机制提供。

4. 如果当前项目支持通过 CLI 参数传入 model，则文档必须给出 CLI 示例。

5. 如果当前项目支持通过环境变量传入 model，则文档必须给出环境变量示例。

6. 如果当前项目支持通过 profile / config file 传入 model，则文档必须给出配置片段示例。

7. 如果当前项目暂不支持某种配置方式，文档必须明确说明“不支持”，不要暗示可用。

---

### 6.2 Secret Resolver 说明

文档中必须明确说明：

1. 不要把真实 API Key 写入仓库；
2. 不要把真实 API Key 写入示例文件；
3. 推荐通过环境变量提供 API Key；
4. `.env.example` 只能包含占位符；
5. `.env` 不应提交；
6. 当前 secret resolver 支持哪些 secret reference 形式；
7. 缺失 secret 时应该出现什么错误；
8. 空 secret 或占位符 secret 应如何处理；
9. 文档示例必须与实际 resolver 行为一致。

---

### 6.3 `llm-check` Smoke Test 说明

文档中必须提供最小 smoke test 流程。

至少包括：

```bash
content-review llm-check ...
```

或当前项目实际支持的命令形式。

说明必须覆盖：

1. 命令用途；
2. 成功时会输出什么；
3. 失败时常见原因；
4. 缺少 API Key 的失败原因；
5. 缺少 model name 的失败原因；
6. provider 不支持的失败原因；
7. 网络错误或认证错误如何识别；
8. 为什么该命令不应放入默认 CI；
9. 如何在本地手动运行。

---

### 6.4 Single-file LLM 使用示例

文档中必须提供一次单文件真实 LLM 审计示例。

示例应覆盖：

```bash
content-review review <input.md> --profile <profile.yml> --enable-llm ...
```

并根据当前项目实际 CLI，展示如何同时使用：

```text
--llm-output
--combined-output
--format json
--format markdown
--llm-fail-on
```

注意：

1. 示例必须和当前 CLI 真实参数一致；
2. 不要使用不存在的参数；
3. 不要暗示 `--combined-output` 会自动启用 LLM；
4. 不要暗示 `--llm-fail-on` 会自动启用 LLM；
5. 要明确 `--output` 仍然是 deterministic 主输出；
6. 要明确 `--llm-output` 是 raw LLM sidecar；
7. 要明确 `--combined-output` 是 explicit opt-in combined envelope / report。

---

### 6.5 Batch LLM 使用示例

文档中必须提供一次 batch 真实 LLM 审计示例。

示例应覆盖：

```bash
content-review batch <input_dir> --profile <profile.yml> --enable-llm ...
```

并根据当前项目实际 CLI，展示如何同时使用：

```text
--llm-output
--combined-output
--format json
--format markdown
--llm-fail-on
```

注意：

1. batch 行为必须与 single-file 说明一致；
2. raw sidecar 与 combined output 的语义必须一致；
3. exit code 行为必须说明清楚；
4. deterministic gate 与 LLM gate 必须说明清楚。

---

### 6.6 Quality Gate 行为说明

文档中必须再次确认：

1. `--fail-on` 是 deterministic-only；
2. `--llm-fail-on` 是 LLM-only；
3. LLM findings 默认不影响 exit code；
4. 只有显式传入 `--llm-fail-on` 时，LLM findings 才能影响 exit code；
5. `--llm-fail-on` 不会自动启用 LLM；
6. `--combined-output` 不会自动启用 LLM；
7. combined envelope 中可以包含 `llm.quality_gate` metadata；
8. raw LLM sidecar 不应被 LLM gate metadata 污染。

---

### 6.7 示例文件要求

如果新增 `.env.example`，只能包含占位符，例如：

```bash
CONTENT_REVIEW_LLM_API_KEY=replace-with-your-api-key
CONTENT_REVIEW_LLM_MODEL=replace-with-your-model-name
```

具体变量名必须使用当前项目真实支持的变量名。

如果当前项目不是通过这些变量名配置，则必须使用实际变量名，不允许发明不存在的配置方式。

示例 Markdown 文件应非常小，便于 smoke test，例如：

```md
# Test Article

This is a short draft used for LLM review smoke testing.
```

示例中不得包含真实敏感内容。

---

### 6.8 错误提示要求

如当前错误提示不清晰，可以做最小改进。

至少应区分：

1. provider 缺失；
2. model name 缺失；
3. secret reference 缺失；
4. secret environment variable 缺失；
5. secret 为空；
6. provider factory 不支持；
7. LLM response validation failed；
8. runtime provider error。

错误提示应尽量帮助用户知道下一步该配置什么。

---

### 6.9 测试要求

测试不应调用真实 LLM API。

默认测试只能使用：

1. mock provider；
2. PydanticAI test model；
3. fake env；
4. monkeypatch；
5. snapshot / reference artifact；
6. docs consistency tests。

必须新增或更新测试覆盖：

1. provider config 中 model name 的要求；
2. 缺失 model name 的错误行为；
3. 缺失 API key env 的错误行为；
4. secret resolver 不泄露 secret；
5. `.env.example` 不包含真实 secret；
6. `llm-check` 文档示例与 CLI 参数一致；
7. single-file LLM 使用文档示例与 CLI 参数一致；
8. batch LLM 使用文档示例与 CLI 参数一致；
9. `--combined-output` 不自动启用 LLM 的说明仍存在；
10. `--llm-fail-on` 不自动启用 LLM 的说明仍存在；
11. 默认 CI 不需要真实 LLM API。

---

## 7. 文档更新要求

必须更新：

```text
docs/LLM_PROVIDER_USAGE.md
PROJECT_STATE.md
CHANGELOG.md
```

根据实际改动更新：

```text
docs/CLI.md
docs/CI.md
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
examples/llm_review_artifacts/README.md
```

文档中必须清楚区分：

```text
deterministic output
raw LLM sidecar
combined output
deterministic quality gate
LLM quality gate
local smoke test
default CI
real provider usage
test-model usage
```

---

## 8. 验收标准

完成后应满足：

1. 用户可以根据文档配置自己的真实 LLM API；
2. 用户知道 API Key 与 model name 都需要配置；
3. 用户知道如何运行 `content-review llm-check`；
4. 用户知道如何运行 single-file LLM review；
5. 用户知道如何运行 batch LLM review；
6. 用户知道如何输出 raw LLM sidecar；
7. 用户知道如何输出 combined JSON / Markdown；
8. 用户知道真实 LLM smoke test 不属于默认 CI；
9. 用户知道 `.env.example` 不能包含真实 secret；
10. 测试覆盖配置、secret、文档示例和 smoke check 行为；
11. `uv run pytest` 通过；
12. `PROJECT_STATE.md` 准确记录当前阶段；
13. `CHANGELOG.md` 记录本次收口；
14. 没有改变 deterministic 主线行为；
15. 没有改变 0083–0087 已固定的 combined output / LLM gate 契约。

---

## 9. 风险与注意事项

本任务最容易出现的风险：

1. 文档写了当前代码并不支持的配置方式；
2. 只写 API Key，忘记 model name；
3. 把真实 LLM smoke test 加入默认 CI；
4. 示例中泄露真实 API Key；
5. `.env.example` 使用了真实 secret；
6. 错误提示过于模糊，用户不知道缺什么；
7. 为了跑真实 API 而大改 provider factory；
8. 顺手新增 MCP / Python API；
9. 顺手改变 combined output schema；
10. 顺手改变 deterministic quality gate；
11. 让 LLM findings 默认影响 exit code；
12. 让 `--combined-output` 或 `--llm-fail-on` 隐式启用 LLM。

本任务应保持小步收口，只修补真实 LLM 使用验证路径，不扩大产品能力范围。

---

## 10. 完成后需要运行的命令

至少运行：

```bash
uv run pytest
```

如果修改了特定测试文件，应额外运行，例如：

```bash
uv run pytest tests/test_llm_provider_config.py
uv run pytest tests/test_llm_secret_resolver.py
uv run pytest tests/test_llm_smoke_check.py
uv run pytest tests/test_llm_provider_usage_docs.py
uv run pytest tests/test_cli.py
```

如果项目已有 lint / type check 命令，也应根据仓库规则运行。

不要在默认验证中要求真实 API Key。

---
