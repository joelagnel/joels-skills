#!/usr/bin/env python3
"""
wiki-generator.py, Render a multi-page "wiki" workshop from per-page markdown.

Unlike workshop-html-generator.py (which renders ONE self-contained WORKSHOP.html
with an in-page table-of-contents sidebar), this renders a SET of pages, an
Overview/landing page plus one page per module, that link to each other, with a
persistent left sidebar listing every page (the current one highlighted, its
in-page sections nested beneath it) and prev/next navigation at the foot of each
page. Use this when a workshop is large enough that one scroll is unwieldy and you
want each module to be its own page that can grow independently.

It reuses the styling, helper transforms, and JavaScript from
workshop-html-generator.py (imported as a sibling module), so the two stay
visually identical; this file only adds the cross-page chrome.

Input: a manifest JSON describing the pages. Example (content/wiki.json):

    {
      "title": "My Workshop",
      "output_dir": "..",
      "pages": [
        {"slug": "index",    "file": "index.md",    "nav": "Overview"},
        {"slug": "module-0", "file": "module-0.md", "nav": "0 · Basics"},
        {"slug": "module-1", "file": "module-1.md", "nav": "1 · Deeper"},
        {"slug": "exam",     "href": "exam.html",   "nav": "Final Exam",
         "external": true}
      ]
    }

`output_dir` is resolved relative to the manifest's directory (default ".").
Image paths inside each markdown are resolved relative to that markdown file and
embedded as base64, so the emitted HTML is fully self-contained and portable.

Dependencies: pip install markdown beautifulsoup4 pygments

Usage:
    python3 wiki-generator.py content/wiki.json
"""

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import markdown
from bs4 import BeautifulSoup

# ── Import the single-page generator as a sibling module ─────────────────────
# Its filename has hyphens, so load it by path rather than a plain import.
_SIB = Path(__file__).parent / "workshop-html-generator.py"
_spec = importlib.util.spec_from_file_location("workshop_html_generator", _SIB)
whg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(whg)

# ── Extra CSS for the wiki chrome (page list + prev/next), layered on top of
#    the single-page PICO_OVERRIDES so the look is identical elsewhere. ───────
WIKI_CSS = """
/* Sidebar: top-level page links (Overview, each Module, Exam). Brighter and
   a touch larger than the nested in-page (.h2-link) section links. */
#sidebar nav a.page-link {
  color: var(--sidebar-head);
  font-weight: 600;
  font-size: .95rem;
  padding: .5rem 1.25rem;
  border-top: 1px solid rgba(255,255,255,.05);
}
#sidebar nav a.page-link:first-of-type { border-top: none; }
#sidebar nav a.page-link.page-active {
  color: #fff;
  background: rgba(96,165,250,.16);
  border-left: 3px solid var(--sidebar-active);
}
/* Nested in-page section links only show under the active page. */
#sidebar nav a.h2-link { font-size: .84rem; padding-top: .28rem; padding-bottom: .28rem; }

/* Prev / next footer nav at the bottom of each page. */
.page-nav {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  margin-top: 3rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--border);
}
.page-nav a {
  display: inline-block;
  max-width: 46%;
  padding: .6rem 1rem;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--surface);
  color: var(--accent) !important;
  font-weight: 600;
  font-size: .92rem;
  text-decoration: none !important;
  box-shadow: var(--shadow);
  transition: transform .1s, border-color .15s;
}
.page-nav a:hover { transform: translateY(-1px); border-color: var(--accent); }
.page-nav a.next { margin-left: auto; text-align: right; }
.page-nav .nav-dir { display: block; font-size: .72rem; color: var(--text-muted); font-weight: 500; }
"""


def _page_href(page):
    return page.get("href") or f"{page['slug']}.html"


def build_wiki_sidebar(pages, current_slug, soup, title):
    """Persistent sidebar: every page listed; current one highlighted with its
    in-page h2 sections nested beneath it."""
    parts = []
    for page in pages:
        active = (page.get("slug") == current_slug and not page.get("external"))
        cls = "page-link page-active" if active else "page-link"
        href = _page_href(page)
        nav = page.get("nav", page.get("slug", ""))
        parts.append(f'<a class="{cls}" href="{href}">{nav}</a>')
        if active:
            for h2 in soup.find_all("h2"):
                hid = h2.get("id")
                text = h2.get_text(" ", strip=True)
                if not hid or not text:
                    continue
                if hid.startswith("optional--"):
                    continue   # collapsed deep-dives stay out of the nav
                disp = text if len(text) <= 42 else text[:39] + "…"
                parts.append(
                    f'<a class="h2-link" href="#{hid}" title="{text}">{disp}</a>')
    nav_html = "\n    ".join(parts)
    return (
        '<div id="sidebar">\n'
        f'  <div class="sidebar-label">{title}</div>\n'
        f'{whg.theme_picker_html()}'
        f'  <nav>\n    {nav_html}\n  </nav>\n'
        '</div>\n'
    )


