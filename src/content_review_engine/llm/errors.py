from __future__ import annotations


class LLMReviewError(Exception):
    """Base error for future LLM review failures."""


class LLMProviderError(LLMReviewError):
    """Raised when a provider adapter fails to complete a review."""


class LLMProviderRuntimeError(LLMProviderError):
    """Raised when a provider runtime fails for an unknown reason."""


class LLMProviderTimeoutError(LLMProviderRuntimeError):
    """Raised when a provider runtime times out."""


class LLMProviderAuthError(LLMProviderRuntimeError):
    """Raised when a provider runtime rejects authentication."""


class LLMProviderNetworkError(LLMProviderRuntimeError):
    """Raised when a provider runtime cannot reach the remote service."""


class LLMProviderRateLimitError(LLMProviderRuntimeError):
    """Raised when a provider runtime is rate limited."""


class LLMProviderModelError(LLMProviderRuntimeError):
    """Raised when a provider runtime rejects the configured model or request."""


class LLMProviderConfigError(LLMReviewError):
    """Raised when provider configuration is invalid."""


class LLMProviderSecretError(LLMProviderConfigError):
    """Raised when provider secret resolution fails safely."""


class LLMProviderNotImplementedError(LLMProviderConfigError):
    """Raised when a recognized provider is not implemented yet."""


class LLMResponseValidationError(LLMReviewError):
    """Raised when provider output cannot be validated as an LLM review result."""


__all__ = [
    "LLMProviderAuthError",
    "LLMProviderConfigError",
    "LLMProviderModelError",
    "LLMProviderNetworkError",
    "LLMProviderNotImplementedError",
    "LLMProviderError",
    "LLMProviderRateLimitError",
    "LLMProviderRuntimeError",
    "LLMProviderSecretError",
    "LLMProviderTimeoutError",
    "LLMResponseValidationError",
    "LLMReviewError",
]
