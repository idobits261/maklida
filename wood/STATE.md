# woodshmood — state

## Baseline (26.11.2026, before automation)
Followers 31 · Likes 119 · ~15 manual carousel posts, best 1,919 views.
Goal: compare followers on 26.12.2026.

## Counters
- Next post number: 002
- Next Mistake #: 1
- Last series used: build (001)
- Weekly "5 Projects" post: Sundays, first slot

## Pending (rendered, not yet scheduled)
- (none)

## Used (never repeat)
- Projects: cedar planter box (001)
- Mistakes: —
- Tricks: —

## Log
- 26.11.2026: pipeline set up. 001-planter rendered (sample approved by Ido). Waiting for BUFFER_WOOD_KEY.
- 25.11.2026 (test run): `buffer_post.py channels` → HTTP 401 UNAUTHENTICATED ("An authentication JWT or Access Token is required"). The api.buffer.com Network secret was not injected by the proxy and BUFFER_WOOD_KEY is unset. 001-planter NOT scheduled — kept in Pending.
- 26.11.2026 (publish-now run): `buffer_post.py channels` → HTTP 401 UNAUTHENTICATED ("An authentication JWT or Access Token is required"), same with a direct curl to api.buffer.com. Network secret still not injected; BUFFER_WOOD_KEY unset. `env | grep -ci proxy` = 26, CLAUDE_CODE_REMOTE_ENVIRONMENT_TYPE = cloud_default. 001-planter NOT published — kept in Pending.
- 26.11.2026 (publish-now run #2): `buffer_post.py channels` → HTTP 401 UNAUTHENTICATED ("An authentication JWT or Access Token is required"); direct curl same. Proxy did not inject the api.buffer.com Network secret; BUFFER_WOOD_KEY unset. `env | grep -ci proxy` = 26, CLAUDE_CODE_REMOTE_ENVIRONMENT_TYPE = cloud_default (scheduled runs use the default environment, which likely lacks the secret). 001-planter NOT published — kept in Pending.
- 26.11.2026 10:39: posting moved to the GitHub Action queue (repo secret). 001-planter sent to Buffer via the Action (exit=0, status sending) → TikTok.
