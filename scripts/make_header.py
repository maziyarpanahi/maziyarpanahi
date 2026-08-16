#!/usr/bin/env python3
"""Render assets/header.svg from metrics/hf.json.

The banner is self-hosted (no third-party image service) and paints its own
background, so it looks identical in GitHub's light and dark themes.

Usage:
    python3 scripts/make_header.py [--metrics metrics/hf.json] [--out assets/header.svg]
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

# Warm palette lifted from site/assets/styles.css so the banner and
# maziyarpanahi.com read as the same brand.
INK = "#f5ece1"
MUTED = "#cbbdad"
GOLD = "#f7ddb4"
RULE = "#4a3c31"

NAME = "Maziyar Panahi"
ROLE = "Building on-device Medical AI"
TAGLINE = "Open, sovereign, deployable medical AI"

FONT = (
    "'Public Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', "
    "Roboto, Helvetica, Arial, sans-serif"
)

WIDTH, HEIGHT = 1200, 300


def ecg_path(y: float, start: float, end: float, step: float = 120.0) -> str:
    """A repeating heartbeat trace - a nod to the health-AI work.

    The spike reaches 24px above the baseline and dips 16px below it, so the
    trace lives entirely within y-24 .. y+16. Keep that band clear of text.
    """
    d = [f"M {start:.0f} {y:.0f}"]
    x = start
    while x < end:
        # flat line, then the QRS complex, then flat again
        d.append(f"H {x + step * 0.42:.0f}")
        d.append(f"l {step * 0.06:.0f} -24")
        d.append(f"l {step * 0.07:.0f} 40")
        d.append(f"l {step * 0.06:.0f} -16")
        x += step
    d.append(f"H {end:.0f}")
    return " ".join(d)


def build(data: dict) -> str:
    display = data["display"]
    stats = [
        (display["models"], "MODELS"),
        (display["downloads_all_time"], "DOWNLOADS · ALL TIME"),
        (display["followers"], "FOLLOWERS"),
    ]
    # Three evenly spaced, centre-anchored columns - no box-fitting to get wrong
    # when font metrics differ between machines. Shifted left of the earlier
    # layout to keep the widest label, DOWNLOADS · ALL TIME, off its neighbour.
    centres = [808, 968, 1108]

    updated = data.get("updated_at", "")
    try:
        stamp = datetime.strptime(updated, "%Y-%m-%dT%H:%M:%SZ").strftime("%d %b %Y")
    except ValueError:
        stamp = updated

    stat_markup = []
    for (value, label), cx in zip(stats, centres):
        stat_markup.append(
            f'    <text class="stat-value" x="{cx}" y="142" text-anchor="middle">{escape(value)}</text>\n'
            f'    <text class="stat-label" x="{cx}" y="170" text-anchor="middle">{escape(label)}</text>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}"
     width="{WIDTH}" height="{HEIGHT}" role="img"
     aria-label="{escape(NAME)} - {escape(ROLE)}. {escape(display['models'])} models, {escape(display['downloads_all_time'])} downloads all time, {escape(display['followers'])} followers on Hugging Face.">
  <title>{escape(NAME)} - {escape(ROLE)}</title>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#1d1714"/>
      <stop offset="55%" stop-color="#171210"/>
      <stop offset="100%" stop-color="#221a14"/>
    </linearGradient>
    <linearGradient id="glow" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{GOLD}" stop-opacity="0"/>
      <stop offset="45%" stop-color="{GOLD}" stop-opacity="0.55"/>
      <stop offset="100%" stop-color="{GOLD}" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="card">
      <rect x="0" y="0" width="{WIDTH}" height="{HEIGHT}" rx="20"/>
    </clipPath>
  </defs>

  <style><![CDATA[
    .name   {{ font: 700 54px {FONT}; fill: {INK}; letter-spacing: -0.5px; }}
    .role   {{ font: 400 22px {FONT}; fill: {MUTED}; }}
    .tag    {{ font: 500 15px {FONT}; fill: {GOLD}; letter-spacing: 0.6px; }}
    .stat-value {{ font: 700 40px {FONT}; fill: {INK}; }}
    .stat-label {{ font: 600 11px {FONT}; fill: {MUTED}; letter-spacing: 1.2px; }}
    .section {{ font: 700 12px {FONT}; fill: {GOLD}; letter-spacing: 2.2px; }}
    .stamp  {{ font: 400 12px {FONT}; fill: {MUTED}; opacity: 0.65; }}

    /* Everything above is visible with no animation involved. Motion is only
       ever additive: several renderers (GitHub's image proxy among them) draw
       SVG-in-<img> as a static frame and never tick the animation clock, so
       nothing may depend on a keyframe running to become visible. */
    .ecg {{ animation: pulse 4s ease-in-out infinite; }}

    @keyframes pulse {{
      0%, 100% {{ stroke-opacity: 0.22; }}
      50%      {{ stroke-opacity: 0.40; }}
    }}

    @media (prefers-reduced-motion: reduce) {{
      .ecg {{ animation: none; }}
    }}
  ]]></style>

  <g clip-path="url(#card)">
    <rect x="0" y="0" width="{WIDTH}" height="{HEIGHT}" fill="url(#bg)"/>

    <!-- heartbeat trace across the lower third; band is y 238..278 -->
    <path class="ecg" d="{ecg_path(262, -20, WIDTH + 20)}"
          fill="none" stroke="{GOLD}" stroke-opacity="0.28"
          stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>
    <rect x="0" y="{HEIGHT - 3}" width="{WIDTH}" height="3" fill="url(#glow)"/>

    <text class="name" x="60" y="118">{escape(NAME)}</text>
    <!-- clears the descender on the 'y' in Maziyar -->
    <rect x="62" y="146" width="54" height="3" rx="1.5" fill="{GOLD}"/>
    <text class="role" x="60" y="176">{escape(ROLE)}</text>
    <text class="tag" x="60" y="212">{escape(TAGLINE)}</text>

    <line x1="740" y1="62" x2="740" y2="186" stroke="{RULE}" stroke-width="1"/>
    <text class="section" x="770" y="84">HUGGING FACE</text>
    <g>
{chr(10).join(stat_markup)}
    </g>

    <!-- tucked under the stats, above the heartbeat band -->
    <text class="stamp" x="{WIDTH - 60}" y="212" text-anchor="end">updated {escape(stamp)}</text>
  </g>
  <rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="20"
        fill="none" stroke="{RULE}" stroke-width="1"/>
</svg>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics", default="metrics/hf.json")
    parser.add_argument("--out", default="assets/header.svg")
    args = parser.parse_args()

    data = json.loads(Path(args.metrics).read_text(encoding="utf-8"))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(data), encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
