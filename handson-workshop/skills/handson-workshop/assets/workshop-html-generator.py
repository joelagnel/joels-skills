#!/usr/bin/env python3
"""
workshop-html-generator.py, Render WORKSHOP.md → styled, self-contained WORKSHOP.html

Features:
  - Sticky sidebar table of contents with JS scroll-position highlighting
  - Quiz sections wrapped in a blue callout box
  - Answer key sections wrapped in collapsible <details> elements
  - Optional deep-dive sections (h3/h4 with {#optional--*} anchors) wrapped in
    collapsible <details>, kept out of the sidebar nav
  - Syntax-highlighted fenced code blocks (Pygments github-dark style)
  - Diagram PNGs/SVGs embedded as base64 data URIs (fully self-contained)
  - Modern learning-conducive color theme (calm blue/navy/teal palette)

Dependencies: pip install markdown beautifulsoup4 pygments

Usage:
    python3 workshop-html-generator.py WORKSHOP.md
    python3 workshop-html-generator.py WORKSHOP.md -o out.html
    python3 workshop-html-generator.py WORKSHOP.md --no-embed-images
"""

import argparse
import base64
import re
import sys
from pathlib import Path

import markdown
from bs4 import BeautifulSoup, Tag
from pygments.formatters import HtmlFormatter
from pygments.styles import get_style_by_name

# ── CSS strategy ─────────────────────────────────────────────────────────────
#
# Base: Pico.css 2.x (classless), inlined from assets/pico.classless.min.css.
# Pico handles body / html / typography / mobile responsive defaults / iOS
# Safari quirks. We were reinventing this and getting iOS rendering wrong.
#
# CUSTOM_CSS layers on top of Pico for the bits Pico doesn't know about:
#   - Sticky sidebar with table-of-contents and scroll-position highlighting
#   - Mobile hamburger / overlay
#   - Quiz callout boxes
#   - Collapsible answer-key <details>
#   - Click-to-enlarge diagram lightbox
#   - Pygments-rendered code blocks
#   - Fluid typography via clamp() (replaces our hand-rolled media queries)
#
# Pygments github-dark CSS is appended after CUSTOM_CSS so it takes precedence
# over Pico's <pre> styling for the .codehilite class.

# Path relative to this file
PICO_CSS_PATH = Path(__file__).parent / 'pico.classless.min.css'

# Version stamped into the attribution footer on every generated page.
SKILL_VERSION = '1.2.0'
SKILL_URL = 'https://github.com/joelagnel/joels-skills/tree/master/handson-workshop'
ATTRIBUTION_HTML = (
    '<footer class="attribution">Created by '
    f'<a href="{SKILL_URL}" target="_blank" rel="noopener">'
    f'HOW (hands-on workshop skill, v{SKILL_VERSION})</a></footer>'
)


# ── Themes ───────────────────────────────────────────────────────────────────
# Five fixed themes, selectable from the sidebar swatch picker and persisted
# in localStorage['handson-theme']. Each theme is permanently dark or light —
# there are no per-theme dark-mode variants. 'aurora' (vivid dark) is the
# default. Variables are emitted as [data-theme=X] blocks over one shared set
# of names; a tiny inline <head> script applies the saved theme before first
# paint (no flash), and printing always pins the 'paper' palette.

# name, picker label, swatch background, swatch dot (accent)
THEMES = [
    ('aurora',    'Aurora (vivid dark, default)', '#0d0b1e',
     'linear-gradient(135deg,#22d3ee,#f472b6)'),
    ('midnight',  'Midnight (dark)',              '#0b1220', '#60a5fa'),
    ('synthwave', 'Synthwave (dark)',             '#16072b',
     'linear-gradient(135deg,#ff6ad5,#00e5ff)'),
    ('paper',     'Paper (light)',                '#eef2f7', '#2563eb'),
    ('sepia',     'Sepia (light)',                '#f3ecdd', '#b45309'),
]

# Runs in <head>, before the stylesheet paints.
THEME_HEAD_JS = (
    "(function(){var t='aurora';"
    "try{t=localStorage.getItem('handson-theme')||t;}catch(e){}"
    "document.documentElement.setAttribute('data-theme',t);})();"
)


def theme_picker_html():
    """Swatch-row widget for the sidebar (one button per theme)."""
    btns = '\n    '.join(
        f'<button type="button" class="theme-swatch" data-theme-pick="{name}" '
        f'title="{label}" aria-label="{label}" style="background:{bg}">'
        f'<span class="dot" style="background:{dot}"></span></button>'
        for name, label, bg, dot in THEMES)
    return ('  <div class="theme-picker" role="group" aria-label="Color theme">\n'
            f'    {btns}\n  </div>\n')


_AURORA_VARS = """\
  color-scheme: dark;
  --pico-primary:        #22d3ee;
  --pico-primary-hover:  #67e8f9;
  --pico-primary-focus:  rgba(34, 211, 238, 0.3);
  --pico-primary-inverse:#08303a;
  --pico-color:          #e6e4f5;
  --pico-h1-color:       #f5f3ff;
  --pico-h2-color:       #c4b5fd;
  --pico-h3-color:       #93c5fd;
  --pico-h4-color:       #e6e4f5;
  --pico-muted-color:    #a5a0c8;
  --bg:              #0d0b1e;
  --surface:         #171432;
  --sidebar-bg:      #100d24;
  --sidebar-text:    #9d97c9;
  --sidebar-head:    #e9d5ff;
  --sidebar-active:  #f0abfc;
  --sidebar-hover:   rgba(255,255,255,.07);
  --text:            #e6e4f5;
  --text-muted:      #a5a0c8;
  --heading:         #f5f3ff;
  --accent:          #22d3ee;
  --accent2:         #f472b6;
  --code-bg:         #0a0818;
  --code-fg:         #e6edf3;
  --code-border:     #2a2450;
  --ic-bg:           #2b1f4d;
  --ic-fg:           #d8b4fe;
  --quiz-bg:         #0e2233;
  --quiz-border:     #22d3ee;
  --quiz-text-link-bg: #164e63;
  --ans-border:      #a3e635;
  --ans-sum-bg:      #1d2e10;
  --ans-sum-text:    #d9f99d;
  --ans-body-bg:     #131f0b;
  --opt-border:      #fbbf24;
  --opt-sum-bg:      #33260b;
  --opt-sum-text:    #fde68a;
  --opt-body-bg:     #241b08;
  --border:          #2b2650;
  --table-row-hover: #1b1740;
  --meta-bg:         #171432;
  --shadow:          0 2px 8px rgba(0,0,0,.45), 0 1px 3px rgba(0,0,0,.35);
  --bg-grad:         radial-gradient(1100px 600px at 12% -8%, #241d5c 0%, rgba(13,11,30,0) 60%), radial-gradient(900px 500px at 105% 15%, #143b4d 0%, rgba(13,11,30,0) 55%), #0d0b1e;
  --sidebar-grad:    linear-gradient(180deg, #1b1546 0%, #100d24 45%, #0d0a1c 100%);
  --h1-grad-a:       #22d3ee;
  --h1-grad-b:       #f472b6;
  --strong-color:    #fbbf24;
  --em-color:        #f0abfc;
  --marker-color:    #a3e635;
  --thead-bg:        #221a52;
  --thead-fg:        #e9d5ff;
  --hr-grad:         linear-gradient(90deg, #22d3ee, #f472b6, transparent);
  --link-hover:      #a5f3fc;
"""

