import asyncio
from urllib.parse import urlsplit

from apify import Actor
from getsocialapi_facebook import Client, GetSocialFacebookError


# Operation name, SDK method, target parameter, and accepted options.
OPERATIONS = {
    "resolve_group": ("resolve", "url", ()),
    "resolve_profile": ("resolve_profile", "url", ()),
    "group_overview": ("overview", "group_id", ()),
    "group_members": ("members", "group_id", ("after",)),
    "group_posts": ("group_posts", "group_id", ("after",)),
    "profile_about": ("contacts", "user_id", ()),
    "profile_posts": ("posts", "user_id", ("after",)),
    "profile_feed": ("feed", "user_id", ("after", "per_page")),
    "group_feed": ("feed", "group_id", ("after", "per_page")),
    "followers": ("followers", "user_id", ("after",)),
    "following": ("followings", "user_id", ("after",)),
    "friends": ("friends", "user_id", ("after",)),
}


def parse_input(actor_input):
    operation = actor_input.get("operation", "resolve_group")
    if not isinstance(operation, str) or operation not in OPERATIONS:
        raise ValueError("Choose a supported operation from the Actor input form.")

    target = actor_input.get("target")
    if not isinstance(target, str) or not target.strip():
        raise ValueError("Provide a Facebook URL or numeric ID in Target.")
    target = target.strip()

    method, target_parameter, supported = OPERATIONS[operation]
    if target_parameter == "url":
        url = urlsplit(target)
        host = url.hostname or ""
        if (
            url.scheme not in ("https", "http")
            or url.username is not None
            or (host != "facebook.com" and not host.endswith(".facebook.com"))
        ):
            raise ValueError("Provide a full URL on facebook.com.")
    options = {
        name: actor_input[name]
        for name in ("after", "per_page")
        if actor_input.get(name) is not None
    }
    if options.keys() - set(supported):
        raise ValueError(f"Unsupported pagination options for {operation}.")

    return operation, method, target, {target_parameter: target, **options}


async def main():
    async with Actor:
        operation, method, target, options = parse_input(await Actor.get_input() or {})
        request = getattr(Client().facebook, method)
        try:
            data = await asyncio.to_thread(request, **options)
        except GetSocialFacebookError as error:
            status = getattr(error.response, "status_code", None)
            detail = f"HTTP {status}" if status is not None else type(error).__name__
            raise RuntimeError(f"GetSocialAPI request failed for {operation}: {detail}") from None

        await Actor.push_data({"operation": operation, "target": target, "data": data})


if __name__ == "__main__":
    asyncio.run(main())
