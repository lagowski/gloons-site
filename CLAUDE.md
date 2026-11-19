# gloons-site: the Gloons channel's public pages and the media host for its Instagram/Facebook posts
Verified against `main@debabcc` on 2026-11-19 (open PRs: 1). Public repo: yes.

One GitHub Pages site, `https://lagowski.github.io/gloons-site/`, with two jobs:

- **Pages**: `index.html`, `privacy.html` and `terms.html` are the home, privacy-policy and terms URLs
  registered for the Gloons publishing app's Google OAuth consent screen; `privacy.html` also has the
  TikTok section. `tiktok-callback.html` is the TikTok OAuth callback (it only shows the one-time code
  to copy). The `tiktok*.txt` file is TikTok's URL-prefix verification.
- **Media host**: Instagram and Facebook take a URL, not a file, so the Gloons publishing pipeline
  (a separate repo) commits each video or image to `media/<sha256[:16]>.<ext>` and hands the Pages
  URL of that file to the platform.

This repo is public and Pages serves its root: every file here, this one included, is published.

## Commands

- Clone: `git clone --depth 1 https://github.com/lagowski/gloons-site` (see Traps for why).
- Preview: `python3 -m http.server 8000`, then open `http://localhost:8000/`.
- Test: `python -m pytest tests/ -q` (stdlib + pytest; CI uses Python 3.12 and `pytest==8.3.4`).
- Run one test: `python -m pytest tests/test_theme.py -q -k contrast`.
- Build: none. Deploy: none of its own, a push to `main` is the deploy.

## Owner rules

- The repo stays public: Instagram and Facebook fetch the hosted media from it (owner 2026-11-03).
- No AI review gate on this repo: a public repo cannot call the private review workflows; the CI
  check below is what PRs get (owner 2026-11-03).
- GitHub-hosted runners only: anyone can open a fork PR, so the job never moves to a self-hosted
  label (owner 2026-11-03).

## Traps

- Reworded or restyled `privacy.html` / `terms.html` -> they are the texts Google and TikTok reviewed,
  and the privacy page names the scopes the app really uses -> change them only when the app's
  scopes or data use change, in the same step.
- Moved or renamed `index.html`, `privacy.html`, `terms.html`, `tiktok-callback.html`, the
  `tiktok*.txt` file or `media/` -> their URLs are registered with Google and TikTok and used by the
  publishing pipeline -> keep the names and places.
- Edited, renamed or deleted a file in `media/` by hand, or rewrote `main`'s history -> a post that
  is being published may be fetching that URL -> leave `media/` to the pipeline. It commits
  `media: <name> (Gloons video for Instagram/Facebook)`, waits until Pages serves the same sha256
  (a retry is an empty commit that starts a new Pages build) and prunes files older than 3 days
  (`media: prune N file(s) older than 3 days`), because the platforms copy the file when they publish.
- A full clone is about 1 GB -> history keeps every media file ever hosted, while the working tree's
  `media/` is 23 MB (2026-11-19) -> clone with `--depth 1`.
- Branch or merge on a stale `main` -> media commits land several times a day (5 to 9 a day in
  2026-11) -> `git pull --ff-only` before you branch and before you merge.
- A new file in the root is on the web after the next push -> Pages serves the whole root -> add
  nothing that should not be public.
- Absolute links break the site -> it is served under `/gloons-site/` -> keep every link relative.
- A new page fails CI -> `tests/test_site.py` globs every `*.html` in the root (balanced tags, `lang`,
  `<title>`, local links resolve) -> make the page pass it. The theme tests cover only `index.html`,
  `privacy.html` and `terms.html`; `tiktok-callback.html` has no theme toggle.
- A colour literal outside the token blocks fails `tests/test_theme.py` -> colours live only in
  `style.css`'s light `:root`, `:root[data-theme="dark"]` and the `prefers-color-scheme` block, which
  must equal the dark block; the accent is the same in both modes (issue #1, PR #2).
- A transition outside `prefers-reduced-motion: no-preference`, or longer than 250 ms, fails the
  theme tests; so does moving the inline theme script in `<head>` after the stylesheet, or loading
  `theme.js` without `defer` (issue #1, PR #2).

## Workflow

- Base branch `main`. Pages serves `main`, path `/` ("deploy from a branch"); no custom domain is set
  in Pages and there is no `CNAME` file (checked 2026-11-19).
- Pages, CSS, JS, tests and CI change through a PR into `main` (as #2 and #3 did). Only the
  pipeline's media commits go straight to `main`.
- CI: `.github/workflows/ci.yml` runs the tests on every pull request and on pushes to `main` that
  touch anything outside `media/`.
- The CI check is not required by a ruleset, on purpose: a required status check would also reject
  the pipeline's direct media pushes (PR #3). `main` has no branch protection (checked 2026-11-19).
- No build step and no dependencies: hand-written HTML (one long line per page), `style.css`,
  `theme.js`.

## Pointers

- `@README.md`: what the site is, preview and test commands.
- `.github/workflows/ci.yml`: the comment at the top gives the reasons behind the owner rules.
- Issue #1 and PR #2: the light/dark/system theme contract that `tests/test_theme.py` enforces.
