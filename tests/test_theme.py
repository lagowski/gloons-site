"""Light/dark theme checks (issue #1, fleet brief veracrew#2165).

Stdlib only, so it can never be skipped for a missing dependency.
Run: python -m pytest tests/
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
CSS = (ROOT / "style.css").read_text()
PAGES = ("index.html", "privacy.html", "terms.html")

DARK_BLOCK = re.compile(r':root\[data-theme="dark"\]\s*\{([^}]*)\}')
SYSTEM_BLOCK = re.compile(
    r'@media\s*\(prefers-color-scheme:\s*dark\)\s*\{\s*'
    r':root:not\(\[data-theme="light"\]\)\s*\{([^}]*)\}'
)
LIGHT_BLOCK = re.compile(r"^:root\s*\{([^}]*)\}", re.M)


def tokens(body):
    return dict(re.findall(r"(--[\w-]+)\s*:\s*([^;]+?)\s*(?:;|$)", body))


def block(pattern):
    m = pattern.search(CSS)
    assert m, f"style.css has no block matching {pattern.pattern}"
    return tokens(m.group(1))


def rgb(hex_):
    h = hex_.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    assert re.fullmatch(r"[0-9a-fA-F]{6}", h), f"not a hex colour: {hex_}"
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def luminance(c):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

    r, g, b = (ch(v) for v in c)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def over(top, alpha, bottom):
    return tuple(round(t * alpha + b * (1 - alpha)) for t, b in zip(top, bottom))


def grain_worst_case():
    """Grain colour and peak alpha, read from the feColorMatrix in --grain."""
    grain = block(LIGHT_BLOCK)["--grain"]
    values = re.search(r"values='([^']+)'", grain).group(1).split()
    m = [float(v) for v in values]
    colour = tuple(round(m[i * 5 + 4] * 255) for i in range(3))
    return colour, m[18]  # alpha row: 0 0 0 a 0 -> peak alpha = a


def dark_backgrounds():
    d = block(DARK_BLOCK)
    bg, card = rgb(d["--bg"]), rgb(d["--card"])
    colour, alpha = grain_worst_case()
    return {"bg": bg, "card": card, "bg+grain": over(colour, alpha, bg)}


# Every text/background pair in the dark set, with its minimum ratio.
TEXT_PAIRS = [("--fg", 12.0), ("--muted", 4.5), ("--accent", 4.5)]


@pytest.mark.parametrize("fg,minimum", TEXT_PAIRS)
@pytest.mark.parametrize("surface", ["bg", "card", "bg+grain"])
def test_dark_text_contrast(fg, minimum, surface):
    d = block(DARK_BLOCK)
    ratio = contrast(rgb(d[fg]), dark_backgrounds()[surface])
    assert ratio >= minimum, f"{fg} on {surface}: {ratio:.2f} < {minimum}"


def test_dark_is_calm_not_black():
    d = block(DARK_BLOCK)
    assert d["--fg"].lower() not in ("#fff", "#ffffff")
    assert d["--bg"].lower() not in ("#000", "#000000")
    assert luminance(rgb(d["--card"])) > luminance(rgb(d["--bg"]))


def test_accent_constant_across_modes():
    assert block(DARK_BLOCK)["--accent"] == block(LIGHT_BLOCK)["--accent"]


@pytest.mark.parametrize("pattern", [LIGHT_BLOCK, DARK_BLOCK], ids=["light", "dark"])
def test_blend_mode_hero_contrast(pattern):
    """The hero uses mix-blend-mode:difference, so it shows |bg - ink|."""
    t = block(pattern)
    bg, ink = rgb(t["--bg"]), rgb(block(LIGHT_BLOCK)["--hero-ink"])
    shown = tuple(abs(a - b) for a, b in zip(bg, ink))
    assert contrast(shown, bg) >= 4.5


def test_system_block_matches_dark_set():
    assert block(SYSTEM_BLOCK) == block(DARK_BLOCK)


def test_every_colour_is_a_token():
    rest = CSS
    for pattern in (LIGHT_BLOCK, DARK_BLOCK, SYSTEM_BLOCK):
        rest = pattern.sub("", rest)
    literals = re.findall(r"#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(", rest)
    assert not literals, f"colour literals outside the token blocks: {literals}"


def test_transitions_only_without_reduced_motion():
    m = re.search(r"@media\s*\(prefers-reduced-motion:\s*no-preference\)\s*\{", CSS)
    assert m, "no prefers-reduced-motion:no-preference block"
    before, inside = CSS[: m.start()], CSS[m.end() :]
    assert "transition" not in before and "animation" not in before
    for ms in re.findall(r"transition:[^;}]*?([\d.]+)(m?s)", inside):
        value = float(ms[0]) * (1 if ms[1] == "ms" else 1000)
        assert value <= 250


@pytest.mark.parametrize("page", PAGES)
def test_page_has_head_script_before_paint(page):
    html = (ROOT / page).read_text()
    head = html.split("</head>", 1)[0]
    script = re.search(r"<script>(.*?)</script>", head, re.S)
    assert script, f"{page}: no inline theme script in <head>"
    assert 'localStorage.getItem("theme")' in script.group(1)
    assert "data-theme" in script.group(1)
    assert head.index("<script>") < head.index('rel="stylesheet"')


@pytest.mark.parametrize("page", PAGES)
def test_page_has_toggle(page):
    html = (ROOT / page).read_text()
    header = re.search(r"<header>(.*?)</header>", html, re.S).group(1)
    button = re.search(r"<button[^>]*class=\"theme-toggle\"[^>]*>", header)
    assert button, f"{page}: no theme toggle in the header"
    assert 'type="button"' in button.group(0)
    assert re.search(r'aria-label="Theme: \w+"', button.group(0))
    assert '<script src="theme.js" defer></script>' in html
