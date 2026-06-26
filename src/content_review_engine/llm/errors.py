from __future__ import annotations


class LLMReviewError(Exception):
    """Base error for future LLM review failures."""


class LLMProviderError(LLMReviewError):
    """Raised when a provider adapter fails to complete a review."""


class LLMResponseValidationError(LLMReviewError):
    """Raised when provider output cannot be validated as an LLM review result."""


__all__ = [
    "LLMProviderError",
    "LLMResponseValidationError",
    "LLMReviewError",
]