def build_page_nav(pages, idx):
    """Prev/next buttons based on manifest order."""
    prev_p = pages[idx - 1] if idx > 0 else None
    next_p = pages[idx + 1] if idx < len(pages) - 1 else None
    bits = ['<nav class="page-nav">']
    if prev_p:
        bits.append(
            f'<a class="prev" href="{_page_href(prev_p)}">'
            f'<span class="nav-dir">&larr; Previous</span>{prev_p.get("nav","")}</a>')
    if next_p:
        bits.append(
            f'<a class="next" href="{_page_href(next_p)}">'
            f'<span class="nav-dir">Next &rarr;</span>{next_p.get("nav","")}</a>')
    bits.append("</nav>")
    return "\n".join(bits)


def render_page(page, idx, pages, content_dir, out_dir, title,
                pico_css, pygments_css):
    md_text = (content_dir / page["file"]).read_text(encoding="utf-8")
    md_text, math_stash = whg.render_math_prepare(md_text)
    md_engine = markdown.Markdown(
        extensions=["extra", "codehilite"],
        extension_configs={"codehilite": {
            "guess_lang": False, "linenums": False, "use_pygments": True}},
    )
    soup = BeautifulSoup(md_engine.convert(md_text), "html.parser")

    whg.render_math_inject(soup, math_stash)
    whg.ensure_heading_ids(soup)
    sidebar_html = build_wiki_sidebar(pages, page["slug"], soup, title)

    whg.embed_images(soup, content_dir, embed=True)
    whg.style_meta_block(soup)
    whg.style_exam_links(soup)
    whg.wrap_tables(soup)
    whg.inline_quiz_answers(soup)   # each answer as a per-question collapsible, inline
    whg.wrap_quiz_sections(soup)
    whg.wrap_optional_sections(soup)

    h1 = soup.find("h1")
    page_title = h1.get_text(" ", strip=True) if h1 else page.get("nav", title)
    # Avoid "Title, Title" on the landing page, where the h1 equals the site title.
    doc_title = page_title if page_title == title else f"{page_title} - {title}"
    content_html = (str(soup) + "\n" + build_page_nav(pages, idx)
                    + "\n" + whg.ATTRIBUTION_HTML)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="format-detection" content="telephone=no">
<title>{doc_title}</title>
<script>{whg.THEME_HEAD_JS}</script>
<style>
{pico_css}

{whg.PICO_OVERRIDES}

{WIKI_CSS}

{pygments_css}
</style>
</head>
<body>
<button id="mobile-nav-toggle" aria-label="Open navigation" title="Open navigation">&#9776;</button>
<div id="sidebar-overlay"></div>
{sidebar_html}
<div id="main">
  <main class="content-wrap">
{content_html}
  </main>
</div>
<div id="lightbox" class="lightbox" role="dialog" aria-label="Enlarged diagram">
  <button class="lightbox-close" aria-label="Close">&times;</button>
  <img alt="">
</div>
<script>
{whg.SIDEBAR_JS}
</script>
</body>
</html>
"""
    out_path = out_dir / f"{page['slug']}.html"
    out_path.write_text(html, encoding="utf-8")
    kb = out_path.stat().st_size // 1024
    print(f"Written: {out_path}  ({kb} KB)")


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("manifest", help="Path to the wiki.json manifest")
    args = ap.parse_args()

    manifest_path = Path(args.manifest).resolve()
    if not manifest_path.exists():
        sys.exit(f"Error: {manifest_path} not found")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    content_dir = manifest_path.parent
    out_dir = (content_dir / manifest.get("output_dir", ".")).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    title = manifest.get("title", "Workshop")
    pages = manifest["pages"]

    pico_css = whg.load_pico_css()
    pygments_css = whg.get_pygments_css()

    for idx, page in enumerate(pages):
        if page.get("external"):
            continue  # e.g. a prebuilt exam.html, only appears in nav
        render_page(page, idx, pages, content_dir, out_dir, title,
                    pico_css, pygments_css)


if __name__ == "__main__":
    main()
