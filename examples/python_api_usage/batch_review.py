from content_review_engine.api import review_batch


result = review_batch(
    "tests/fixtures/batch/articles",
    "tests/fixtures/batch/profile.yml",
    recursive=True,
)

print(result.batch_result.summary.file_count)
print(result.batch_result.summary.finding_count)
