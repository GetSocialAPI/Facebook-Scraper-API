# getsocialapi-facebook

[![tests](https://github.com/GetSocialAPI/Facebook-Scraper-API/actions/workflows/tests.yml/badge.svg)](https://github.com/GetSocialAPI/Facebook-Scraper-API/actions/workflows/tests.yml)
[![license](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org)

Python client for the **[GetSocialAPI](https://getsocialapi.com/)** Facebook Scraper API.

- Groups: resolve links, overview, paginated members
- Profiles: resolve links, About/contacts in raw GraphQL
- Connections: followers, followings, friends
- Raw responses — no transformations
- Automatic retries on 429/502/503, typed exceptions

## Installation

```bash
pip install git+https://github.com/GetSocialAPI/Facebook-Scraper-API.git
```

## Quickstart

```python
from getsocialapi_facebook import Client

# Get your API key at https://getsocialapi.com/dashboard/
client = Client(api_key="gsa_live_...")  # or set GETSOCIALAPI_FB_API_KEY

# Resolve any group link (slug, m.facebook, share/g) to a group_id
group = client.fb.resolve("https://www.facebook.com/groups/freegarden/")
group_id = group["group_id"]

# Profile links resolve the same way
user = client.fb.resolve_profile("https://www.facebook.com/nasa")
user_id = user["user_id"]

# Group card
client.fb.overview(group_id)

# Members: raw GraphQL pages (1st -> data.group, 2nd+ -> data.fetch__Group)
page = client.fb.members(group_id)  # fixed page of 15 members
page["data"]["group"]["group_member_profiles"]["page_info"]["end_cursor"]

# Next page: pass page_info.end_cursor as `after`
client.fb.members(group_id, after="AQHTm5Xq…")  # end_cursor from page_info
```

Base URL: `https://api.getsocialapi.com/fb` — authenticate with the API key
from your [dashboard](https://getsocialapi.com/dashboard/).

## Client

```python
Client(api_key=None, base_url="https://api.getsocialapi.com/fb", timeout=30, max_retries=3)
```

- `api_key` — your API key (env var `GETSOCIALAPI_FB_API_KEY` works too)

## Methods

| Method | Route | Description |
| --- | --- | --- |
| `resolve(url)` | `GET /resolve` | group link → `group_id` (numeric id, slug, m.facebook, `/share/g/…`) |
| `resolve_profile(url)` | `GET /resolve/profile` | profile link → `user_id` |
| `overview(group_id)` | `GET /overview` | group card: name, visibility |
| `members(group_id, after=None)` | `GET /api/v1/members` | raw GraphQL page of 15 (1st — `data.group`, 2nd+ — `data.fetch__Group`) |
| `group_posts(group_id, after=None)` | `GET /api/v1/group_posts` | group feed: page of 2–3 `Story` posts, cursor from `group_feed.page_info.end_cursor` |
| `contacts(user_id)` | `GET /api/v1/contacts` | profile About: raw GraphQL |
| `posts(user_id, after=None)` | `GET /api/v1/posts` | user timeline: page of ~100 posts (the fixed service maximum), cursor from `timeline_feed_units.page_info.end_cursor` |
| `feed(user_id=None, group_id=None, per_page=None, after=None)` | `GET /api/v1/feed` | unified user/group feed, small pages: `per_page` 3–20 (default 10) |
| `followers(user_id, after=None)` | `GET /api/v1/followers` | raw GraphQL `full_profile_list` |
| `followings(user_id, after=None)` | `GET /api/v1/followings` | same shape |
| `friends(user_id, after=None)` | `GET /api/v1/friends` | same shape |

Full request/response reference with live examples:
[getsocialapi.com/docs — API Reference / Facebook](https://getsocialapi.com/docs/api/facebook/resolve/).

### Pagination

Every method returns one raw page. Pass the connection's
`page_info.end_cursor` as `after` while `has_next_page` is true.

| List | Page size (fixed) | Cursor source |
| --- | --- | --- |
| `posts` | ~100 posts — the service maximum, there is no `count` parameter | `data.profile.timeline_feed_units.page_info.end_cursor` |
| `feed` | `per_page` 3–20 (default 10); a page may come back short — follow `has_next_page` | same connection as the target: `timeline_feed_units` / `group_feed` `page_info.end_cursor` |
| `group_posts` | 2–3 `Story` posts (skip `GroupsSectionHeaderUnit` edges, dedupe by `cache_id`) | `data.group_address.group_feed.page_info.end_cursor` |
| `members` | 15 | `data.(group / fetch__Group).group_member_profiles.page_info.end_cursor` |
| `followers` / `followings` / `friends` | 15 | `…list_items.page_info.end_cursor` |

Cursors are reusable and not bound to a session; a broken or foreign cursor
returns `400 Invalid Cursor` — take `end_cursor` only from the connection's
`page_info`, never from node fields.

```python
posts, after = [], None
while True:
    page = client.fb.posts(user_id, after=after)
    tfu = page["data"]["profile"]["timeline_feed_units"]
    posts += [e["node"] for e in tfu["edges"]]
    pi = tfu.get("page_info") or {}
    if not pi.get("has_next_page") or not pi.get("end_cursor"):
        break
    after = pi["end_cursor"]
```

### Response notes

- members page 1 lives in `data.group`, following pages in `data.fetch__Group`
- connection lists: `can_see_follower_list: false` means the list is hidden by
  privacy settings (only the count is available)

## Errors

| Exception | HTTP | Notes |
| --- | --- | --- |
| `GetSocialFacebookError` | — | base class; also network errors |
| `BadRequestError` | 400 | bad parameters |
| `APIKeyError` | 401 | invalid key |
| `RateLimitError` | 429 | `.limit` from the response |
| `UpstreamError` | 502 | temporary upstream error — retried automatically |
| `ServiceUnavailableError` | 503 | service overloaded — retried automatically |

Only successful responses count against your quota.
Plans and rate limits: [getsocialapi.com/#pricing](https://getsocialapi.com/#pricing).

## Support

- Telegram: [@getsocialapi](https://t.me/getsocialapi)
- Email: [hello@getsocialapi.com](mailto:hello@getsocialapi.com)
- Website: [getsocialapi.com](https://getsocialapi.com/)
- Documentation: [getsocialapi.com/docs](https://getsocialapi.com/docs/)
- Status: [getsocialapi.com/status](https://getsocialapi.com/status/)

## License

MIT
