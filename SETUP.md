# How this profile is built

The README is part hand-written, part generated. This note explains which is
which, so future-you edits the right file.

## Layout

| Path | Generated? | What it is |
| --- | --- | --- |
| `README.md` | partly | Hand-written, except the block between the `HF-STATS` markers |
| `assets/header.svg` | yes | The banner, rebuilt from the live numbers |
| `assets/github.svg` | yes | The GitHub stats card |
| `metrics/hf.json` | yes | Raw Hugging Face figures, refreshed daily |
| `metrics/github.json` | yes | Raw GitHub figures |
| `scripts/fetch_hf_stats.py` | no | Hugging Face Hub API → `metrics/hf.json` |
| `scripts/make_header.py` | no | `metrics/hf.json` → `assets/header.svg` |
| `scripts/render_readme.py` | no | `metrics/hf.json` → the README stats block |
| `scripts/make_github_card.py` | no | GitHub GraphQL API → `assets/github.svg` |
| `.github/workflows/profile.yml` | no | Runs the four scripts daily, plus the snake |

## What the numbers count

Hugging Face figures are the **combined total across both accounts** —
[MaziyarPanahi](https://huggingface.co/MaziyarPanahi) (2,816 models) and the
[OpenMed](https://huggingface.co/OpenMed) org (2,271 models) — because the same
person authored all of them. To add or drop an account, edit `ACCOUNTS` at the
top of `scripts/fetch_hf_stats.py`; everything downstream follows.

Downloads are reported **all time**, not the API's default rolling 30-day
window. The Hub only exposes those two windows — there is no "last 12 months"
figure to read — so all-time is the honest cumulative number. It needs
`expand[]=downloadsAllTime` on the request; without that the API returns the
30-day count only. Both are stored in `metrics/hf.json` if you want to switch.

Followers come from the personal account alone, since that is a property of the
person rather than of the combined body of work.

Everything between these two markers in `README.md` is overwritten on every run —
don't hand-edit it:

```
<!-- HF-STATS:START -->
<!-- HF-STATS:END -->
```

Anything outside the markers is yours and is never touched.

## Running it by hand

The scripts are standard library only — no `pip install`, no `node_modules`.

```bash
export GITHUB_TOKEN=$(gh auth token)
python3 scripts/fetch_hf_stats.py && python3 scripts/make_header.py && python3 scripts/render_readme.py && python3 scripts/make_github_card.py
```

Only `make_github_card.py` needs the token, and only to read public data. In CI
the workflow's built-in `GITHUB_TOKEN` covers it with no setup.

To check whether the README is stale without rewriting it (exits non-zero if so):

```bash
python3 scripts/render_readme.py --check
```

### macOS certificate error

If `fetch_hf_stats.py` fails locally with `CERTIFICATE_VERIFY_FAILED`, that's the
python.org installer not wiring up a CA bundle. Point Python at one:

```bash
export SSL_CERT_FILE=$(python3 -c "import certifi; print(certifi.where())")
```

CI is unaffected — only local macOS runs hit this.

## The workflow

`profile.yml` runs daily at 04:17 UTC, on demand via *Actions → Profile → Run
workflow*, and whenever `scripts/**` changes on `main`. Two independent jobs:

**`stats`** — fetches the numbers, rebuilds the banner and the README block, and
commits only if something actually changed.

**`snake`** — renders the contribution-graph snake and force-pushes the two SVGs
to a branch called `output`. The README points at that branch via raw.githubusercontent.com.

### Things worth knowing

- **The `output` branch is expected.** It holds nothing but the two snake SVGs
  and is rewritten on every run. Don't merge it, don't delete it.
- **The snake is a broken image until the workflow runs once.** That's normal on
  a fresh setup and fixes itself after the first successful run.
- **`Settings → Actions → General → Workflow permissions` must be
  "Read and write permissions"** — already enabled here. Without it the commit
  and the `output` push both fail with a 403.
- **The daily commit does not redeploy the website.** Commits pushed with the
  built-in `GITHUB_TOKEN` deliberately don't trigger other workflows, so
  `deploy-pages.yml` stays put. The site only rebuilds when you change `site/`
  yourself.
- **GitHub pauses cron on idle repos.** If the repo sees no pushes for 60 days
  the schedule is suspended until you visit Actions and re-enable it. The daily
  self-commit normally keeps it alive on its own.
- **`HF_TOKEN` is optional.** Everything read is public; a token in
  *Settings → Secrets → Actions* only buys a higher rate limit.

## Third-party images in the README

The banner and the Hugging Face figures are ours. Four images are not, and each
is a service that can disappear without warning:

| Image | Host |
| --- | --- |
| Banner and GitHub stats card | ours, in `assets/` |
| Contribution streak | `streak-stats.demolab.com` |
| Rank in France | `user-badge.committers.top` |
| Snake | our own `output` branch |

The GitHub stats card was self-hosted on 16 August 2026. It used to come from
`github-readme-stats-sigma-five.vercel.app`, which answers with a
*"Maximum retries exceeded — please add an env variable called PAT_1"* image
once its shared rate limit is hit. Note that this failure still returns a valid
image, so a "does it load?" check passes while the card reads as an error to a
human — worth remembering when checking the profile.

The trophy row that used to sit here was dropped the same day:
`github-profile-trophy.vercel.app` now answers `402 Payment required /
DEPLOYMENT_DISABLED` to everyone, so it rendered as a broken image. To bring
trophies back, deploy your own copy of
[github-profile-trophy](https://github.com/ryo-ma/github-profile-trophy) and
point the URL at it — the same trick already in use for the stats card.

If any of the others start showing as broken, check the URL with
`curl -s -o /dev/null -w "%{http_code}" "<url>"` before assuming the README is
at fault.

## Changing the banner

Text, colours, and layout live at the top of `scripts/make_header.py` — `NAME`,
`ROLE`, `TAGLINE`, and the palette constants, which mirror
`site/assets/styles.css` so the banner and maziyarpanahi.com match.

One rule when editing the SVG: **nothing may depend on a CSS animation to become
visible.** GitHub's image proxy renders SVG as a static frame and never starts
the animation clock, so an element that fades in from `opacity: 0` is simply
invisible on the profile. Motion is only ever decoration on top of an already
readable banner.

## Which clone to work in

The repo lives at `~/Developer/maziyarpanahi`. If a stray `~/maziyarpanahi`
turns up again, it's a leftover — delete it rather than committing from it.
