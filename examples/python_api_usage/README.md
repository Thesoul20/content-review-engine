# Python API Usage

Import the stable facade from `content_review_engine.api`.

## Single File

```python
from content_review_engine.api import review_file

result = review_file(
    "tests/fixtures/markdown/clean_article.md",
    "tests/fixtures/profiles/default.yml",
    include_combined_result=True,
)

print(result.review_result.summary.finding_count)
print(result.combined_result.llm_status)
```

## Batch

```python
from content_review_engine.api import review_batch

result = review_batch(
    "tests/fixtures/batch/articles",
    "tests/fixtures/batch/profile.yml",
    recursive=True,
)

print(result.batch_result.summary.file_count)
```

## Optional LLM

Use `mock` in tests and examples:

```python
from content_review_engine.api import review_file
from content_review_engine.llm import LLMProviderConfig

result = review_file(
    "tests/fixtures/markdown/clean_article.md",
    "tests/fixtures/profiles/default.yml",
    enable_llm=True,
    llm_provider_config=LLMProviderConfig(provider="mock"),
    include_combined_result=True,
)

print(result.llm_result)
```

The examples do not depend on a real API key, do not use `.env`, and do not
call an external provider by default.