_MIDNIGHT_VARS = """\
  color-scheme: dark;
  --pico-primary:        #60a5fa;
  --pico-primary-hover:  #93c5fd;
  --pico-primary-focus:  rgba(96, 165, 250, 0.28);
  --pico-primary-inverse:#0b1220;
  --pico-color:          #e2e8f0;
  --pico-h1-color:       #f1f5f9;
  --pico-h2-color:       #f1f5f9;
  --pico-h3-color:       #cbd5e1;
  --pico-h4-color:       #e2e8f0;
  --pico-muted-color:    #94a3b8;
  --bg:              #0b1220;
  --surface:         #131c2e;
  --sidebar-bg:      #0d1422;
  --sidebar-text:    #94a3b8;
  --sidebar-head:    #cbd5e1;
  --sidebar-active:  #93c5fd;
  --sidebar-hover:   rgba(255,255,255,.06);
  --text:            #e2e8f0;
  --text-muted:      #94a3b8;
  --heading:         #f1f5f9;
  --accent:          #60a5fa;
  --accent2:         #22d3ee;
  --code-bg:         #060a13;
  --code-fg:         #e6edf3;
  --code-border:     #1e2a3d;
  --ic-bg:           #1e3a5f;
  --ic-fg:           #bfdbfe;
  --quiz-bg:         #122236;
  --quiz-border:     #3b82f6;
  --quiz-text-link-bg: #1e3a5f;
  --ans-border:      #4ade80;
  --ans-sum-bg:      #143124;
  --ans-sum-text:    #bbf7d0;
  --ans-body-bg:     #0d1f17;
  --opt-border:      #a78bfa;
  --opt-sum-bg:      #251b3f;
  --opt-sum-text:    #ddd6fe;
  --opt-body-bg:     #16112a;
  --border:          #243049;
  --table-row-hover: #1a253c;
  --meta-bg:         #131c2e;
  --shadow:          0 2px 8px rgba(0,0,0,.4), 0 1px 3px rgba(0,0,0,.3);
  --bg-grad:         radial-gradient(1000px 550px at 15% -8%, #16294d 0%, rgba(11,18,32,0) 60%), #0b1220;
  --sidebar-grad:    linear-gradient(180deg, #12203a 0%, #0d1422 55%);
  --h1-grad-a:       #60a5fa;
  --h1-grad-b:       #22d3ee;
  --strong-color:    #7dd3fc;
  --em-color:        #a5b4fc;
  --marker-color:    #38bdf8;
  --thead-bg:        #16294d;
  --thead-fg:        #cfe4ff;
  --hr-grad:         linear-gradient(90deg, #60a5fa, #22d3ee, transparent);
  --link-hover:      #bfdbfe;
"""

_SYNTHWAVE_VARS = """\
  color-scheme: dark;
  --pico-primary:        #ff6ad5;
  --pico-primary-hover:  #ff8fe0;
  --pico-primary-focus:  rgba(255, 106, 213, 0.3);
  --pico-primary-inverse:#33041f;
  --pico-color:          #f3e8ff;
  --pico-h1-color:       #ffffff;
  --pico-h2-color:       #f0abfc;
  --pico-h3-color:       #67e8f9;
  --pico-h4-color:       #f3e8ff;
  --pico-muted-color:    #b795e0;
  --bg:              #16072b;
  --surface:         #22103f;
  --sidebar-bg:      #120524;
  --sidebar-text:    #b795e0;
  --sidebar-head:    #fbcfe8;
  --sidebar-active:  #00e5ff;
  --sidebar-hover:   rgba(255,255,255,.08);
  --text:            #f3e8ff;
  --text-muted:      #b795e0;
  --heading:         #ffffff;
  --accent:          #ff6ad5;
  --accent2:         #00e5ff;
  --code-bg:         #0d0318;
  --code-fg:         #e6edf3;
  --code-border:     #3b1a63;
  --ic-bg:           #3b1a63;
  --ic-fg:           #f5d0fe;
  --quiz-bg:         #131046;
  --quiz-border:     #00e5ff;
  --quiz-text-link-bg: #1e1b64;
  --ans-border:      #4ade80;
  --ans-sum-bg:      #0c2d1c;
  --ans-sum-text:    #bbf7d0;
  --ans-body-bg:     #081f14;
  --opt-border:      #ffd166;
  --opt-sum-bg:      #33260b;
  --opt-sum-text:    #ffe9a8;
  --opt-body-bg:     #241b08;
  --border:          #3b2a63;
  --table-row-hover: #2a1650;
  --meta-bg:         #22103f;
  --shadow:          0 2px 8px rgba(0,0,0,.45), 0 1px 3px rgba(0,0,0,.35);
  --bg-grad:         radial-gradient(1000px 600px at 20% -10%, #3b1263 0%, rgba(22,7,43,0) 60%), radial-gradient(800px 500px at 110% 20%, #6b1d4f 0%, rgba(22,7,43,0) 55%), #16072b;
  --sidebar-grad:    linear-gradient(180deg, #2a0d52 0%, #120524 60%);
  --h1-grad-a:       #ff6ad5;
  --h1-grad-b:       #00e5ff;
  --strong-color:    #ffd166;
  --em-color:        #ff9ecf;
  --marker-color:    #00e5ff;
  --thead-bg:        #33125f;
  --thead-fg:        #fbcfe8;
  --hr-grad:         linear-gradient(90deg, #ff6ad5, #00e5ff, transparent);
  --link-hover:      #ff9ee2;
"""

_PAPER_VARS = """\
  color-scheme: light;
  --pico-primary:        #2563eb;
  --pico-primary-hover:  #1d4ed8;
  --pico-primary-focus:  rgba(37, 99, 235, 0.25);
  --pico-primary-inverse:#ffffff;
  --pico-color:          #1e293b;
  --pico-h1-color:       #0f172a;
  --pico-h2-color:       #0f172a;
  --pico-h3-color:       #0f172a;
  --pico-h4-color:       #1e293b;
  --pico-muted-color:    #475569;
  --bg:              #eef2f7;
  --surface:         #ffffff;
  --sidebar-bg:      #18243f;
  --sidebar-text:    #8aafd0;
  --sidebar-head:    #ccddf5;
  --sidebar-active:  #60a5fa;
  --sidebar-hover:   rgba(255,255,255,.06);
  --text:            #1e293b;
  --text-muted:      #475569;
  --heading:         #0f172a;
  --accent:          #2563eb;
  --accent2:         #0891b2;
  --code-bg:         #0d1117;
  --code-fg:         #e6edf3;
  --code-border:     #21262d;
  --ic-bg:           #dbeafe;
  --ic-fg:           #1e40af;
  --quiz-bg:         #eff6ff;
  --quiz-border:     #3b82f6;
  --quiz-text-link-bg: #e0f2fe;
  --ans-border:      #16a34a;
  --ans-sum-bg:      #dcfce7;
  --ans-sum-text:    #14532d;
  --ans-body-bg:     #f0fdf4;
  --opt-border:      #7c3aed;
  --opt-sum-bg:      #ede9fe;
  --opt-sum-text:    #4c1d95;
  --opt-body-bg:     #f5f3ff;
  --border:          #e2e8f0;
  --table-row-hover: var(--quiz-bg);
  --meta-bg:         #f8faff;
  --shadow:          0 1px 4px rgba(0,0,0,.08), 0 1px 2px rgba(0,0,0,.05);
  --bg-grad:         linear-gradient(180deg, #f4f7fb 0%, #eef2f7 240px);
  --sidebar-grad:    linear-gradient(180deg, #1e2c4e 0%, #18243f 55%);
  --h1-grad-a:       #1d4ed8;
  --h1-grad-b:       #0891b2;
  --strong-color:    #b45309;
  --em-color:        #0f766e;
  --marker-color:    #2563eb;
  --thead-bg:        #dbeafe;
  --thead-fg:        #1e3a8a;
  --hr-grad:         linear-gradient(90deg, #2563eb, #0891b2, transparent);
  --link-hover:      #1d4ed8;
"""

