#!/usr/bin/env python3
"""Fetch GitHub stats and render assets/github.svg.

Replaces the third-party github-readme-stats card, which rate-limits to an
error image unless you host your own instance with a PAT. Self-hosted means
the card is as reliable as the workflow itself.

Needs a token in GITHUB_TOKEN (the workflow's built-in one is enough - only
public data is read). Locally: export GITHUB_TOKEN=$(gh auth token)

Usage:
    python3 scripts/make_github_card.py [--user maziyarpanahi] [--out assets/github.svg]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

# Same palette as make_header.py so the two cards read as one set.
INK = "#f5ece1"
MUTED = "#cbbdad"
GOLD = "#f7ddb4"
RULE = "#4a3c31"

FONT = (
    "'Public Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', "
    "Roboto, Helvetica, Arial, sans-serif"
)

WIDTH, HEIGHT = 500, 195

QUERY = """
query($login:String!){
  user(login:$login){
    followers{ totalCount }
    repositories(first:100, ownerAffiliations:OWNER, isFork:false, privacy:PUBLIC){
      totalCount
      nodes{ stargazerCount }
    }
    contributionsCollection{
      totalCommitContributions
      totalPullRequestContributions
      contributionCalendar{ totalContributions }
    }
  }
}
"""


def comma(n: int) -> str:
    return f"{n:,}"


def fetch(user: str) -> dict:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit(
            "error: GITHUB_TOKEN is not set.\n"
            "  locally: export GITHUB_TOKEN=$(gh auth token)"
        )

    body = json.dumps({"query": QUERY, "variables": {"login": user}}).encode()
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "maziyarpanahi-profile-bot/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        raise SystemExit(f"GitHub API {error.code}: {error.read().decode('utf-8')[:300]}")

    if "errors" in payload:
        raise SystemExit(f"GitHub GraphQL error: {payload['errors']}")

    node = payload["data"]["user"]
    contributions = node["contributionsCollection"]
    return {
        "stars": sum(r["stargazerCount"] for r in node["repositories"]["nodes"]),
        "repos": node["repositories"]["totalCount"],
        "followers": node["followers"]["totalCount"],
        "commits_year": contributions["totalCommitContributions"],
        "prs_year": contributions["totalPullRequestContributions"],
        "contributions_year": contributions["contributionCalendar"]["totalContributions"],
    }


def build(stats: dict) -> str:
    cells = [
        (comma(stats["stars"]), "STARS EARNED"),
        (comma(stats["contributions_year"]), "CONTRIBUTIONS · 1Y"),
        (comma(stats["commits_year"]), "COMMITS · 1Y"),
        (comma(stats["prs_year"]), "PULL REQUESTS · 1Y"),
    ]
    columns = [28, 268]
    rows = [(96, 116), (156, 176)]

    markup = []
    for index, (value, label) in enumerate(cells):
        x = columns[index % 2]
        value_y, label_y = rows[index // 2]
        markup.append(
            f'    <text class="v" x="{x}" y="{value_y}">{escape(value)}</text>\n'
            f'    <text class="l" x="{x}" y="{label_y}">{escape(label)}</text>'
        )

    label_text = (
        f"GitHub: {comma(stats['stars'])} stars earned, "
        f"{comma(stats['contributions_year'])} contributions in the last year."
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}"
     width="{WIDTH}" height="{HEIGHT}" role="img" aria-label="{escape(label_text)}">
  <title>{escape(label_text)}</title>
  <defs>
    <linearGradient id="gh-bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#1d1714"/>
      <stop offset="100%" stop-color="#171210"/>
    </linearGradient>
    <clipPath id="gh-card">
      <rect x="0" y="0" width="{WIDTH}" height="{HEIGHT}" rx="12"/>
    </clipPath>
  </defs>

  <style><![CDATA[
    .h {{ font: 700 13px {FONT}; fill: {GOLD}; letter-spacing: 2px; }}
    .v {{ font: 700 30px {FONT}; fill: {INK}; }}
    .l {{ font: 600 11px {FONT}; fill: {MUTED}; letter-spacing: 1.3px; }}
    /* No animation anywhere: GitHub renders SVG-in-<img> as a static frame. */
  ]]></style>

  <g clip-path="url(#gh-card)">
    <rect x="0" y="0" width="{WIDTH}" height="{HEIGHT}" fill="url(#gh-bg)"/>
    <text class="h" x="28" y="40">GITHUB</text>
    <rect x="28" y="52" width="40" height="2" rx="1" fill="{GOLD}"/>
{chr(10).join(markup)}
  </g>
  <rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="12"
        fill="none" stroke="{RULE}" stroke-width="1"/>
</svg>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--user", default="maziyarpanahi")
    parser.add_argument("--out", default="assets/github.svg")
    parser.add_argument("--metrics", default="metrics/github.json")
    args = parser.parse_args()

    stats = fetch(args.user)

    metrics = Path(args.metrics)
    metrics.parent.mkdir(parents=True, exist_ok=True)
    metrics.write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(stats), encoding="utf-8")

    print(
        f"wrote {out}: {comma(stats['stars'])} stars, "
        f"{comma(stats['contributions_year'])} contributions/1y",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
