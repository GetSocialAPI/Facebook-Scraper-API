import os

from .facebook import FacebookAPI
from .http import DEFAULT_BASE_URL, Transport


class Client:
    """GetSocialAPI Facebook client.

    Usage:
        from getsocialapi_facebook import Client
        client = Client(api_key="gsa_live_...")
        group = client.resolve("https://www.facebook.com/groups/freegarden/")
        client.fb.members(group["group_id"], first=15)
    """

    def __init__(self, api_key=None, base_url=DEFAULT_BASE_URL, timeout=30,
                 max_retries=3, session=None):
        api_key = api_key or os.environ.get("GETSOCIALAPI_FB_API_KEY")
        if not api_key:
            raise ValueError(
                "api_key is required (pass api_key=... or set GETSOCIALAPI_FB_API_KEY)"
            )
        self._transport = Transport(
            base_url=base_url, api_key=api_key, timeout=timeout,
            max_retries=max_retries, session=session,
        )
        self.fb = self.facebook = FacebookAPI(self._transport)
