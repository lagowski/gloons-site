"""Basic site checks: every page is well-formed enough to serve and every local link resolves.

Run: python -m pytest tests/
"""

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

import pytest

ROOT = Path(__file__).resolve().parent.parent
PAGES = sorted(p.name for p in ROOT.glob("*.html"))
# Elements that never take a closing tag.
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.refs, self.stack, self.errors = [], [], []
        self.title, self.lang, self.in_title = "", None, False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.lang = a.get("lang")
        if tag == "title":
            self.in_title = True
        for key in ("href", "src"):
            if a.get(key) is not None:
                self.refs.append(a[key])
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if tag in VOID:
            return
        if not self.stack or self.stack[-1] != tag:
            self.errors.append(f"</{tag}> closes <{self.stack[-1] if self.stack else 'nothing'}>")
            if tag in self.stack:
                del self.stack[len(self.stack) - 1 - self.stack[::-1].index(tag) :]
            return
        self.stack.pop()

    def handle_data(self, data):
        if self.in_title:
            self.title += data


def parse(name):
    page = Page()
    page.feed((ROOT / name).read_text(encoding="utf-8"))
    page.close()
    return page


def test_there_are_pages():
    # A guard that finds nothing must not pass: an empty glob would make every check below vacuous.
    assert {"index.html", "privacy.html", "terms.html"} <= set(PAGES)


@pytest.mark.parametrize("name", PAGES)
def test_page_is_well_formed(name):
    page = parse(name)
    assert not page.errors, f"{name}: {page.errors}"
    assert not page.stack, f"{name}: unclosed {page.stack}"
    assert page.lang, f"{name}: <html> has no lang"
    assert page.title.strip(), f"{name}: empty <title>"


@pytest.mark.parametrize("name", PAGES)
def test_local_links_resolve(name):
    missing = []
    for ref in parse(name).refs:
        parts = urlsplit(ref)
        if parts.scheme or parts.netloc or not parts.path:  # external, mailto:, data:, or #fragment
            continue
        target = (ROOT / name).parent / parts.path
        if target.is_dir():
            target = target / "index.html"
        if not target.is_file():
            missing.append(ref)
    assert not missing, f"{name}: broken local links {missing}"
