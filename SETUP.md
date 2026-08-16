# How this profile is built

The README is part hand-written, part generated. This note explains which is
which, so future-you edits the right file.

## Layout

| Path | Generated? | What it is |
| --- | --- | --- |
| `README.md` | partly | Hand-written, except the block between the `HF-STATS` markers |
| `assets/header.svg` | yes | The banner, rebuilt from the live numbers |
| `metrics/hf.json` | yes | Raw Hugging Face figures, refreshed daily |
| `scripts/fetch_hf_stats.py` | no | Hugging Face Hub API → `metrics/hf.json` |
| `scripts/make_header.py` | no | `metrics/hf.json` → `assets/header.svg` |
| `scripts/render_readme.py` | no | `metrics/hf.json` → the README stats block |
| `.github/workflows/profile.yml` | no | Runs the three scripts daily, plus the snake |

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
python3 scripts/fetch_hf_stats.py && python3 scripts/make_header.py && python3 scripts/render_readme.py
```

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
