from content_review_engine.api import review_file


result = review_file(
    "tests/fixtures/markdown/clean_article.md",
    "tests/fixtures/profiles/default.yml",
    include_combined_result=True,
)

print(result.review_result.summary.finding_count)
print(result.combined_result.llm_status if result.combined_result is not None else "none")