_SEPIA_VARS = """\
  color-scheme: light;
  --pico-primary:        #b45309;
  --pico-primary-hover:  #92400e;
  --pico-primary-focus:  rgba(180, 83, 9, 0.25);
  --pico-primary-inverse:#ffffff;
  --pico-color:          #3f3226;
  --pico-h1-color:       #2a2118;
  --pico-h2-color:       #2a2118;
  --pico-h3-color:       #4a3a2b;
  --pico-h4-color:       #3f3226;
  --pico-muted-color:    #6b5a48;
  --bg:              #f3ecdd;
  --surface:         #fbf6ea;
  --sidebar-bg:      #3d2f23;
  --sidebar-text:    #cbb49a;
  --sidebar-head:    #f0e3d0;
  --sidebar-active:  #f59e0b;
  --sidebar-hover:   rgba(255,255,255,.06);
  --text:            #3f3226;
  --text-muted:      #6b5a48;
  --heading:         #2a2118;
  --accent:          #b45309;
  --accent2:         #0f766e;
  --code-bg:         #241c14;
  --code-fg:         #ede0d0;
  --code-border:     #3a2e22;
  --ic-bg:           #ecdcc3;
  --ic-fg:           #7c4a03;
  --quiz-bg:         #f6ecd9;
  --quiz-border:     #b45309;
  --quiz-text-link-bg: #efe0c5;
  --ans-border:      #4d7c0f;
  --ans-sum-bg:      #e8f0d8;
  --ans-sum-text:    #365314;
  --ans-body-bg:     #f2f7e8;
  --opt-border:      #7e22ce;
  --opt-sum-bg:      #f0e5f7;
  --opt-sum-text:    #581c87;
  --opt-body-bg:     #f7f1fb;
  --border:          #e0d3bd;
  --table-row-hover: #f1e7d2;
  --meta-bg:         #f8f2e4;
  --shadow:          0 1px 4px rgba(60,40,10,.1), 0 1px 2px rgba(60,40,10,.06);
  --bg-grad:         linear-gradient(180deg, #f7f1e2 0%, #f3ecdd 240px);
  --sidebar-grad:    linear-gradient(180deg, #4a3a2b 0%, #3d2f23 55%);
  --h1-grad-a:       #b45309;
  --h1-grad-b:       #0f766e;
  --strong-color:    #9a3412;
  --em-color:        #0f766e;
  --marker-color:    #b45309;
  --thead-bg:        #ecdcc3;
  --thead-fg:        #5c3d10;
  --hr-grad:         linear-gradient(90deg, #b45309, #0f766e, transparent);
  --link-hover:      #92400e;
"""

THEME_CSS = (
    "/* ── Themes: one variable set, five fixed palettes ─────────────────── */\n"
    ":root {\n"
    "  --pico-text-decoration: none;\n"
    "  /* Fluid typography: ~17 px on phones up to ~19 px on wide displays. */\n"
    "  --pico-font-size:   clamp(1rem, 0.92rem + 0.4vw, 1.1875rem);\n"
    "  --pico-line-height: 1.65;\n"
    "}\n\n"
    "/* Selectors are written as :root[data-theme=x] (specificity 0,2,0) so they\n"
    "   out-rank the vendored Pico sheet's own :root:not([data-theme=dark]) light\n"
    "   block, which would otherwise force light text/background variables onto\n"
    "   every theme not literally named 'dark'. */\n"
    ":root:not([data-theme]), :root[data-theme=aurora] {\n" + _AURORA_VARS + "}\n\n"
    ":root[data-theme=midnight] {\n" + _MIDNIGHT_VARS + "}\n\n"
    ":root[data-theme=synthwave] {\n" + _SYNTHWAVE_VARS + "}\n\n"
    ":root[data-theme=paper] {\n" + _PAPER_VARS + "}\n\n"
    ":root[data-theme=sepia] {\n" + _SEPIA_VARS + "}\n\n"
    "/* Map Pico's surface variables onto the active theme, so element styling\n"
    "   that Pico owns (table cells, cards, blockquotes, inline code) follows the\n"
    "   palette instead of Pico's own light/dark blocks. */\n"
    ":root, :root[data-theme] {\n"
    "  --pico-background-color: var(--bg);\n"
    "  --pico-card-background-color: var(--surface);\n"
    "  --pico-card-sectioning-background-color: var(--surface);\n"
    "  --pico-card-border-color: var(--border);\n"
    "  --pico-table-border-color: var(--border);\n"
    "  --pico-table-row-stripped-background-color: var(--table-row-hover);\n"
    "  --pico-muted-border-color: var(--border);\n"
    "  --pico-blockquote-border-color: var(--border);\n"
    "  --pico-code-background-color: var(--code-bg);\n"
    "  --pico-code-color: var(--code-fg);\n"
    "  --pico-secondary: var(--text-muted);\n"
    "  --pico-secondary-hover: var(--text);\n"
    "  --pico-contrast: var(--heading);\n"
    "}\n\n"
    "/* Printing always uses the paper palette, whatever theme is active. */\n"
    "@media print {\n  :root, :root[data-theme] {\n" + _PAPER_VARS + "  }\n}\n\n"
    "/* ── Theme picker (sidebar swatches) ───────────────────────────────── */\n"
    ".theme-picker {\n"
    "  display: flex; gap: .5rem; align-items: center;\n"
    "  padding: .15rem 1.25rem .7rem;\n"
    "}\n"
    ".theme-picker .theme-swatch {\n"
    "  width: 21px; height: 21px; border-radius: 50%;\n"
    "  border: 2px solid rgba(255,255,255,.28);\n"
    "  padding: 0; margin: 0; cursor: pointer; position: relative;\n"
    "  flex: 0 0 auto; box-shadow: none;\n"
    "}\n"
    ".theme-picker .theme-swatch .dot {\n"
    "  position: absolute; inset: 4px; border-radius: 50%; display: block;\n"
    "}\n"
    ".theme-picker .theme-swatch.sel {\n"
    "  border-color: var(--sidebar-active);\n"
    "  transform: scale(1.12);\n"
    "}\n"
    "@media print { .theme-picker { display: none !important; } }\n"
)

# Role styling that consumes the per-theme variables: gradient page/sidebar
# backgrounds, gradient h1, colored bold/italics/list markers, tinted table
# headers, gradient rules. Appended LAST so it wins over the base rules.
VIVID_CSS = """
/* ── Vivid role styling: multiple hues per theme ─────────────────────────── */

body { background: var(--bg-grad, var(--bg)); }
#sidebar { background: var(--sidebar-grad, var(--sidebar-bg)); }

@supports ((-webkit-background-clip: text) or (background-clip: text)) {
  main.content-wrap h1 {
    background: linear-gradient(92deg, var(--h1-grad-a, var(--heading)), var(--h1-grad-b, var(--heading)));
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    color: var(--heading);
  }
}

main.content-wrap strong { color: var(--strong-color, inherit); }
main.content-wrap em { color: var(--em-color, inherit); }
main.content-wrap li::marker { color: var(--marker-color, var(--accent)); font-weight: 700; }
main.content-wrap thead th { background: var(--thead-bg, var(--surface)); color: var(--thead-fg, var(--heading)); }
main.content-wrap hr { border: 0; height: 2px; background: var(--hr-grad, var(--border)); }
main.content-wrap a:hover { color: var(--link-hover, var(--accent)); }

@media print {
  body, #sidebar { background: #ffffff; }
  main.content-wrap h1 { background: none; -webkit-text-fill-color: initial; color: var(--heading); }
  main.content-wrap strong, main.content-wrap em { color: inherit; }
}

/* ── Attribution footer ───────────────────────────────────────────────────── */

footer.attribution {
  margin: 3rem 0 .5rem;
  text-align: center;
  font-size: .85em;
  color: var(--text-muted);
}
footer.attribution a { color: var(--text-muted); text-decoration: underline; }
footer.attribution a:hover { color: var(--link-hover, var(--accent)); }
"""

