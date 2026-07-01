# Real LLM Usage

This directory documents the current minimum manual verification path for a
real LLM provider run.

It is reference-only. It does not make the CLI read `.env` files
automatically, and it does not add any new provider contract beyond the
existing `pydanticai` path.

## Supported Today

Current real-provider runtime path:

- real review provider: `pydanticai`
- safe local test providers: `mock`, `pydantic-ai-testmodel`

Current configuration inputs for real-provider review:

- provider: `--llm-provider pydanticai` or `--llm-config <file>`
- model name: `--llm-model <name>` or `model:` in `--llm-config`
- API key reference: `--llm-api-key-env <ENV_NAME>` or `api_key_env:` in
  `--llm-config`
- optional base URL: `--llm-base-url <url>` or `base_url:` in `--llm-config`

Not supported today:

- raw API key values in CLI arguments
- raw API key values in committed YAML config
- automatic `.env` loading by `content-review`
- model name from a dedicated environment-variable contract
- provider config inside review profile YAML

## Secret Setup

Use `.env.example` as a placeholder template only.

The CLI does not read `.env` automatically. You must export your real secret
into the shell yourself or use your own local secret manager before running
the commands below.

Example:

```bash
export OPENAI_API_KEY="replace-with-your-real-key"
```

Optional for OpenAI-compatible endpoints:

```bash
export OPENAI_BASE_URL="https://your-openai-compatible-endpoint.example/v1"
```

## Minimal `llm-check`

Config-file path:

```bash
uv run content-review llm-check \
  --llm-config examples/llm/pydanticai/llm-provider.yml
```

Direct CLI path:

```bash
uv run content-review llm-check \
  --llm-provider pydanticai \
  --llm-model openai:gpt-4o-mini \
  --llm-api-key-env OPENAI_API_KEY
```

Explicit live smoke call:

```bash
uv run content-review llm-check \
  --llm-provider pydanticai \
  --llm-model openai:gpt-4o-mini \
  --llm-api-key-env OPENAI_API_KEY \
  --llm-base-url "$OPENAI_BASE_URL" \
  --live
```

Notes:

- `--provider` on `llm-check` is only for safe factory providers such as
  `mock` and `pydantic-ai-testmodel`
- real-provider `llm-check` uses `--llm-provider pydanticai` or
  `--llm-config`
- API key authentication and model selection are separate requirements
- if `model` is missing, `pydanticai` smoke check fails before live runtime
- if `api_key_env` is missing or empty, secret resolution fails before live
  runtime

## Single-file Smoke Review

```bash
uv run content-review review \
  examples/real_llm_usage/single-file-smoke.md \
  --profile profiles/examples/general-basic.yaml \
  --enable-llm \
  --llm-provider pydanticai \
  --llm-model openai:gpt-4o-mini \
  --llm-api-key-env OPENAI_API_KEY \
  --llm-base-url "$OPENAI_BASE_URL" \
  --llm-output /tmp/content-review-real-single.llm.json \
  --combined-output /tmp/content-review-real-single.combined.md
```

Optional explicit LLM gate:

```bash
uv run content-review review \
  examples/real_llm_usage/single-file-smoke.md \
  --profile profiles/examples/general-basic.yaml \
  --enable-llm \
  --llm-provider pydanticai \
  --llm-model openai:gpt-4o-mini \
  --llm-api-key-env OPENAI_API_KEY \
  --llm-output /tmp/content-review-real-single.llm.json \
  --llm-fail-on error
```

## Batch Smoke Review

```bash
uv run content-review batch \
  examples/real_llm_usage/batch \
  --profile profiles/examples/general-basic.yaml \
  --recursive \
  --enable-llm \
  --llm-provider pydanticai \
  --llm-model openai:gpt-4o-mini \
  --llm-api-key-env OPENAI_API_KEY \
  --llm-output /tmp/content-review-real-batch.llm.json \
  --combined-output /tmp/content-review-real-batch.combined.json \
  --combined-output-format json
```

Optional explicit LLM gate:

```bash
uv run content-review batch \
  examples/real_llm_usage/batch \
  --profile profiles/examples/general-basic.yaml \
  --recursive \
  --enable-llm \
  --llm-provider pydanticai \
  --llm-model openai:gpt-4o-mini \
  --llm-api-key-env OPENAI_API_KEY \
  --llm-output /tmp/content-review-real-batch.llm.json \
  --llm-fail-on error
```

## What To Check

- deterministic stdout or `--output` remains the canonical deterministic
  artifact
- `--llm-output` writes the raw sidecar contract only
- `--combined-output` stays explicit opt-in and does not auto-enable LLM
- `--llm-fail-on` stays explicit opt-in and does not auto-enable LLM
- default CI should not run these real-provider commands
