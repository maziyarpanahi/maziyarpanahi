#!/usr/bin/env python3
"""Fetch Hugging Face Hub stats and write them to metrics/hf.json.

Figures are the COMBINED total across every account in ACCOUNTS - the personal
account and the OpenMed org - because the models are authored by the same
person. Downloads are reported all-time, not the API's rolling 30-day window.

Standard library only - no pip install needed in CI.

Usage:
    python3 scripts/fetch_hf_stats.py [--out metrics/hf.json]

Set HF_TOKEN in the environment for higher rate limits. Only public data is
read, so the token is optional.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://huggingface.co/api"
USER_AGENT = "maziyarpanahi-profile-bot/1.0 (+https://github.com/maziyarpanahi)"
TOP_N = 6

# (name, kind) - kind picks the overview endpoint: users/ or organizations/.
ACCOUNTS = [
    ("MaziyarPanahi", "users"),
    ("OpenMed", "organizations"),
]
# Followers are a property of the person, not of the combined body of work, so
# this one figure comes from the personal account alone.
PRIMARY = "MaziyarPanahi"


def human(n: int) -> str:
    """Compact form for big figures: 1234567 -> '1.2M'. Used for downloads."""
    for limit, suffix in ((1_000_000_000, "B"), (1_000_000, "M"), (1_000, "K")):
        if n >= limit:
            value = n / limit
            if value >= 100:
                # 254M, not 254.0M.
                return f"{value:.0f}{suffix}"
            # 1.2M, but 20M rather than 20.0M.
            return f"{value:.1f}".removesuffix(".0") + suffix
    return str(n)


def comma(n: int) -> str:
    """Grouped form for countable things: 5087 -> '5,087'. Reads better than 5.1K."""
    return f"{n:,}"


def get(url: str, retries: int = 4):
    """GET a JSON endpoint, returning (payload, response_headers)."""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    token = os.environ.get("HF_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    last_error = None
    for attempt in range(retries):
        try:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=90) as response:
                return json.loads(response.read().decode("utf-8")), response.headers
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as error:
            last_error = error
            if attempt < retries - 1:
                backoff = 2 ** attempt
                print(f"  retry {attempt + 1}/{retries - 1} in {backoff}s ({error})", file=sys.stderr)
                time.sleep(backoff)
    raise SystemExit(f"giving up on {url}: {last_error}")


def next_page(headers) -> str | None:
    """Pull the rel=next URL out of a Link header, if there is one."""
    link = headers.get("Link")
    if not link:
        return None
    match = re.search(r'<([^>]+)>;\s*rel="next"', link)
    return match.group(1) if match else None


def collect(kind: str, author: str) -> list[dict]:
    """Walk every page of /api/{kind}?author={author} and return the raw records.

    expand[] is what makes downloadsAllTime available; without it the API only
    returns the rolling 30-day `downloads` field.
    """
    url = (
        f"{API}/{kind}?author={author}&limit=1000&sort=downloads&direction=-1"
        "&expand[]=downloads&expand[]=downloadsAllTime&expand[]=likes"
    )
    items: list[dict] = []
    page = 1
    while url:
        payload, headers = get(url)
        items.extend(payload)
        print(f"  {author}/{kind}: page {page} -> {len(items)}", file=sys.stderr)
        url = next_page(headers)
        page += 1
    return items


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="metrics/hf.json")
    args = parser.parse_args()

    all_models: list[dict] = []
    all_datasets: list[dict] = []
    likes = 0
    followers = 0
    per_account = {}

    for name, endpoint in ACCOUNTS:
        print(f"fetching {name}", file=sys.stderr)
        overview, _ = get(f"{API}/{endpoint}/{name}/overview")
        models = collect("models", name)
        datasets = collect("datasets", name)

        all_models.extend(models)
        all_datasets.extend(datasets)
        likes += overview.get("numLikes") or 0
        if name == PRIMARY:
            followers = overview.get("numFollowers") or 0

        per_account[name] = {
            "models": len(models),
            "datasets": len(datasets),
            "downloads_all_time": sum(m.get("downloadsAllTime") or 0 for m in models)
            + sum(d.get("downloadsAllTime") or 0 for d in datasets),
            "downloads_30d": sum(m.get("downloads") or 0 for m in models)
            + sum(d.get("downloads") or 0 for d in datasets),
        }

    downloads_all_time = sum(a["downloads_all_time"] for a in per_account.values())
    downloads_30d = sum(a["downloads_30d"] for a in per_account.values())

    totals = {
        "models": len(all_models),
        "datasets": len(all_datasets),
        "downloads_all_time": downloads_all_time,
        "downloads_30d": downloads_30d,
        "likes": likes,
        "followers": followers,
    }

    top_models = [
        {
            "id": item["id"],
            "name": item["id"].split("/", 1)[-1],
            "owner": item["id"].split("/", 1)[0],
            "url": f"https://huggingface.co/{item['id']}",
            "downloads_all_time": item.get("downloadsAllTime") or 0,
            "downloads_display": human(item.get("downloadsAllTime") or 0),
            "likes": item.get("likes") or 0,
        }
        for item in sorted(
            all_models, key=lambda m: m.get("downloadsAllTime") or 0, reverse=True
        )[:TOP_N]
    ]

    # Downloads get the compact treatment; everything countable keeps its digits.
    compact = {"downloads_all_time", "downloads_30d"}
    display = {
        key: human(value) if key in compact else comma(value)
        for key, value in totals.items()
    }

    data = {
        "accounts": [name for name, _ in ACCOUNTS],
        "profile_url": f"https://huggingface.co/{PRIMARY}",
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "totals": totals,
        "display": display,
        "per_account": per_account,
        "top_models": top_models,
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(
        f"wrote {out}: {comma(totals['models'])} models across "
        f"{len(ACCOUNTS)} accounts, {human(downloads_all_time)} downloads all-time",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
