import time

import requests

from .exceptions import (
    APIKeyError,
    BadRequestError,
    GetSocialFacebookError,
    RateLimitError,
    ServiceUnavailableError,
    UpstreamError,
)

DEFAULT_BASE_URL = "https://api.getsocialapi.com/fb"

RETRYABLE_STATUS = {429, 500, 502, 503, 504}


class Transport:
    """HTTP transport: X-API-Key auth, JSON parsing, retries."""

    def __init__(self, base_url=DEFAULT_BASE_URL, api_key=None, timeout=30,
                 max_retries=3, session=None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = session or requests.Session()

    def request(self, method, path, params=None):
        url = f"{self.base_url}{path}"
        headers = {"X-API-Key": self.api_key}
        attempts = self.max_retries + 1
        for attempt in range(attempts):
            try:
                resp = self.session.request(
                    method, url, params=params, headers=headers, timeout=self.timeout,
                )
            except (requests.ConnectionError, requests.Timeout) as e:
                if attempt < attempts - 1:
                    time.sleep(min(2 ** attempt, 10))
                    continue
                raise GetSocialFacebookError(f"Network error: {e}") from e

            if resp.status_code in RETRYABLE_STATUS and attempt < attempts - 1:
                time.sleep(self._retry_after(resp))
                continue
            return self._parse(resp)
        raise GetSocialFacebookError("Request failed after retries")  # pragma: no cover

    @staticmethod
    def _retry_after(resp):
        try:
            return min(max(int(float(resp.headers.get("Retry-After", 1))), 0), 30)
        except (TypeError, ValueError):
            return 1

    @staticmethod
    def _parse(resp):
        try:
            body = resp.json()
        except ValueError:
            body = {"raw": resp.text}

        if resp.status_code == 400:
            raise BadRequestError(resp, body)
        if resp.status_code == 401:
            raise APIKeyError(resp, body)
        if resp.status_code == 429:
            raise RateLimitError(resp, body, limit=(body or {}).get("limit"))
        if resp.status_code == 502:
            raise UpstreamError(resp, body)
        if resp.status_code == 503:
            raise ServiceUnavailableError(resp, body)
        if resp.status_code >= 400:
            raise GetSocialFacebookError(f"HTTP {resp.status_code}: {body}", resp, body)
        return body
