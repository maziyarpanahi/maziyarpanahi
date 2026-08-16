#!/usr/bin/env python3
"""Fetch Hugging Face Hub stats for a user and write them to metrics/hf.json.

Standard library only - no pip install needed in CI.

Usage:
    python3 scripts/fetch_hf_stats.py [--user MaziyarPanahi] [--out metrics/hf.json]

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
    """Grouped form for countable things: 2816 -> '2,816'. Reads better than 2.8K."""
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
            with urllib.request.urlopen(request, timeout=60) as response:
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


def collect(kind: str, user: str) -> list[dict]:
    """Walk every page of /api/{kind}?author={user} and return the raw records."""
    url = f"{API}/{kind}?author={user}&limit=1000&sort=downloads&direction=-1"
    items: list[dict] = []
    page = 1
    while url:
        payload, headers = get(url)
        items.extend(payload)
        print(f"  {kind}: page {page} -> {len(items)} total", file=sys.stderr)
        url = next_page(headers)
        page += 1
    return items


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--user", default="MaziyarPanahi")
    parser.add_argument("--out", default="metrics/hf.json")
    args = parser.parse_args()

    print(f"fetching Hugging Face stats for {args.user}", file=sys.stderr)
    overview, _ = get(f"{API}/users/{args.user}/overview")

    models = collect("models", args.user)
    datasets = collect("datasets", args.user)

    model_downloads = sum(item.get("downloads") or 0 for item in models)
    dataset_downloads = sum(item.get("downloads") or 0 for item in datasets)
    downloads = model_downloads + dataset_downloads

    totals = {
        "models": overview.get("numModels", len(models)),
        "datasets": overview.get("numDatasets", len(datasets)),
        "spaces": overview.get("numSpaces", 0),
        "papers": overview.get("numPapers", 0),
        "likes": overview.get("numLikes", 0),
        "followers": overview.get("numFollowers", 0),
        "model_downloads_30d": model_downloads,
        "dataset_downloads_30d": dataset_downloads,
        "downloads_30d": downloads,
    }

    top_models = [
        {
            "id": item["id"],
            "name": item["id"].split("/", 1)[-1],
            "url": f"https://huggingface.co/{item['id']}",
            "downloads": item.get("downloads") or 0,
            "downloads_display": human(item.get("downloads") or 0),
            "likes": item.get("likes") or 0,
        }
        for item in sorted(models, key=lambda m: m.get("downloads") or 0, reverse=True)[:TOP_N]
    ]

    # Downloads get the compact treatment; everything countable keeps its digits.
    compact = {"model_downloads_30d", "dataset_downloads_30d", "downloads_30d"}
    display = {
        key: human(value) if key in compact else comma(value)
        for key, value in totals.items()
    }

    data = {
        "user": args.user,
        "profile_url": f"https://huggingface.co/{args.user}",
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "totals": totals,
        "display": display,
        "top_models": top_models,
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(
        f"wrote {out}: {totals['models']} models, {totals['datasets']} datasets, "
        f"{human(downloads)} downloads/30d, {totals['followers']} followers",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