# Custom palette overrides (Pico's CSS variables), layered on the theme
# blocks above. Pico exposes ~80 vars; we only override the ones that matter
# for our visual identity.
PICO_OVERRIDES = THEME_CSS + """
html {
  scroll-behavior: smooth;
  scroll-padding-top: .5rem;       /* nicer landing for anchor links */
}

/* Defence in depth: prevent any wide child from triggering iOS Safari's
   "scale-to-fit-page" behavior (the symptom: body text appears tiny).
   Use `clip` instead of `hidden`; `overflow-x: hidden` on <body> breaks
   scroll-to-anchor on iOS Safari (clicking a TOC link does nothing).
   `clip` clips overflow without establishing a scroll container, which
   leaves the document's natural scroll/anchor behavior intact. */
body {
  overflow-x: clip;
  background: var(--bg);
  color: var(--text);
}

/* Each heading gets a small scroll-margin so when an anchor lands on it,
   it isn't pinned to viewport top under the mobile hamburger button. */
main.content-wrap :is(h1, h2, h3, h4) { scroll-margin-top: .75rem; }

/* ── Layout: fixed sidebar + flexible main ───────────────────────────────── */

main { padding-bottom: 5rem; }

.layout {
  display: flex;
  min-height: 100vh;
}

#main {
  flex: 1;
  padding: 2.5rem clamp(.75rem, 3vw, 2.5rem) 5rem;
  margin-left: 272px;     /* clear the sidebar on desktop */
}

main.content-wrap {
  /* Fill the available space (96% of the column beside the sidebar), with a
     880px floor for narrow viewports. Percentage-based so the card keeps
     absorbing the extra room a zoomed-out page or wide monitor creates,
     instead of shrinking inside fixed margins. */
  max-width: max(880px, 96%);
  margin: 0 auto;
  background: var(--surface);
  border-radius: 12px;
  padding: clamp(1.25rem, 4vw, 3rem) clamp(1rem, 5vw, 3.5rem);
  box-shadow: var(--shadow);
}

@media (max-width: 860px) {
  #main { margin-left: 0; padding: .75rem .65rem 4rem; }
  main.content-wrap {
    padding: 1.5rem 1.1rem 2rem;
    border-radius: 8px;
  }
}

/* ── Typography accents ─────────────────────────────────────────────────── */

main.content-wrap h1 {
  font-size: clamp(1.55rem, 1.2rem + 1.6vw, 2.1rem);
  font-weight: 800;
  color: var(--heading);
  letter-spacing: -.02em;
  margin-bottom: .4rem;
  line-height: 1.2;
}

main.content-wrap h2 {
  font-size: clamp(1.25rem, 1rem + 0.9vw, 1.55rem);
  font-weight: 700;
  color: var(--heading);
  margin: 2.2rem 0 .8rem;
  padding-left: .75rem;
  border-left: 4px solid var(--accent);
  line-height: 1.3;
}

main.content-wrap h3 {
  font-size: clamp(1.1rem, 1rem + 0.4vw, 1.25rem);
  font-weight: 600;
  color: var(--accent2);
  margin: 1.4rem 0 .55rem;
}

main.content-wrap h4 {
  font-size: clamp(1rem, 0.95rem + 0.2vw, 1.1rem);
  font-weight: 600;
  color: var(--text);
  margin: 1.1rem 0 .4rem;
}

main.content-wrap p { margin: .65rem 0; }
main.content-wrap ul, main.content-wrap ol { padding-left: 1.4rem; margin: .65rem 0; }
main.content-wrap li { margin: .35rem 0; }
main.content-wrap hr { border: none; border-top: 1px solid var(--border); margin: 2rem 0; }

main.content-wrap blockquote {
  border-left: 4px solid var(--accent);
  background: var(--quiz-bg);
  padding: .75rem 1rem;
  margin: 1rem 0;
  border-radius: 0 6px 6px 0;
  color: var(--text-muted);
  font-style: italic;
}

.subtitle {
  font-size: 1.05rem;
  color: var(--text-muted);
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 2px solid var(--border);
  font-style: normal;
}
.subtitle p { margin: 0; }

main.content-wrap a {
  color: var(--accent);
  text-decoration: none;
  --pico-text-decoration: none;
}
main.content-wrap a:hover { text-decoration: underline; }

/* Inline code (Pico styles <code> reasonably; tighten visual treatment) */
main.content-wrap :not(pre) > code {
  font-family: "Roboto Mono", "JetBrains Mono", "Cascadia Code", "Menlo",
               monospace;
  font-size: .87em;
  background: var(--ic-bg);
  color: var(--ic-fg);
  padding: .12em .38em;
  border-radius: 4px;
}

/* ── Code blocks (Pygments output) ──────────────────────────────────────── */

.codehilite {
  background: var(--code-bg) !important;
  border-radius: 8px;
  margin: 1rem 0;
  border: 1px solid var(--code-border);
  overflow: hidden;
}

.codehilite pre, main.content-wrap pre {
  background: var(--code-bg) !important;
  border: 1px solid var(--code-border);
  border-radius: 8px;
  margin: 1rem 0;
  padding: 1rem 1.25rem;
  overflow-x: auto;
  color: var(--code-fg);
  font-size: clamp(.85rem, 0.78rem + 0.3vw, .92rem);
  line-height: 1.55;
}

.codehilite pre {
  background: transparent !important;
  border: none;
  margin: 0;
  border-radius: 0;
}

.codehilite pre code, main.content-wrap pre code {
  background: none;
  color: inherit;
  padding: 0;
  font-size: inherit;
}

main.content-wrap p code, main.content-wrap li code { word-break: break-word; }

/* ── Tables ─────────────────────────────────────────────────────────────── */

main.content-wrap table {
  width: 100%;
  border-collapse: collapse;
  margin: 1rem 0;
  font-size: .92rem;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: var(--shadow);
}
main.content-wrap th {
  background: var(--sidebar-bg);
  color: var(--sidebar-head);
  padding: .55rem .85rem;
  text-align: left;
  font-weight: 600;
  font-size: .88rem;
}
main.content-wrap td {
  padding: .5rem .85rem;
  border-bottom: 1px solid var(--border);
  color: var(--text);
}
main.content-wrap tbody tr:last-child td { border-bottom: none; }
main.content-wrap tbody tr:hover td { background: var(--table-row-hover); }

.table-wrapper {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  margin: 1rem 0;
  border-radius: 8px;
  box-shadow: var(--shadow);
}
.table-wrapper table { margin: 0; box-shadow: none; border-radius: 0; }

/* ── Sidebar ────────────────────────────────────────────────────────────── */

#sidebar {
  width: 272px;
  background: var(--sidebar-bg);
  position: fixed;
  top: 0; left: 0; bottom: 0;
  overflow-y: auto;
  padding: 1.5rem 0 2rem;
  z-index: 100;
  transition: transform .25s ease;
}
#sidebar .sidebar-label {
  color: var(--sidebar-head);
  font-size: .7rem;
  font-weight: 700;
  letter-spacing: .1em;
  text-transform: uppercase;
  padding: 0 1.25rem .75rem;
  border-bottom: 1px solid rgba(255,255,255,.08);
  margin-bottom: .75rem;
}
/* Pico styles <nav> as a horizontal flex row of links; undo that for the
   sidebar so headings stack vertically. */
#sidebar nav {
  display: block;
  flex-direction: column;
  padding: 0;
  margin: 0;
  width: 100%;
}
#sidebar nav ul,
#sidebar nav ol {
  display: block;
  list-style: none;
  margin: 0;
  padding: 0;
}
#sidebar nav li { display: block; margin: 0; padding: 0; }
#sidebar nav a {
  display: block;
  width: 100%;
  color: var(--sidebar-text);
  text-decoration: none;
  --pico-text-decoration: none;
  padding: .35rem 1.25rem;
  font-size: .9rem;
  border-left: 2px solid transparent;
  line-height: 1.4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: color .13s, background .13s, border-color .13s;
  flex: none;       /* in case Pico's flex still applies somewhere */
}
#sidebar nav a:hover { color: #fff; background: var(--sidebar-hover); text-decoration: none; }
#sidebar nav a.h2-link { color: #afc9e8; padding-left: 1.5rem; font-weight: 500; }
#sidebar nav a.h3-link { padding-left: 2.4rem; font-size: .85rem; }
#sidebar nav a.active {
  color: var(--sidebar-active) !important;
  border-left-color: var(--sidebar-active);
  background: rgba(96,165,250,.12);
}

@media (max-width: 860px) {
  /* Sidebar slides in. min-width MUST be 0 to stop iOS treating the
     off-screen sidebar as a "minimum content width" floor. */
  #sidebar {
    transform: translateX(-100%);
    width: 88vw;
    min-width: 0;
    max-width: 320px;
  }
  #sidebar.open { transform: translateX(0); box-shadow: 4px 0 24px rgba(0,0,0,.35); }
}

#mobile-nav-toggle {
  display: none;
  position: fixed;
  top: .8rem; left: .8rem;
  z-index: 200;
  background: var(--sidebar-bg);
  color: var(--sidebar-head);
  border: none;
  border-radius: 8px;
  width: 2.6rem; height: 2.6rem;
  font-size: 1.25rem;
  cursor: pointer;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 10px rgba(0,0,0,.25);
  line-height: 1;
}
@media (max-width: 860px) { #mobile-nav-toggle { display: flex; } }

#sidebar-overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.45);
  z-index: 99;
}
#sidebar-overlay.open { display: block; }

/* ── Images and lightbox ────────────────────────────────────────────────── */

main.content-wrap img {
  max-width: 100%;
  height: auto;
  display: block;
  margin: 1.5rem auto;
  border-radius: 8px;
  box-shadow: var(--shadow);
  background: #ffffff;
  cursor: zoom-in;
}

/* Tall/narrow diagrams (e.g. a vertical stack of a few boxes) look absurd blown
   up to the full column; the text inside inflates with them. Cap their display
   width and keep them centered. Tagged automatically by aspect ratio in
   embed_images(). The qualified selector outranks the rule above. */
main.content-wrap img.img-portrait {
  max-width: min(100%, 380px);
}

/* ── Code listings (captioned, line-numbered figures, perfbook style) ─────── */
figure.code-listing {
  margin: 1.5rem 0;
  border: 1px solid var(--code-border);
  border-radius: 8px;
  overflow: hidden;
  background: var(--code-bg);
  box-shadow: var(--shadow);
}
figure.code-listing > figcaption {
  background: var(--surface);
  color: var(--sidebar-head);
  font-size: .84rem;
  font-weight: 600;
  padding: .5rem .9rem;
  border-bottom: 1px solid var(--code-border);
}
/* the Pygments table renderer nested inside the figure carries no box of its own */
figure.code-listing .codehilite {
  margin: 0;
  border: none;
  border-radius: 0;
}
figure.code-listing table.codehilitetable {
  width: 100%;
  border-collapse: collapse;
  display: block;
  overflow-x: auto;
}
figure.code-listing td.linenos,
figure.code-listing .linenos {
  color: var(--text-muted);
  text-align: right;
  padding: 0 .8rem 0 .6rem;
  user-select: none;
  -webkit-user-select: none;
  white-space: nowrap;
  border-right: 1px solid var(--code-border);
  width: 1%;
}
figure.code-listing td.code { width: 100%; }
figure.code-listing td.code pre { margin: 0; }
@media (max-width: 600px) {
  figure.code-listing td.linenos { padding: 0 .45rem; font-size: .8rem; }
  figure.code-listing > figcaption { font-size: .8rem; padding: .4rem .6rem; }
}
@media print { figure.code-listing { break-inside: avoid; } }

@media (max-width: 860px) {
  main.content-wrap img {
    margin: 1rem -.5rem;
    max-width: calc(100% + 1rem);
    border-radius: 4px;
  }
}
@media (max-width: 480px) {
  main.content-wrap img {
    margin: .85rem -.9rem;
    max-width: calc(100% + 1.8rem);
    border-radius: 0;
    box-shadow: none;
    border-top: 1px solid var(--border);
    border-bottom: 1px solid var(--border);
  }
}

.lightbox {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.85);
  z-index: 500;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  cursor: zoom-out;
}
.lightbox.open { display: flex; }
.lightbox img {
  max-width: 100%;
  max-height: 100%;
  background: #fff;
  border-radius: 6px;
  box-shadow: 0 12px 40px rgba(0,0,0,.6);
  cursor: default;
}
.lightbox-close {
  position: absolute;
  top: 1rem; right: 1rem;
  background: rgba(255,255,255,.9);
  color: #111;
  border: none;
  border-radius: 50%;
  width: 2.6rem; height: 2.6rem;
  font-size: 1.5rem;
  line-height: 1;
  cursor: pointer;
  font-weight: 700;
}

/* ── Quiz callout boxes ─────────────────────────────────────────────────── */

.quiz-section {
  background: var(--quiz-bg);
  border-left: 4px solid var(--quiz-border);
  border-radius: 0 8px 8px 0;
  padding: 1rem 1.25rem;
  margin: 1.5rem 0;
}
.quiz-section h3 { color: var(--accent); margin-top: 0; }
.quiz-section p, .quiz-section li, .quiz-section { color: var(--text); }
.quiz-section p a[href^="#answer-key"] {
  display: inline-block;
  font-weight: 600;
  color: var(--accent2);
  padding: .2rem .55rem;
  background: var(--quiz-text-link-bg);
  border-radius: 4px;
  font-size: .92rem;
  text-decoration: none;
}

/* ── Answer key (collapsible) ───────────────────────────────────────────── */

details.answer-key-section {
  border: 1px solid var(--ans-sum-bg);
  border-left: 4px solid var(--ans-border);
  border-radius: 0 8px 8px 0;
  margin: .75rem 0;
  overflow: hidden;
}
details.answer-key-section > summary {
  background: var(--ans-sum-bg);
  padding: .7rem 1rem;
  cursor: pointer;
  font-weight: 600;
  font-size: 1rem;
  color: var(--ans-sum-text);
  user-select: none;
  list-style: none;
  display: flex;
  align-items: center;
  gap: .5rem;
}
details.answer-key-section > summary::-webkit-details-marker { display: none; }
details.answer-key-section > summary::before {
  content: "\\25B6";
  font-size: .65em;
  transition: transform .2s ease;
  color: var(--ans-border);
  flex-shrink: 0;
}
details.answer-key-section[open] > summary::before { transform: rotate(90deg); }
.answer-body {
  padding: 1rem 1.25rem;
  background: var(--ans-body-bg);
  color: var(--text);
}
.answer-body p, .answer-body li { color: var(--text); }
.answer-body p a { color: var(--ans-border); font-weight: 600; }

/* ── Optional deep-dive sections (collapsible) ──────────────────────────── */

details.optional-section {
  border: 1px solid var(--opt-sum-bg);
  border-left: 4px solid var(--opt-border);
  border-radius: 0 8px 8px 0;
  margin: 1.25rem 0;
  overflow: hidden;
}
details.optional-section > summary {
  background: var(--opt-sum-bg);
  padding: .7rem 1rem;
  cursor: pointer;
  font-weight: 600;
  font-size: 1rem;
  color: var(--opt-sum-text);
  user-select: none;
  list-style: none;
  display: flex;
  align-items: center;
  gap: .5rem;
}
details.optional-section > summary::-webkit-details-marker { display: none; }
details.optional-section > summary::before {
  content: "\\25B6";
  font-size: .65em;
  transition: transform .2s ease;
  color: var(--opt-border);
  flex-shrink: 0;
}
details.optional-section[open] > summary::before { transform: rotate(90deg); }
.optional-body {
  padding: 1rem 1.25rem;
  background: var(--opt-body-bg);
  color: var(--text);
}
.optional-body p, .optional-body li { color: var(--text); }

/* ── Meta info block (Time / Difficulty / Exam) ─────────────────────────── */

.meta-block {
  background: var(--meta-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: .75rem 1.1rem;
  margin: 1rem 0 2rem;
  color: var(--text);
}
.meta-block p { margin: .2rem 0; color: var(--text); }

/* ── Exam CTA button ────────────────────────────────────────────────────── */

.exam-cta { text-align: center; margin: 2rem 0; }
.exam-cta a {
  display: inline-block;
  background: var(--accent);
  color: #fff !important;
  padding: .3rem .85rem;
  border-radius: 5px;
  font-weight: 600;
  font-size: .9rem;
  text-decoration: none !important;
  box-shadow: 0 2px 6px rgba(37,99,235,.2);
  transition: background .15s, transform .1s;
}
.exam-cta a:hover { background: #1d4ed8; transform: translateY(-1px); }
/* Inside .meta-block, links are inline within prose; render as text links, not buttons. */
.meta-block .exam-cta { text-align: left; margin: 0; }
.meta-block .exam-cta a {
  display: inline;
  background: transparent;
  color: var(--accent) !important;
  padding: 0;
  border-radius: 0;
  font-weight: 600;
  font-size: inherit;
  text-decoration: underline !important;
  box-shadow: none;
}
.meta-block .exam-cta a:hover { background: transparent; transform: none; }
@media (max-width: 860px) {
  .exam-cta a { padding: .35rem .85rem; }
}

/* ── Print ──────────────────────────────────────────────────────────────── */

@media print {
  .lightbox, #mobile-nav-toggle, #sidebar-overlay { display: none !important; }
  #sidebar { display: none; }
  #main { margin-left: 0; }
  main.content-wrap { box-shadow: none; padding: 0; }
}

/* ── MathML (rendered from LaTeX by latex2mathml) ───────────────────────── */

math[display="block"] {
  display: block;
  margin: 1.1rem auto;
  font-size: 1.18em;
  text-align: center;
}
math { font-family: "STIX Two Math", "Latin Modern Math", "Cambria Math", serif; }

/* ── Copy-code buttons ──────────────────────────────────────────────────── */

main pre { position: relative; }
.code-copy-btn {
  position: absolute;
  top: .4rem;
  right: .4rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.9rem;
  height: 1.9rem;
  padding: 0;
  margin: 0;
  border: 1px solid rgba(255, 255, 255, .25);
  border-radius: 6px;
  background: rgba(255, 255, 255, .08);
  color: #c9d1d9;
  cursor: pointer;
  opacity: .55;
  transition: opacity .15s, background .15s;
  box-shadow: none;
}
.code-copy-btn:hover { opacity: 1; background: rgba(255, 255, 255, .18); }
.code-copy-btn svg { width: 1rem; height: 1rem; display: block; }
.code-copy-btn.copied { color: #4ade80; border-color: #4ade80; opacity: 1; }
@media (max-width: 860px) { .code-copy-btn { opacity: .8; } }
@media print { .code-copy-btn { display: none !important; } }
""" + VIVID_CSS

