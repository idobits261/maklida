#!/usr/bin/env python3
"""Post woodshmood videos through the SECOND Buffer account's GraphQL API.

Auth: Network secret for api.buffer.com in the cloud environment (proxy injects it). Never commit a key.

  python3 buffer_post.py channels
  python3 buffer_post.py post <post_json> <video_url> <dueAt ISO with offset>
"""
import json, os, sys, urllib.request

API = "https://api.buffer.com"


class Enum(str):
    pass


def lit(v):
    if isinstance(v, Enum):
        return str(v)
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, list):
        return "[" + ", ".join(lit(x) for x in v) + "]"
    if isinstance(v, dict):
        return "{" + ", ".join(f"{k}: {lit(x)}" for k, x in v.items()) + "}"
    raise TypeError(v)


def gql(query):
    # The key is a "Network secret" in the cloud environment: the proxy adds the Authorization header
    # for api.buffer.com, so the code never sees it. BUFFER_WOOD_KEY is only a local fallback.
    headers = {"Content-Type": "application/json"}
    if os.environ.get("BUFFER_WOOD_KEY"):
        headers["Authorization"] = "Bearer " + os.environ["BUFFER_WOOD_KEY"]
    req = urllib.request.Request(API, data=json.dumps({"query": query}).encode(), headers=headers)
    with urllib.request.urlopen(req, timeout=60) as r:
        out = json.load(r)
    if out.get("errors"):
        raise RuntimeError(json.dumps(out["errors"], ensure_ascii=False))
    return out["data"]


def channels():
    orgs = gql("query { account { organizations { id name } } }")["account"]["organizations"]
    res = []
    for o in orgs:
        q = 'query { channels(input: {organizationId: %s}) { id name service } }' % json.dumps(o["id"])
        for c in gql(q)["channels"]:
            c["org"] = o["id"]
            res.append(c)
    return res


def post(spec_path, video_url, due_at):
    spec = json.load(open(spec_path))
    caption = spec["caption"]
    results = []
    for ch in channels():
        svc = ch["service"]
        inp = {"text": caption, "channelId": ch["id"], "schedulingType": Enum("automatic"),
               "mode": Enum("customScheduled"), "dueAt": due_at,
               "assets": [{"video": {"url": video_url, "metadata": {"thumbnailOffset": 500}}}]}
        if svc == "tiktok":
            inp["metadata"] = {"tiktok": {"title": spec.get("title", spec["slides"][0].get("title", ""))[:90]}}
        elif svc == "instagram":
            inp["metadata"] = {"instagram": {"type": Enum("reel"), "shouldShareToFeed": True}}
        elif svc == "youtube":
            title = (spec.get("title") or spec["slides"][0].get("title", "Woodworking")) + " #shorts"
            inp["metadata"] = {"youtube": {"type": Enum("short"), "title": title[:95], "categoryId": "26"}}
        else:
            results.append((svc, "skipped"))
            continue
        q = ("mutation { createPost(input: %s) { ... on PostActionSuccess { post { id status dueAt } } "
             "... on MutationError { message } } }") % lit(inp)
        r = gql(q)["createPost"]
        results.append((svc, r))
    print(json.dumps(results, ensure_ascii=False, indent=1))
    bad = [x for x in results if isinstance(x[1], dict) and "message" in x[1]]
    if bad:
        sys.exit(1)


if __name__ == "__main__":
    if sys.argv[1] == "channels":
        print(json.dumps(channels(), indent=1, ensure_ascii=False))
    elif sys.argv[1] == "post":
        post(sys.argv[2], sys.argv[3], sys.argv[4])
