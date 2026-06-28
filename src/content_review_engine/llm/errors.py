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


class LLMProviderRetryExhaustedError(LLMProviderRuntimeError):
    """Raised when retryable provider runtime failures exceed configured retries."""


class LLMProviderConfigError(LLMReviewError):
    """Raised when provider configuration is invalid."""


class UnsupportedLLMProviderError(LLMProviderConfigError):
    """Raised when a requested reviewer provider name is not supported."""


class LLMProviderSecretError(LLMProviderConfigError):
    """Raised when provider secret resolution fails safely."""


class MissingLLMProviderSecretReferenceError(LLMProviderSecretError):
    """Raised when secret resolution is requested without api_key_env."""


class MissingLLMProviderSecretEnvironmentVariableError(LLMProviderSecretError):
    """Raised when the configured secret environment variable is not set."""


class EmptyLLMProviderSecretEnvironmentVariableError(LLMProviderSecretError):
    """Raised when the configured secret environment variable is empty."""


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
    "LLMProviderRetryExhaustedError",
    "LLMProviderRuntimeError",
    "LLMProviderSecretError",
    "LLMProviderTimeoutError",
    "MissingLLMProviderSecretReferenceError",
    "MissingLLMProviderSecretEnvironmentVariableError",
    "EmptyLLMProviderSecretEnvironmentVariableError",
    "LLMResponseValidationError",
    "LLMReviewError",
    "UnsupportedLLMProviderError",
]