# ── Sidebar scroll-highlight JS ──────────────────────────────────────────────

SIDEBAR_JS = r"""
(function () {
  var sidebar = document.getElementById('sidebar');
  var overlay = document.getElementById('sidebar-overlay');
  var toggle  = document.getElementById('mobile-nav-toggle');
  if (!sidebar) return;

  // ── Mobile open/close ──────────────────────────────────────────────────
  function openSidebar() {
    sidebar.classList.add('open');
    if (overlay) overlay.classList.add('open');
    document.body.style.overflow = 'hidden';
  }
  function closeSidebar() {
    sidebar.classList.remove('open');
    if (overlay) overlay.classList.remove('open');
    document.body.style.overflow = '';
  }
  if (toggle)  toggle.addEventListener('click', openSidebar);
  if (overlay) overlay.addEventListener('click', closeSidebar);

  // ── Theme picker ───────────────────────────────────────────────────────
  var swatches = Array.from(sidebar.querySelectorAll('.theme-swatch'));
  function markTheme() {
    var cur = document.documentElement.getAttribute('data-theme') || 'aurora';
    swatches.forEach(function (b) {
      b.classList.toggle('sel', b.getAttribute('data-theme-pick') === cur);
    });
  }
  swatches.forEach(function (b) {
    b.addEventListener('click', function () {
      var t = b.getAttribute('data-theme-pick');
      document.documentElement.setAttribute('data-theme', t);
      try { localStorage.setItem('handson-theme', t); } catch (e) {}
      markTheme();
    });
  });
  markTheme();

  // ── Scroll-position highlight ──────────────────────────────────────────
  var links = Array.from(sidebar.querySelectorAll('nav a'));
  var targets = links.map(function (a) {
    return document.getElementById(a.getAttribute('href').slice(1));
  }).filter(Boolean);

  // ── TOC link click handler ─────────────────────────────────────────────
  // We take over the scroll instead of letting the browser's default
  // anchor-scroll fire. Reasons:
  //   1. On mobile, openSidebar() puts `overflow: hidden` on <body>. When the
  //      user taps a TOC link, the click handler removes that lock and the
  //      browser then tries to do its native anchor-scroll. iOS Safari
  //      INTERMITTENTLY misfires this (the scroll target is computed against
  //      the locked-state document); symptom: only some anchors land in the
  //      right place.
  //   2. If a target is inside a collapsed <details> (answer-key sections),
  //      we must open it BEFORE scrolling, otherwise the bounding rect is
  //      wrong.
  //   3. A double-rAF after closeSidebar() lets layout settle (body overflow
  //      restored, sidebar transition started) before we read positions.
  links.forEach(function (a) {
    a.addEventListener('click', function (e) {
      var hash = a.getAttribute('href') || '';
      if (hash.charAt(0) !== '#' || hash.length < 2) return;
      var target = document.getElementById(hash.slice(1));
      if (!target) return;

      e.preventDefault();

      // Reflect the new hash in the URL (so back/forward and refresh work)
      // without triggering a default scroll.
      if (history.pushState) history.pushState(null, '', hash);

      // Open any collapsed <details> ancestor so the target is in flow.
      var d = target.closest ? target.closest('details') : null;
      if (d && !d.open) d.open = true;

      if (window.innerWidth <= 860) closeSidebar();

      requestAnimationFrame(function () {
        requestAnimationFrame(function () {
          var rect = target.getBoundingClientRect();
          var top  = rect.top + window.pageYOffset - 8;
          window.scrollTo({ top: top, behavior: 'smooth' });
        });
      });
    });
  });

  var current = null;

  function activate(el) {
    if (current === el) return;
    current = el;
    links.forEach(function (a) { a.classList.remove('active'); });
    var a = sidebar.querySelector('a[href="#' + el.id + '"]');
    if (!a) return;
    a.classList.add('active');
    var sRect = sidebar.getBoundingClientRect();
    var aRect = a.getBoundingClientRect();
    if (aRect.top < sRect.top + 48 || aRect.bottom > sRect.bottom - 48) {
      a.scrollIntoView({ block: 'nearest' });
    }
  }

  function onScroll() {
    var scrollY = window.scrollY + 130;
    var active = targets[0];
    for (var i = 0; i < targets.length; i++) {
      if (targets[i] && targets[i].getBoundingClientRect().top + window.scrollY <= scrollY) {
        active = targets[i];
      }
    }
    if (active) activate(active);
  }

  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // ── Diagram lightbox: tap any image inside .content-wrap to enlarge ────
  var lightbox = document.getElementById('lightbox');
  var lbImg    = lightbox ? lightbox.querySelector('img') : null;
  var lbClose  = lightbox ? lightbox.querySelector('.lightbox-close') : null;
  if (lightbox && lbImg) {
    document.querySelectorAll('.content-wrap img').forEach(function (img) {
      img.addEventListener('click', function () {
        lbImg.src = img.src;
        lbImg.alt = img.alt || '';
        lightbox.classList.add('open');
        document.body.style.overflow = 'hidden';
      });
    });
    function closeLb() {
      lightbox.classList.remove('open');
      lbImg.src = '';
      document.body.style.overflow = '';
    }
    lightbox.addEventListener('click', function (e) { if (e.target === lightbox) closeLb(); });
    if (lbClose) lbClose.addEventListener('click', closeLb);
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && lightbox.classList.contains('open')) closeLb();
    });
  }
})();

/* ── Copy-code buttons ─────────────────────────────────────────────────────
   Adds a copy icon to every <pre> block. Uses the async clipboard API on
   secure contexts and a hidden-textarea fallback elsewhere (the common case
   for plain-HTTP LAN/tailscale hosting). */
(function () {
  var COPY_SVG =
    '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4">' +
    '<rect x="5.5" y="5.5" width="8" height="8" rx="1.5"/>' +
    '<path d="M10.5 3.5v-1a1 1 0 0 0-1-1h-6a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h1"/></svg>';
  var CHECK_SVG =
    '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8">' +
    '<path d="M2.5 8.5l3.5 3.5 7-8"/></svg>';

  function copyText(text, done) {
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(done, function () { fallback(text, done); });
    } else {
      fallback(text, done);
    }
  }
  function fallback(text, done) {
    var ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand('copy'); } catch (e) {}
    document.body.removeChild(ta);
    done();
  }

  document.querySelectorAll('main pre').forEach(function (pre) {
    // a table line-number gutter is its own <pre>; don't add a copy button to it
    if (pre.closest('td.linenos, .linenodiv')) { return; }
    var btn = document.createElement('button');
    btn.className = 'code-copy-btn';
    btn.type = 'button';
    btn.title = 'Copy code';
    btn.setAttribute('aria-label', 'Copy code');
    btn.innerHTML = COPY_SVG;
    btn.addEventListener('click', function () {
      var clone = pre.cloneNode(true);
      var b = clone.querySelector('.code-copy-btn');
      if (b) b.remove();
      copyText(clone.innerText.replace(/\n+$/, '\n'), function () {
        btn.classList.add('copied');
        btn.innerHTML = CHECK_SVG;
        setTimeout(function () {
          btn.classList.remove('copied');
          btn.innerHTML = COPY_SVG;
        }, 1500);
      });
    });
    pre.appendChild(btn);
  });
})();
"""


