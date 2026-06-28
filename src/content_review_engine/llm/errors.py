from __future__ import annotations


class LLMReviewError(Exception):
    """Base error for future LLM review failures."""


class LLMProviderError(LLMReviewError):
    """Raised when a provider adapter fails to complete a review."""


class LLMProviderConfigError(LLMReviewError):
    """Raised when provider configuration is invalid."""


class LLMProviderSecretError(LLMProviderConfigError):
    """Raised when provider secret resolution fails safely."""


class LLMProviderNotImplementedError(LLMProviderConfigError):
    """Raised when a recognized provider is not implemented yet."""


class LLMResponseValidationError(LLMReviewError):
    """Raised when provider output cannot be validated as an LLM review result."""


__all__ = [
    "LLMProviderConfigError",
    "LLMProviderNotImplementedError",
    "LLMProviderError",
    "LLMProviderSecretError",
    "LLMResponseValidationError",
    "LLMReviewError",
]
