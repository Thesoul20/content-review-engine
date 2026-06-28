# TASK-0044: Normalize PydanticAI Provider Adapter Boundary

## 1. 背景

当前项目已经完成确定性规则审计、单文件 / 批量 CLI、JSON / Markdown 报告、Quality Gate，以及 LLM 语义审计相关的 provider interface、mock reviewer、runner、sidecar JSON、sidecar Markdown report 和 provider configuration boundary。

已完成任务包括：

```text
TASK-0040: Add Batch LLM Sidecar Output
TASK-0041: Add LLM Sidecar Summary and Error Handling
TASK-0042: Add LLM Sidecar Markdown Report
TASK-0043: Add Real LLM Provider Configuration Boundary
```

TASK-0043 已经新增：

```text
LLMProviderConfig
provider factory / registry
--llm-provider
--llm-model
--llm-api-key-env
--llm-base-url
LLMProviderConfigError
LLMProviderNotImplementedError
```

当前 provider 行为是：

```text
provider="mock"
  -> 返回 MockLLMReviewer，是当前唯一可运行 provider。

provider="pydanticai"
  -> 名称被识别，但返回 LLMProviderNotImplementedError。

unknown provider
  -> 返回 LLMProviderConfigError。
```

但是 TASK-0043 完成后仍然存在一个边界风险：

> 仓库里可能仍保留旧的 PydanticAI adapter 实现文件和对应测试，但当前 CLI / factory 边界明确认为 `pydanticai` 是 recognized but not implemented。

这会造成语义不一致：

```text
代码里看起来有 PydanticAI adapter
  但 factory / CLI 又说 pydanticai 尚未实现
```

因此，本任务的目标不是接入真实 PydanticAI 调用，而是先统一 PydanticAI adapter 的代码边界、文档边界和测试边界，避免后续真实 provider 接入前出现混乱。

本任务是 TASK-0043 之后的边界整理任务，为后续 TASK-0045 正式接入 PydanticAI provider 做准备。

---

## 2. 任务目标

规范仓库中 PydanticAI provider adapter 的边界，使其与当前 provider factory 行为保持一致。

完成后应满足：

1. 仓库中与 PydanticAI 相关的代码不会造成“已经可运行”的误解；
2. `provider="pydanticai"` 在 factory / CLI 中仍然返回 clear not implemented error；
3. 旧的 PydanticAI adapter 代码要么被移除，要么被明确隔离为 future / experimental skeleton；
4. 所有相关测试与当前 provider boundary 一致；
5. 文档明确说明当前可运行 provider 只有 `mock`；
6. 文档明确说明 `pydanticai` 是已识别但尚未实现的 future provider；
7. 不接入真实 PydanticAI SDK；
8. 不发起真实网络请求；
9. 不读取真实 API key；
10. 不改变 sidecar JSON、sidecar Markdown report、deterministic review 和 Quality Gate 行为。

---

## 3. 本任务允许做什么

本任务只允许完成以下内容：

1. 检查仓库中现有 PydanticAI adapter 相关文件；
2. 统一 PydanticAI adapter 与 provider factory 的边界；
3. 如果旧 adapter 未被当前边界使用，可以删除或隔离旧 adapter；
4. 如果保留旧 adapter，必须改成明确的 future / skeleton / not implemented 语义；
5. 更新 provider factory 测试，确保 `pydanticai` 仍然返回 not implemented；
6. 更新 CLI 测试，确保 `--enable-llm --llm-provider pydanticai` 仍然返回清晰错误；
7. 更新或删除旧的 PydanticAI adapter 测试，使其不再暗示真实 provider 已可运行；
8. 更新 LLM provider 文档；
9. 更新 PROJECT_STATE.md 和 CHANGELOG.md；
10. 保持 mock provider 现有行为不变。

---

## 4. 本任务不允许做什么

本任务不允许实现以下内容：