# ── Helpers ──────────────────────────────────────────────────────────────────

# LaTeX math support: $$...$$ (display) and \(...\) (inline) are extracted from
# the raw markdown BEFORE the markdown engine runs (markdown would mangle
# backslash escapes like \( and \! and may treat _ as emphasis), replaced with
# placeholder tokens, then injected back into the soup as native MathML via
# latex2mathml. Bare $...$ is deliberately unsupported (false positives on
# prices). Fenced code blocks and inline code spans are left untouched.

_MATH_TOKEN = '%%MATHML{}%%'
_MATH_TOKEN_RE = re.compile(r'%%MATHML(\d+)%%')
_MATH_SPAN_RE = re.compile(r'\$\$(.+?)\$\$|\\\((.+?)\\\)', re.DOTALL)
_FENCE_RE = re.compile(r'(?ms)^(?P<f>```|~~~)[^\n]*\n.*?^(?P=f)[ \t]*$')
_INLINE_CODE_RE = re.compile(r'`[^`\n]+`')


def render_math_prepare(md_text):
    """Replace LaTeX math spans (outside code) with placeholder tokens.

    Returns (new_md_text, stash) where stash is a list of (latex, display)
    tuples indexed by token number. If latex2mathml is unavailable, returns
    the text unchanged with an empty stash (and warns if math is present).
    """
    try:
        import latex2mathml.converter  # noqa: F401
    except ImportError:
        if '$$' in md_text or r'\(' in md_text:
            print('WARNING: latex2mathml not installed, LaTeX math left as '
                  'plain text. Fix: pip install latex2mathml')
        return md_text, []

    stash = []

    def _extract(segment):
        def repl(m):
            latex = m.group(1) if m.group(1) is not None else m.group(2)
            display = 'block' if m.group(1) is not None else 'inline'
            stash.append((latex.strip(), display))
            return _MATH_TOKEN.format(len(stash) - 1)
        # protect inline code spans within this non-fenced segment
        code_spans = []
        def stash_code(m):
            code_spans.append(m.group(0))
            return '%%CODESPAN{}%%'.format(len(code_spans) - 1)
        segment = _INLINE_CODE_RE.sub(stash_code, segment)
        segment = _MATH_SPAN_RE.sub(repl, segment)
        for i, span in enumerate(code_spans):
            segment = segment.replace('%%CODESPAN{}%%'.format(i), span)
        return segment

    out, last = [], 0
    for m in _FENCE_RE.finditer(md_text):
        out.append(_extract(md_text[last:m.start()]))
        out.append(m.group(0))          # fenced code: untouched
        last = m.end()
    out.append(_extract(md_text[last:]))
    return ''.join(out), stash


