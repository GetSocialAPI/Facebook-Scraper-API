import json
import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from getsocialapi_facebook import Client, FacebookAPI  # noqa: E402
from getsocialapi_facebook.exceptions import (  # noqa: E402
    APIKeyError,
    BadRequestError,
    RateLimitError,
    ServiceUnavailableError,
    UpstreamError,
)
from getsocialapi_facebook.http import Transport  # noqa: E402


def fake_response(status, body=None, headers=None):
    r = MagicMock()
    r.status_code = status
    r.headers = headers or {}
    r.text = json.dumps(body) if body is not None else ""
    r.json = (lambda b=body: b) if body is not None else (lambda: (_ for _ in ()).throw(ValueError()))
    return r


def make_client(session):
    return Client(api_key="test_key", session=session, max_retries=0)


class TestErrorMessages(unittest.TestCase):
    def test_reason_shapes(self):
        from getsocialapi_facebook.exceptions import BadRequestError
        self.assertEqual(str(BadRequestError(body={"message": "bad thing", "status": "fail"})), "bad thing")
        self.assertEqual(str(BadRequestError(body={"error": "invalid id"})), "invalid id")
        self.assertEqual(str(BadRequestError(body={"error": {"message": "nested"}})), "nested")
        self.assertEqual(str(BadRequestError(body={})), "Bad request")


class TestClient(unittest.TestCase):
    def test_requires_key(self):
        with self.assertRaises(ValueError):
            Client(api_key=None)

    def test_sends_api_key_header(self):
        s = MagicMock()
        s.request.return_value = fake_response(200, {"group_id": "1"})
        make_client(s).fb.overview("1")
        headers = s.request.call_args.kwargs["headers"]
        self.assertEqual(headers, {"X-API-Key": "test_key"})


class TestErrors(unittest.TestCase):
    def _transport(self, resp):
        t = Transport(api_key="k", max_retries=0)
        t.session = MagicMock()
        t.session.request.return_value = resp
        return t

    def test_400(self):
        with self.assertRaises(BadRequestError) as ctx:
            self._transport(fake_response(400, {"error": "bad params"})).request("GET", "/x")
        self.assertEqual(str(ctx.exception), "bad params")

    def test_401(self):
        with self.assertRaises(APIKeyError):
            self._transport(fake_response(401, {"error": "invalid key"})).request("GET", "/x")

    def test_429_limit(self):
        with self.assertRaises(RateLimitError) as ctx:
            self._transport(fake_response(429, {"error": "rate limit", "limit": 32})).request("GET", "/x")
        self.assertEqual(ctx.exception.limit, 32)

    def test_502(self):
        with self.assertRaises(UpstreamError):
            self._transport(fake_response(502, {"error": "could not resolve group id from x"})).request("GET", "/x")

    def test_503(self):
        with self.assertRaises(ServiceUnavailableError):
            self._transport(fake_response(503, {})).request("GET", "/x")


class TestFacebookAPI(unittest.TestCase):
    def api(self):
        t = MagicMock()
        return FacebookAPI(t), t

    def check(self, method, args, expected_path, expected_params=None, kwargs=None):
        a, t = self.api()
        getattr(a, method)(*args, **(kwargs or {}))
        call = t.request.call_args
        self.assertEqual(call.args, ("GET", expected_path))
        if expected_params is not None:
            self.assertEqual(call.kwargs.get("params"), expected_params)

    def test_resolve(self):
        url = "https://www.facebook.com/groups/freegarden/"
        self.check("resolve", (url,), "/resolve", {"url": url})

    def test_overview(self):
        self.check("overview", ("800246542990860",), "/overview",
                   {"group_id": "800246542990860"})

    def test_members(self):
        self.check("members", ("800246542990860",), "/api/v1/members",
                   {"group_id": "800246542990860"})

    def test_members_after(self):
        self.check("members", ("800246542990860",), "/api/v1/members",
                   {"group_id": "800246542990860", "after": "AQH"}, {"after": "AQH"})

    def test_contacts(self):
        self.check("contacts", ("100001797717646",), "/api/v1/contacts",
                   {"user_id": "100001797717646"})

    def test_resolve_profile(self):
        self.check("resolve_profile", ("https://www.facebook.com/zuck",), "/resolve/profile",
                   {"url": "https://www.facebook.com/zuck"})

    def test_followers(self):
        self.check("followers", ("61595500131774",), "/api/v1/followers",
                   {"user_id": "61595500131774"})

    def test_followings_after(self):
        self.check("followings", ("61595500131774",), "/api/v1/followings",
                   {"user_id": "61595500131774", "after": "C"}, {"after": "C"})

    def test_friends(self):
        self.check("friends", ("61595500131774",), "/api/v1/friends",
                   {"user_id": "61595500131774"})

    def test_posts(self):
        self.check("posts", ("100053723115450",), "/api/v1/posts",
                   {"user_id": "100053723115450"})

    def test_posts_after(self):
        cursor = "AQ" * 444  # ~888-char base64 end_cursor
        self.check("posts", ("100053723115450",), "/api/v1/posts",
                   {"user_id": "100053723115450", "after": cursor},
                   {"after": cursor})

    def test_group_posts(self):
        self.check("group_posts", ("800246542990860",), "/api/v1/group_posts",
                   {"group_id": "800246542990860"})

    def test_group_posts_after(self):
        cur = "Cg8TZXhpc3RpbmdfdW5pdF9jb3VudA"
        self.check("group_posts", ("800246542990860",), "/api/v1/group_posts",
                   {"group_id": "800246542990860", "after": cur},
                   {"after": cur})

    def test_feed_user(self):
        self.check("feed", ("100053723115450",), "/api/v1/feed",
                   {"user_id": "100053723115450"})

    def test_feed_group_per_page(self):
        self.check("feed", (), "/api/v1/feed",
                   {"group_id": "800246542990860", "per_page": 10},
                   {"group_id": "800246542990860", "per_page": 10})

    def test_feed_after(self):
        cur = "AQ" * 444
        self.check("feed", ("100053723115450",), "/api/v1/feed",
                   {"user_id": "100053723115450", "after": cur},
                   {"after": cur})

    def test_feed_validation(self):
        a, _ = self.api()
        with self.assertRaises(ValueError):
            a.feed()                              # ни одного id
        with self.assertRaises(ValueError):
            a.feed("100053723115450", "800246542990860")  # оба
        with self.assertRaises(ValueError):
            a.feed(user_id="100053723115450", per_page=21)
        with self.assertRaises(ValueError):
            a.feed(user_id="100053723115450", per_page=2)

    def test_validation(self):
        a, _ = self.api()
        with self.assertRaises(ValueError):
            a.overview("not-digits")
        with self.assertRaises(ValueError):
            a.members("12x")
        with self.assertRaises(ValueError):
            a.resolve("  ")


if __name__ == "__main__":
    unittest.main(verbosity=2)
