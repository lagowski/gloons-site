# gloons-site — context for Claude

This repo is **public** and everything in it is published. Write nothing private here (no machine
details, credentials, vault paths or internal plans): this file included.

## Purpose

Two jobs in one GitHub Pages site, `https://lagowski.github.io/gloons-site/`:

1. **The public pages of the Gloons channel**: `index.html`, `privacy.html`, `terms.html`. They are
   the branding URLs (home, privacy policy, terms) of the "Gloons Publisher" Google OAuth app, and
   `privacy.html` also has the TikTok section. `tiktok-callback.html` is the TikTok OAuth callback:
   it only shows the one-time code so it can be copied into the setup step. The
   `tiktok*.txt` file is TikTok's URL-prefix verification.
2. **The media host for Instagram and Facebook**: both APIs take a URL, not a file, so
   gloons-studio (`gloons/publisher/hosting.py`) pushes each video/image to
   `media/<sha256[:16]>.<ext>` and passes `https://lagowski.github.io/gloons-site/media/<name>`
   to the publishers.

## How it is built and deployed

- Plain static files, no build step, no dependencies: hand-written HTML (one long line per
  page), `style.css`, `theme.js`.
- GitHub Pages serves branch `main`, path `/` (legacy "deploy from a branch"). **A push to `main`
  is the deploy.** No custom domain is configured in Pages (checked 2026-11-18).
- All links are relative, so the site works under `/gloons-site/`. Keep them relative.

## What feeds `media/`

- gloons-studio's `host_video()` commits straight to `main` as Dixter999
  (`media: <name> (Gloons video for Instagram/Facebook)`), then waits until Pages serves the same
  sha256. A retry pushes an empty commit to start a new Pages build.
- `prune()` removes media older than 3 days (`media: prune N file(s) older than 3 days`): the
  platforms copy the file when they publish.
- Several such commits land every day. **Never edit, rename or delete files in `media/` by hand**,
  and never rewrite `main`'s history: a URL may be in use by a post that is being published.

## Test

```
python -m pytest tests/ -q
```

Stdlib + pytest only (CI pins `pytest==8.3.4`, Python 3.12).

- `tests/test_site.py`: every `*.html` in the root is well formed (tags balance, `lang`, `<title>`)
  and every local link resolves.
- `tests/test_theme.py`: the light/dark theme contract (issue #1) for `index.html`,
  `privacy.html`, `terms.html`: dark-set contrast ratios, the system block equals the dark block,
  every colour is a token in the `:root` blocks of `style.css`, transitions only under
  `prefers-reduced-motion: no-preference` and at most 250 ms, the inline theme script in `<head>`
  before the stylesheet, a `.theme-toggle` button in the header, `theme.js` loaded with `defer`.

## CI and review (owner decision 2026-11-03)

- `.github/workflows/ci.yml` runs the tests on pull requests and on pushes to `main` that touch
  anything outside `media/`.
- **The repo must stay public**: Instagram/Facebook fetch the hosted media from it.
- **No fleet AI gate here**: a public repo cannot call the private review-gate workflows.
- **GitHub-hosted runners only.** Anyone can open a fork PR, so the job must never move to a
  self-hosted label.
- **The check is not required by a ruleset, on purpose**: a required status check would also reject
  gloons-studio's direct media pushes.
- Changes to pages, CSS, JS, tests or CI go through a PR into `main` (as #2 and #3 did). Only the
  media commits go straight to `main`.

## Traps

- **`privacy.html` and `terms.html` are what Google and TikTok reviewed.** The privacy page names
  the real scopes the app uses. If the app's scopes or data use change, change the page in the same
  step; don't reword these pages for style.
- **Don't move or rename** `index.html`, `privacy.html`, `terms.html`, `tiktok-callback.html`, the
  `tiktok*.txt` verification file or `media/`: their URLs are registered with Google, TikTok, and
  used by the publisher.
- **Clone with `--depth 1`.** History holds every media file ever hosted; a full clone was 1.1 GB
  on 2026-11-18 while the working tree's `media/` was 23 MB.
- `main` moves several times a day: `git pull --ff-only` before you branch and before you merge.
- Every file in the root is served by Pages. Don't add anything that should not be public.
- A new page must pass `test_site.py` (it globs `*.html`); the theme tests cover only the three
  pages listed above, and `tiktok-callback.html` has no theme toggle.
- Colours live only in the token blocks of `style.css` (light `:root`, `:root[data-theme="dark"]`,
  and the `prefers-color-scheme` block, which must equal the dark block). The accent is the same in
  both modes.

## Recent changes

- 2026-11-03: light/dark/system theme switch (#1, PR #2); first CI (PR #3).
- 2026-10-03: links to the five Gloons profiles on the home page.
- 2026-10-01: the purple Gloons character replaced the placeholder logo.
- 2026-09-30: site created (home, privacy, terms), TikTok section, callback page and verification
  file; Instagram accepted the Pages media host.