def render_math_inject(soup, stash):
    """Replace placeholder tokens in text nodes with MathML elements."""
    if not stash:
        return
    from latex2mathml.converter import convert as _l2m
    for node in list(soup.find_all(string=_MATH_TOKEN_RE)):
        s = str(node)
        parts, last = [], 0
        for m in _MATH_TOKEN_RE.finditer(s):
            if m.start() > last:
                parts.append(s[last:m.start()])
            idx = int(m.group(1))
            latex, display = stash[idx]
            try:
                mathml = _l2m(latex, display=display)
                frag = BeautifulSoup(mathml, 'html.parser')
                parts.extend(list(frag.contents))
            except Exception as e:  # leave the raw LaTeX visible rather than dying
                print(f'WARNING: latex2mathml failed on {latex[:60]!r}: {e}')
                parts.append(('$$%s$$' if display == 'block' else r'\(%s\)') % latex)
            last = m.end()
        parts.append(s[last:])
        for p in parts:
            node.insert_before(p)
        node.extract()


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def ensure_heading_ids(soup):
    counts = {}
    for tag in soup.find_all(['h1', 'h2', 'h3', 'h4']):
        if tag.get('id'):
            continue
        slug = slugify(tag.get_text())
        base = slug
        if slug in counts:
            counts[slug] += 1
            slug = f'{slug}-{counts[slug]}'
        else:
            counts[slug] = 0
        tag['id'] = slug


def _png_dimensions(data):
    """Return (width, height) for PNG bytes, or None. Reads the IHDR chunk -
    no PIL dependency."""
    if len(data) >= 24 and data[:8] == b'\x89PNG\r\n\x1a\n' and data[12:16] == b'IHDR':
        return (int.from_bytes(data[16:20], 'big'),
                int.from_bytes(data[20:24], 'big'))
    return None


def embed_images(soup, base_dir, embed=True):
    MIME = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
            '.svg': 'image/svg+xml', '.gif': 'image/gif', '.webp': 'image/webp'}
    for img in soup.find_all('img'):
        src = img.get('src', '')
        if not src or src.startswith('data:') or src.startswith('http'):
            continue
        p = base_dir / src
        if not p.exists():
            continue
        raw = p.read_bytes()
        # Tall/narrow diagrams (a vertical stack of a few boxes) blow up their
        # own text when stretched to the full column width. Tag portrait PNGs so
        # the stylesheet can cap their display width (see .img-portrait).
        dims = _png_dimensions(raw)
        if dims and dims[1] > dims[0] * 1.25:
            img['class'] = img.get('class', []) + ['img-portrait']
        if not embed:
            continue
        mime = MIME.get(p.suffix.lower(), 'image/png')
        data = base64.b64encode(raw).decode()
        img['src'] = f'data:{mime};base64,{data}'


def build_sidebar(soup):
    items = []
    for tag in soup.find_all(['h2', 'h3']):
        hid = tag.get('id')
        text = tag.get_text(strip=True)
        if not hid or not text:
            continue
        if hid.startswith('optional--'):
            continue   # collapsed deep-dives stay out of the nav
        items.append((tag.name, text, hid))

    if not items:
        return ''

    lines = []
    for level, text, hid in items:
        css = 'h2-link' if level == 'h2' else 'h3-link'
        # Truncate long text for sidebar
        display = text if len(text) <= 46 else text[:43] + '…'
        lines.append(f'<a class="{css}" href="#{hid}" title="{text}">{display}</a>\n')

    nav = '    '.join(lines)
    return (
        '<div id="sidebar">\n'
        '  <div class="sidebar-label">Contents</div>\n'
        f'{theme_picker_html()}'
        f'  <nav>\n    {nav}  </nav>\n'
        '</div>\n'
    )


