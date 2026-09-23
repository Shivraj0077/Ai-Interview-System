class ServiceError(Exception):
    """
    An error that is safe to show to users.

    `message` is written for humans; internal details (stack traces, provider
    responses, credentials) are logged server-side and never put here.
    """

    status_code = 500
    code = "internal_error"
    retryable = False

    def __init__(self, message: str, *, code: str | None = None, retryable: bool | None = None):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        if retryable is not None:
            self.retryable = retryable


class NotFoundError(ServiceError):
    status_code = 404
    code = "not_found"


class ConflictError(ServiceError):
    status_code = 409
    code = "conflict"


class ValidationError(ServiceError):
    status_code = 422
    code = "invalid_request"


class UpstreamError(ServiceError):
    """An AI provider or database call failed. Usually worth retrying."""

    status_code = 502
    code = "upstream_error"
    retryable = True


class RateLimitedError(UpstreamError):
    status_code = 429
    code = "rate_limited"
