from .client import Client
from .exceptions import (
    APIKeyError,
    BadRequestError,
    GetSocialFacebookError,
    RateLimitError,
    ServiceUnavailableError,
    UpstreamError,
)
from .facebook import FacebookAPI

__version__ = "0.1.0"

__all__ = [
    "Client",
    "FacebookAPI",
    "GetSocialFacebookError",
    "BadRequestError",
    "APIKeyError",
    "RateLimitError",
    "UpstreamError",
    "ServiceUnavailableError",
]
