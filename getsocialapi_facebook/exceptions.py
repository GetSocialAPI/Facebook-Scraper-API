class GetSocialFacebookError(Exception):
    """Base error for all GetSocialAPI Facebook SDK failures."""

    def __init__(self, message, response=None, body=None):
        super().__init__(message)
        self.response = response
        self.body = body if body is not None else {}


def _reason(body, fallback):
    """Extract a human-readable reason: {"error": "..."} | {"error": {"message"}} | {"message": ..."}."""
    err = body.get("error")
    if isinstance(err, dict):
        err = err.get("message")
    if isinstance(err, str) and err:
        return err
    msg = body.get("message")
    if isinstance(msg, str) and msg:
        return msg
    return fallback


class BadRequestError(GetSocialFacebookError):
    """400 — bad parameters."""

    def __init__(self, response=None, body=None):
        body = body or {}
        super().__init__(_reason(body, "Bad request"), response, body)


class APIKeyError(GetSocialFacebookError):
    """401 — invalid API key."""

    def __init__(self, response=None, body=None):
        super().__init__("Invalid API key", response, body)


class RateLimitError(GetSocialFacebookError):
    """429 — rate limit (body: {"error": "rate limit", "limit": N})."""

    def __init__(self, response=None, body=None, limit=None):
        super().__init__(f"Rate limit exceeded (limit: {limit})", response, body)
        self.limit = limit


class UpstreamError(GetSocialFacebookError):
    """502 — temporary upstream error. Automatically retried."""

    def __init__(self, response=None, body=None):
        body = body or {}
        super().__init__(_reason(body, "Temporary upstream error"), response, body)


class ServiceUnavailableError(GetSocialFacebookError):
    """503 — service overloaded."""

    def __init__(self, response=None, body=None):
        super().__init__("Service overloaded", response, body)