1. 不接入真实 PydanticAI SDK；
2. 不新增 PydanticAI 依赖；
3. 不调用真实 LLM API；
4. 不发起真实网络请求；
5. 不读取真实 API key；
6. 不解析真实 API key value；
7. 不实现 PydanticAI provider 的真实 review 逻辑；
8. 不实现 prompt template；
9. 不实现 response parsing；
10. 不实现 retry / timeout / rate limit；
11. 不把 LLM findings 合并进主 ReviewResult；
12. 不改变 LLMSidecarResult JSON schema；
13. 不改变 LLM sidecar Markdown report 结构；
14. 不改变 deterministic review JSON schema；
15. 不改变 deterministic Markdown report 结构；
16. 不让 Quality Gate 根据 LLM 结果失败；
17. 不实现 API / MCP / GUI；
18. 不引入 Supabase、用户系统、SaaS、多租户、支付等能力；
19. 不重构整个 LLM runner；
20. 不重构整个 CLI。

---

## 5. 需要修改的文件

预计包括但不限于：

```text
src/content_review_engine/llm/factory.py
src/content_review_engine/llm/errors.py
src/content_review_engine/llm/__init__.py
tests/test_llm_provider_factory.py
tests/test_llm_provider.py
tests/test_cli.py
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
docs/CLI.md
PROJECT_STATE.md
CHANGELOG.md
```

根据仓库实际情况，可能还需要处理已有的 PydanticAI adapter 文件，例如：

```text
src/content_review_engine/llm/pydanticai.py
src/content_review_engine/llm/pydantic_ai.py
src/content_review_engine/llm/providers/pydanticai.py
tests/test_llm_pydanticai.py
tests/test_pydanticai_provider.py
```

具体文件名以当前仓库实际存在的文件为准。

如果现有 PydanticAI adapter 文件确实存在，本任务需要选择一种明确处理方式：

```text
方案 A：删除旧 adapter 和旧测试
  适用于旧 adapter 未被引用、未形成稳定契约、容易误导当前边界的情况。

方案 B：保留但降级为 explicit skeleton
  适用于希望保留文件路径，为后续 TASK-0045 使用的情况。
  skeleton 必须明确抛出 LLMProviderNotImplementedError，不得进行真实调用。

方案 C：移动到明确的 experimental / future 命名空间
  适用于当前仓库已有约定支持 experimental provider 的情况。
```

优先选择最小、最清晰、最符合当前项目结构的方案。不要同时做多个方案。

---

## 6. 实现要求

### 6.1 当前 provider 边界必须保持不变

本任务完成后，provider factory 行为仍然应该是：

```text
provider="mock"
  -> 返回 MockLLMReviewer

provider="pydanticai"
  -> 抛出 LLMProviderNotImplementedError

unknown provider
  -> 抛出 LLMProviderConfigError
```

不得将 `pydanticai` 变成可运行 provider。

不得让 `pydanticai` fallback 到 mock provider。

---

### 6.2 处理旧 PydanticAI adapter

如果仓库中存在旧的 PydanticAI adapter，需要做以下处理之一。

#### 方案 A：删除旧 adapter

如果旧 adapter 没有被当前 factory、CLI、runner 使用，且测试也只是历史遗留，可以删除相关文件和测试。

要求：

1. 删除后所有测试通过；
2. 文档不再引用旧 adapter；
3. `pydanticai` provider name 仍然通过 factory 返回 not implemented；
4. CHANGELOG 中说明移除了未启用的旧 adapter 边界；
5. 不删除 provider name `pydanticai` 的预留行为。

#### 方案 B：保留为 skeleton

如果决定保留文件路径作为未来实现入口，则文件内容必须明确是 skeleton。

建议 skeleton 行为：

```text
class PydanticAIReviewer(LLMReviewer):
    def review(...):
        raise LLMProviderNotImplementedError(
            "Provider 'pydanticai' is recognized but not implemented yet."
        )
```

要求：

