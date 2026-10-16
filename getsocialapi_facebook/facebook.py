from urllib.parse import quote


def _quote(value):
    return quote(str(value), safe="")


def _digits(value, name, max_len=20):
    s = str(value)
    if not s.isdigit() or not 1 <= len(s) <= max_len:
        raise ValueError(f"{name} must be 1-{max_len} digits, got: {value!r}")
    return s


class FacebookAPI:
    """Facebook endpoints of GetSocialAPI (groups, profiles, connections)."""

    def __init__(self, transport):
        self._t = transport

    # ---------- Groups ----------

    def resolve(self, url):
        """Resolve a group link (numeric id, slug, m.facebook, share/g) to group_id."""
        s = str(url).strip()
        if not s:
            raise ValueError("url must not be empty")
        return self._t.request("GET", "/resolve", params={"url": s})

    def resolve_profile(self, url):
        """Resolve a profile link to a numeric user_id."""
        s = str(url).strip()
        if not s:
            raise ValueError("url must not be empty")
        return self._t.request("GET", "/resolve/profile", params={"url": s})

    def overview(self, group_id):
        """Group card: name, visibility, admins count. Upstream: FetchGroupMemberList."""
        return self._t.request("GET", "/overview", params={"group_id": _digits(group_id, "group_id")})

    def members(self, group_id, after=None):
        """Group members, raw Facebook GraphQL (one page of 15).

        Page 1 -> data.group, page 2+ -> data.fetch__Group. The page size is
        fixed by the service (15 edges); pass page_info.end_cursor as `after`
        while has_next_page is true to walk the list.
        """
        params = {"group_id": _digits(group_id, "group_id")}
        if after is not None:
            params["after"] = after
        return self._t.request("GET", "/api/v1/members", params=params)

    # ---------- Profile ----------

    def contacts(self, user_id, raw=True):
        """Profile About (contacts). Raw GraphQL by default, normalized with raw=False.

        Raw: the untouched GraphQL data payload. Normalized: {user_id, name,
        emails[], phones[], websites[], gender, about_sections,
        entries[{section, field_type, title, details, link}]}.
        """
        params = {"user_id": _digits(user_id, "user_id"), "raw": "1" if raw else "0"}
        return self._t.request("GET", "/api/v1/contacts", params=params)

    # ---------- Connections ----------

    def followers(self, user_id, after=None):
        """User followers. Raw GraphQL: data.full_profile_list.list_items."""
        return self._t.request("GET", "/api/v1/followers",
                               params=_conn(user_id, after))

    def followings(self, user_id, after=None):
        """User followings."""
        return self._t.request("GET", "/api/v1/followings",
                               params=_conn(user_id, after))

    def friends(self, user_id, after=None):
        """User friends."""
        return self._t.request("GET", "/api/v1/friends",
                               params=_conn(user_id, after))


def _conn(user_id, after):
    params = {"user_id": _digits(user_id, "user_id")}
    if after is not None:
        params["after"] = after
    return params

