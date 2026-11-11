# Facebook Scraper API

Get Facebook group and profile data using GetSocialAPI on Apify. The Actor
resolves Facebook URLs and retrieves group members, posts, feeds, and profile
connections where the upstream API provides them.

**No Facebook account or Facebook session cookies are required.**

## Quick start

Resolve a group URL to its numeric ID:

```json
{"operation": "resolve_group", "target": "https://www.facebook.com/groups/freegarden/"}
```

Use the returned `data.group_id` to retrieve the first page of group members:

```json
{"operation": "group_members", "target": "123456789"}
```

Replace `123456789` with the actual group ID.

## Operations

| Target | Operations |
| --- | --- |
| Full Facebook URL | `resolve_group`, `resolve_profile` |
| Numeric group ID | `group_overview`, `group_members`, `group_posts`, `group_feed` |
| Numeric profile ID | `profile_about`, `profile_posts`, `profile_feed`, `followers`, `following`, `friends` |

The Actor writes one Dataset row per returned API response, with `operation`,
`target`, and the raw payload in `data`. Paginated calls return one page at a
time. If the connection exposes `page_info.has_next_page`, pass its
`page_info.end_cursor` as `after` in the next run. The response path depends
on the operation. `per_page` applies to the two feed operations and accepts
values from 3 to 20. See the [GetSocialAPI documentation](https://getsocialapi.com/docs/)
for response fields and availability.