def wrap_quiz_sections(soup):
    """Wrap Quiz-N h3 + following siblings (until next heading/hr) in .quiz-section."""
    for h3 in list(soup.find_all('h3', id=lambda x: x and x.startswith('quiz-'))):
        siblings = []
        for sib in h3.next_siblings:
            if isinstance(sib, Tag) and sib.name in ('h2', 'h3', 'h4', 'hr'):
                break
            siblings.append(sib)
        wrapper = soup.new_tag('div', **{'class': 'quiz-section'})
        h3.insert_before(wrapper)
        wrapper.append(h3.extract())
        for s in siblings:
            wrapper.append(s.extract())


def wrap_answer_key_sections(soup):
    """Wrap answer-key-module-N h3 + content in collapsible <details>."""
    for h3 in list(soup.find_all('h3', id=lambda x: x and x.startswith('answer-key--module-'))):
        hid = h3.get('id')
        siblings = []
        for sib in h3.next_siblings:
            if isinstance(sib, Tag) and sib.name in ('h2', 'h3', 'h4', 'hr'):
                break
            siblings.append(sib)

        title = h3.get_text(strip=True)
        details = soup.new_tag('details', **{'class': 'answer-key-section', 'id': hid})
        summary = soup.new_tag('summary')
        summary.string = title
        body_div = soup.new_tag('div', **{'class': 'answer-body'})
        details.append(summary)
        details.append(body_div)

        h3.insert_before(details)
        h3.extract()  # id moved to <details>
        for s in siblings:
            body_div.append(s.extract())


def wrap_optional_sections(soup):
    """Wrap h3/h4s whose id starts with "optional--" (plus their content, up
    to the next heading/hr) in a collapsible <details class="optional-section">.

    Authors opt in with an explicit anchor:

        ### How was this measured? {#optional--how-measured-2}

    This keeps deep-dive material (instrumentation, full implementations,
    long derivations) available but out of the main teaching path: the
    reader sees one click-to-expand summary line instead of a page of
    harness code. Links that target ids inside the collapsed body still
    work; the anchor JS opens the ancestor <details> on navigation."""
    for hx in list(soup.find_all(['h3', 'h4'],
                                 id=lambda x: x and x.startswith('optional--'))):
        siblings = []
        for sib in hx.next_siblings:
            if isinstance(sib, Tag) and sib.name in ('h2', 'h3', 'h4', 'hr'):
                break
            siblings.append(sib)

        title = hx.get_text(strip=True)
        details = soup.new_tag('details', **{'class': 'optional-section',
                                             'id': hx.get('id')})
        summary = soup.new_tag('summary')
        summary.string = title
        body_div = soup.new_tag('div', **{'class': 'optional-body'})
        details.append(summary)
        details.append(body_div)

        hx.insert_before(details)
        hx.extract()  # id moved to <details>
        for s in siblings:
            body_div.append(s.extract())


def style_meta_block(soup):
    """Wrap the Time/Difficulty/Exam bold-paragraphs after h1 in a meta-block."""
    h1 = soup.find('h1')
    if not h1:
        return

    # Mark first blockquote (the > subtitle) as subtitle
    nxt = h1.find_next_sibling()
    if nxt and nxt.name == 'blockquote':
        nxt['class'] = nxt.get('class', []) + ['subtitle']
        nxt = nxt.find_next_sibling()

    # Collect consecutive <p> that start with <strong> (meta lines)
    meta_ps = []
    cur = nxt
    while cur and isinstance(cur, Tag) and cur.name == 'p':
        strong = cur.find('strong')
        if strong and cur.get_text(strip=True)[:5] == strong.get_text(strip=True)[:5]:
            meta_ps.append(cur)
            cur = cur.find_next_sibling()
        else:
            break

    if meta_ps:
        wrapper = soup.new_tag('div', **{'class': 'meta-block'})
        meta_ps[0].insert_before(wrapper)
        for p in meta_ps:
            wrapper.append(p.extract())


def wrap_tables(soup):
    """Wrap tables in .table-wrapper for horizontal scroll on mobile."""
    for table in soup.find_all('table'):
        if table.find_parent(class_='table-wrapper'):
            continue
        wrapper = soup.new_tag('div', **{'class': 'table-wrapper'})
        table.insert_before(wrapper)
        wrapper.append(table.extract())


def style_exam_links(soup):
    """Wrap paragraphs that link to exam.html in .exam-cta."""
    for a in soup.find_all('a', href=lambda x: x and 'exam.html' in x):
        p = a.find_parent('p')
        if p and 'exam-cta' not in p.get('class', []):
            p['class'] = p.get('class', []) + ['exam-cta']


def get_pygments_css():
    for style_name in ('github-dark', 'one-dark', 'monokai', 'native'):
        try:
            style = get_style_by_name(style_name)
            return HtmlFormatter(style=style).get_style_defs('.codehilite')
        except Exception:
            continue
    return ''


# ── Main conversion ──────────────────────────────────────────────────────────

def load_pico_css():
    """Load Pico.css classless from disk; warn if missing."""
    if not PICO_CSS_PATH.exists():
        print(f'WARNING: {PICO_CSS_PATH} missing, falling back to overrides only.',
              file=sys.stderr)
        return ''
    return PICO_CSS_PATH.read_text(encoding='utf-8')


def convert(md_path: Path, out_path: Path, embed_img: bool = True):
    md_text = md_path.read_text(encoding='utf-8')
    base_dir = md_path.parent

    md_text, math_stash = render_math_prepare(md_text)

    md_engine = markdown.Markdown(
        extensions=['extra', 'codehilite'],
        extension_configs={
            'codehilite': {
                'guess_lang': False,
                'linenums': False,
                'use_pygments': True,
            }
        },
    )
    body_html = md_engine.convert(md_text)

    soup = BeautifulSoup(body_html, 'html.parser')

    render_math_inject(soup, math_stash)
    ensure_heading_ids(soup)

    # Build sidebar BEFORE structural wrapping (all h3 ids still on h3 elements)
    sidebar_html = build_sidebar(soup)

    embed_images(soup, base_dir, embed=embed_img)
    style_meta_block(soup)
    style_exam_links(soup)
    wrap_tables(soup)
    wrap_quiz_sections(soup)
    wrap_answer_key_sections(soup)  # moves answer-key--module-N id from h3 → <details>
    wrap_optional_sections(soup)    # moves optional--* id from h3/h4 → <details>

    title_tag = soup.find('h1')
    title_text = title_tag.get_text(strip=True) if title_tag else md_path.stem

    pico_css = load_pico_css()
    pygments_css = get_pygments_css()
    content_html = str(soup)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="format-detection" content="telephone=no">
<title>{title_text}</title>
<script>{THEME_HEAD_JS}</script>
<style>
/* ── Pico.css 2.x (classless base, MIT licensed) ─────────────────────────── */
{pico_css}

/* ── Workshop overrides ──────────────────────────────────────────────────── */
{PICO_OVERRIDES}

/* ── Pygments code highlighting (github-dark) ────────────────────────────── */
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
{ATTRIBUTION_HTML}
  </main>
</div>
<div id="lightbox" class="lightbox" role="dialog" aria-label="Enlarged diagram">
  <button class="lightbox-close" aria-label="Close">&times;</button>
  <img alt="">
</div>
<script>
{SIDEBAR_JS}
</script>
</body>
</html>
"""

    out_path.write_text(html, encoding='utf-8')
    kb = out_path.stat().st_size // 1024
    print(f'Written: {out_path}  ({kb} KB)')


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('md_file', help='Path to WORKSHOP.md')
    ap.add_argument('-o', '--output',
                    help='Output path (default: WORKSHOP.html beside the .md)')
    ap.add_argument('--no-embed-images', action='store_true',
                    help='Keep image src as relative paths instead of base64')
    args = ap.parse_args()

    md_path = Path(args.md_file).resolve()
    if not md_path.exists():
        sys.exit(f'Error: {md_path} not found')

    out_path = Path(args.output).resolve() if args.output else md_path.with_suffix('.html')
    convert(md_path, out_path, embed_img=not args.no_embed_images)


if __name__ == '__main__':
    main()