1. skeleton 不 import pydanticai SDK；
2. skeleton 不发起网络请求；
3. skeleton 不读取环境变量；
4. skeleton 不保存或输出 API key；
5. skeleton 不被 CLI 默认调用；
6. skeleton 的测试只断言 not implemented；
7. 文档明确这是 future provider skeleton。

#### 方案 C：移动到 experimental / future

只有在仓库已经有 experimental provider 目录或约定时才使用该方案。

要求：

1. 命名清楚，不让用户误解为 production provider；
2. 不从主 `__init__.py` 暴露为可运行 provider；
3. 不被 factory 调用；
4. 文档明确其状态；
5. 不接入真实 SDK。

---

### 6.3 测试语义统一

所有测试必须统一到当前边界：

```text
mock 是唯一可运行 provider。
pydanticai 是 recognized but not implemented。
unknown provider 是 config error。
```

如果旧测试断言 PydanticAI adapter 可以真实 review，则必须删除或改写。

如果旧测试依赖 pydanticai SDK，则必须删除或改写。

如果旧测试需要保留，只允许断言：

```text
PydanticAI provider skeleton raises LLMProviderNotImplementedError.
```

---

### 6.4 CLI 语义统一

CLI 行为必须保持：

```bash
content-review review article.md \
  --profile profile.yml \
  --enable-llm \
  --llm-provider mock
```

正常使用 mock provider。

```bash
content-review review article.md \
  --profile profile.yml \
  --enable-llm \
  --llm-provider pydanticai
```

返回清晰错误：

```text
Provider 'pydanticai' is recognized but not implemented yet.
```

未知 provider 继续返回类似：

```text
Unknown LLM provider 'openai'. Supported providers: 'mock', 'pydanticai'.
```

---

### 6.5 文档语义统一

文档中必须统一说明：

```text
当前可运行 provider:
  mock

已识别但尚未实现:
  pydanticai

当前不支持:
  openai
  anthropic
  local
  other provider names
```

如果保留 PydanticAI skeleton，文档必须说明：

```text
The pydanticai provider name is reserved for future integration.
It is not currently a runnable provider.
```

中文文档中可以写：

```text
pydanticai provider name 已预留，但当前还不是可运行 provider。
```

---

### 6.6 不改变 sidecar / report / quality gate

本任务不得改变以下结构和行为：

```text
LLMSidecarResult JSON schema
LLM sidecar Markdown report structure
deterministic ReviewResult
deterministic JSON output
deterministic Markdown report
Quality Gate
```

如果测试快照因为旧 adapter 清理而变化，需要确认变化只来自 provider 文档或错误路径，不应影响审计结果结构。

---

## 7. 测试要求

必须新增或更新测试，覆盖以下情况。

### 7.1 Provider factory 测试

测试：

1. `provider="mock"` 仍然返回 `MockLLMReviewer`；
2. `provider="pydanticai"` 仍然返回 `LLMProviderNotImplementedError`；
3. unknown provider 仍然返回 `LLMProviderConfigError`；
4. 不会 fallback 到 mock；
5. factory 不 import 真实 pydanticai SDK；
6. factory 不发起网络请求。

---

### 7.2 PydanticAI adapter 边界测试

根据最终处理方案测试：

如果删除旧 adapter：

1. 旧测试应删除或改写；
2. 不再有测试暗示 PydanticAI provider 可运行；
3. factory / CLI 仍然覆盖 pydanticai not implemented。

如果保留 skeleton：

1. skeleton review 调用返回 `LLMProviderNotImplementedError`；
2. skeleton 不 import 真实 SDK；
3. skeleton 不读取 env；
4. skeleton 不发起网络请求；
5. skeleton 错误信息稳定。

---

### 7.3 CLI 测试

测试：

1. `--enable-llm --llm-provider mock` 仍然成功；
2. `--enable-llm --llm-provider pydanticai` 返回 not implemented；
3. unknown provider 返回 config error；
4. 未启用 `--enable-llm` 时 provider 参数不影响 deterministic review；
5. Quality Gate 不受 provider boundary 影响；
6. 错误信息不包含 API key 或 env value。

