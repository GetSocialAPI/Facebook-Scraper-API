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

    def group_posts(self, group_id, after=None):
        """Group feed posts, raw GroupFeedCsrQuery payload (2-3 posts/page).

        Story-shaped posts (creation_time, message.text, actors,
        attachments) — same node schema as the user timeline; skip
        GroupsSectionHeaderUnit edges. Take the cursor from
        data.group_address.group_feed.page_info.end_cursor and pass it
        back as `after` while has_next_page is true. Post visibility in
        closed groups depends on the scraper token's membership.
        """
        params = {"group_id": _digits(group_id, "group_id")}
        if after is not None:
            params["after"] = after
        return self._t.request("GET", "/api/v1/group_posts", params=params)

    # ---------- Profile ----------

    def contacts(self, user_id):
        """Profile About (contacts) — the untouched Facebook GraphQL payload.

        Walk data.user.profile_intro_card: each About section is a connection
        with edges[].node; `field_type` describes the entry kind (email,
        phone, gender, employer, ...), linked entities are full node objects.
        """
        return self._t.request("GET", "/api/v1/contacts",
                               params={"user_id": _digits(user_id, "user_id")})

    def posts(self, user_id, after=None):
        """User timeline posts, raw Facebook GraphQL (one page of ~100).

        data.profile.timeline_feed_units.edges[] holds Story nodes;
        take the cursor from timeline_feed_units.page_info.end_cursor
        and pass it back as `after` while has_next_page is true. The
        cursor is a ~888-char base64 string — pass it verbatim (the
        transport URL-encodes it). Cursors are reusable and not bound
        to a session. Use only the page_info cursor — end_cursor values
        inside node attachments are impostors and yield Invalid Cursor.
        """
        return self._t.request("GET", "/api/v1/posts", params=_conn(user_id, after))

    def feed(self, user_id=None, group_id=None, per_page=None, after=None):
        """GET /api/v1/feed — unified user/group feed, small pages.

        Pass exactly one of `user_id` / `group_id`. Page size is
        `per_page` (integer 3-20, default 10); a page may come back
        short — follow has_next_page instead of counting posts.

        user: `data.profile.timeline_feed_units` (~10 Story nodes;
        Facebook may return slightly more — the service does not trim,
        trimming would lose posts at page seams).
        group: `data.group_address.group_feed` (Facebook caps its own
        page at ~2 posts; the service stitches several FB pages up to
        per_page — up to 2 duplicate edges are possible at the seam,
        dedupe by node.cache_id).

        Cursor: page_info.end_cursor of the respective connection,
        passed back as `after` while has_next_page is true. A broken
        cursor raises BadRequestError (400 Invalid Cursor).
        """
        if (user_id is None) == (group_id is None):
            raise ValueError("pass exactly one of user_id or group_id")
        params = {}
        if user_id is not None:
            params["user_id"] = _digits(user_id, "user_id")
        else:
            params["group_id"] = _digits(group_id, "group_id")
        if per_page is not None:
            if isinstance(per_page, bool) or not isinstance(per_page, int) \
                    or not 3 <= per_page <= 20:
                raise ValueError(f"per_page must be an integer 3-20, "
                                 f"got: {per_page!r}")
            params["per_page"] = per_page
        if after is not None:
            params["after"] = after
        return self._t.request("GET", "/api/v1/feed", params=params)

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