---

### 7.4 回归测试

必须确保已有测试全部通过：

```bash
uv run pytest
```

如果涉及专门测试文件，也请额外运行：

```bash
uv run pytest tests/test_llm_provider_factory.py
uv run pytest tests/test_llm_provider.py
uv run pytest tests/test_cli.py
```

如果仓库中存在旧 PydanticAI 测试文件，也请运行或删除后确认：

```bash
uv run pytest tests/test_llm_pydanticai.py
uv run pytest tests/test_pydanticai_provider.py
```

具体测试文件名以实际仓库为准。

---

## 8. 文档更新要求

需要更新以下文档：

```text
docs/ARCHITECTURE.md
docs/DATA_MODELS.md
docs/CLI.md
PROJECT_STATE.md
CHANGELOG.md
```

如果 `docs/CI.md` 当前提到 provider config 或 LLM provider 边界，也可以同步更新；否则本任务不强制修改。

更新重点：

1. 在 `docs/ARCHITECTURE.md` 中说明 PydanticAI provider 当前边界；
2. 在 `docs/DATA_MODELS.md` 中说明 `pydanticai` provider name 是 reserved / recognized but not implemented；
3. 在 `docs/CLI.md` 中说明当前只有 `mock` provider 可运行；
4. 在 `docs/CLI.md` 中说明 `--llm-provider pydanticai` 当前会返回 not implemented；
5. 在 `PROJECT_STATE.md` 中记录 TASK-0044 已完成后项目状态；
6. 在 `CHANGELOG.md` 中记录本次边界整理。

---

## 9. 验收标准

本任务完成后应满足：

1. 仓库中 PydanticAI adapter 的状态不再与 factory / CLI 语义冲突；
2. `mock` 仍然是唯一可运行 provider；
3. `pydanticai` 仍然是 recognized but not implemented；
4. unknown provider 仍然是 config error；
5. 不存在测试暗示 PydanticAI provider 已可运行；
6. 不存在文档暗示 PydanticAI provider 已可运行；
7. 不新增 PydanticAI SDK 依赖；
8. 不发起真实网络请求；
9. 不读取或输出真实 API key；
10. 不改变 LLMSidecarResult JSON schema；
11. 不改变 LLM sidecar Markdown report 结构；
12. 不改变 deterministic review JSON / Markdown report 行为；
13. 不改变 Quality Gate 语义；
14. 新增或更新的测试通过；
15. 文档、PROJECT_STATE.md、CHANGELOG.md 已同步更新；
16. `uv run pytest` 全部通过。

---

## 10. 风险与注意事项

1. 不要在本任务中实现真实 PydanticAI provider；
2. 不要新增 pydanticai 依赖；
3. 不要把旧 adapter 接入 factory；
4. 不要让 `pydanticai` fallback 到 mock；
5. 不要让文档出现“pydanticai 已支持”的表述；
6. 不要删除 `pydanticai` provider name 的预留行为；
7. 不要改 sidecar schema；
8. 不要改 sidecar Markdown report 结构；
9. 不要改 Quality Gate；
10. 不要把 provider boundary error 混成 deterministic finding；
11. 不要过度重构 LLM 包结构；
12. 如果删除旧 adapter，要确认没有公共导出被文档或测试引用；
13. 如果保留 skeleton，要确认它不会 import 真实 SDK。

---

## 11. 完成后需要运行的命令

```bash
uv run pytest
```

如果涉及专门测试文件，请额外运行：

```bash
uv run pytest tests/test_llm_provider_factory.py
uv run pytest tests/test_llm_provider.py
uv run pytest tests/test_cli.py
```

如果仓库中存在旧 PydanticAI 测试文件，也请根据最终处理方式运行或确认删除：

```bash
uv run pytest tests/test_llm_pydanticai.py
uv run pytest tests/test_pydanticai_provider.py
```

具体测试文件名以实际仓库为准。

---
