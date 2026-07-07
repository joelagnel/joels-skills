# D2 Diagrams (with ELK layout + Roboto Mono)

D2 is the **first-preference** format for architecture diagrams.
It's vector source, deterministic layout, fine-grained styling, and renders
sharper than Mermaid at any zoom level. This file is the recipe.

## When to use D2

- Any architecture diagram, block diagram, layered system diagram
- Anything with > 5 boxes or > 3 levels of containment
- Anything you want to read clearly when GitHub renders the markdown column at ~1000px
- Anything where you want to control colours per-shape

## When to fall back

- Pure text-flow / no-graphic-needed → drop the diagram entirely
- Plain-text docs, code comments, READMEs, or diff-friendly output → use **non-Unicode ASCII** (images may not render there)
- Confluence / wiki without D2 plugin → Mermaid only as last resort

## Install (one-time per machine)

```bash
# d2 (with TALA layout plugin too — we don't use TALA, but install once)
curl -fsSL https://d2lang.com/install.sh | sh -s -- --tala

# Roboto Mono fonts — the chosen font for monospace alignment in labels
mkdir -p ~/.local/share/fonts
for v in Regular Bold Italic; do
    curl -fsSL "https://cdn.jsdelivr.net/gh/googlefonts/RobotoMono@main/fonts/ttf/RobotoMono-${v}.ttf" \
        -o "$HOME/.local/share/fonts/RobotoMono-${v}.ttf"
done
fc-cache -f ~/.local/share/fonts/

# rsvg-convert — for materializing PNG from SVG (predictable markdown rendering)
sudo apt install -y librsvg2-bin
```

## Hard quality bar (apply to every diagram)

Four rules that override aesthetic preferences:

1. **Legible at phone width.** When the rendered PNG is fit to a 360px-wide phone column, the smallest body text must still be readable (≥10px effective).
2. **Contrast.** Always set an explicit `font-color` whenever you set `fill`. Light fills (`#e8f5e9`, `#fff9c4`) need a *dark* font color (`#1a1a1a`, `#0f172a`). Dark fills (`#1976d2`, `#0f172a`) need a *light* font color (`#ffffff`, `#f5f5f5`). D2 picks its own default that often fails — never trust it. Use the contrast table below.
3. **No text overlapping borders.** D2 sometimes packs labels right against the edge of a shape, especially when a shape contains multi-line markdown. The fix is **always** "shorten the label" — never "shrink the font." Default D2 (16pt) is too small; bumping fonts grows the layout proportionally. Compact labels are the only fix.
4. **Compact labels; details belong in the surrounding prose.** A diagram's job is to anchor *the model* (the boxes and the relationships), not to teach every term inside the boxes. Strip parentheticals, footnotes, and qualifiers from labels; recover the lost detail in the markdown body. The prose should reference each labeled box and edge by name so the reader connects diagram → text.

If the rendered PNG fails any of these, fix the source and re-render. Don't ship a diagram that's unreadable on a phone — that's a defect, not a style preference.

## On-screen text size: the math

Two font-related issues will bite you. Both have the same root cause and the same fix.

**Issue 1 — text overflows the box edge.** D2 measures text geometry at layout time using **Source Sans Pro** metrics (built into the d2 binary). It then emits SVG with `font-family: "Source Sans Pro"`. When `rsvg-convert` rasterizes that SVG, if Source Sans Pro is not installed, `fc-match` falls back to whatever's available — commonly **DejaVu Sans**, which has wider glyphs. Result: boxes were sized for the narrower font, text rendered with the wider font, text overflows the border.

Fix: pass D2 a font path that matches what rsvg will render with. Either install Source Sans Pro, or pass `--font-regular=`/`--font-bold=` pointing to a font that's actually on disk:

```bash
# Match against what rsvg-convert will fall back to (run `fc-match "Source Sans Pro"` to confirm)
DEJAVU=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf
DEJAVU_BOLD=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf
d2 --layout=elk --font-regular="$DEJAVU" --font-bold="$DEJAVU_BOLD" diagram.d2 diagram.svg
```

(The Roboto Mono recipe at the top of this file is the same idea — you install Roboto Mono, then point both D2's measurement and the SVG's `font-family` at it.)

**Issue 2 — text is too small to read on mobile, no matter what font-size you set in the source.** This is the trap I want you to remember:

> **on-screen text size = SVG_FONT × DISPLAY_WIDTH / SVG_NATURAL_WIDTH**

If you bump `font-size` in the source, D2 grows boxes proportionally, the SVG natural width grows by the same ratio, and the on-screen text size is **unchanged** when the browser fits the image to a fixed-width container. If you render the PNG at a wider absolute pixel width, the browser scales it back down. The PNG width drops out of the equation entirely.

The only knob that actually grows on-screen text at a fixed display width is **shrinking the SVG natural width** — which means **less stuff in the source** (shorter labels, fewer lines per box, fewer parentheticals).

Concrete numbers from a real architecture diagram:

| | Source detail | SVG natural | At 1500-px PNG | On phone (360 CSS) | On desktop (800 CSS) |
|--|--|--|--|--|--|
| Verbose | Long multi-line labels | 4569 px | text 11.8 px | **2.8 CSS px** (illegible) | **6.3 CSS px** (small) |
| Compact | Short single-line labels | 2323 px | text 23.2 px | **5.6 CSS px** (2× better) | **12.4 CSS px** (legible) |

The compact rewrite halved the SVG natural width by dropping parentheticals and group qualifiers. **Same PNG width, same display behavior — but text is 2× larger on screen.** The detail moved into the surrounding prose.

Rule of thumb: if the SVG natural width exceeds **2500 px**, the diagram has too much text in it. Shrink the labels.

## Vertical stacking is free; horizontal length is what costs you

The formula above only depends on SVG natural **width**. SVG natural height is independent — it does not affect on-screen text size at a fixed display width. The page just gets longer.

Practical consequence: **multi-line labels are fine, even encouraged** when they help. A 4-line label inside a single box grows that box vertically but its width is bounded by the **widest single line**. So you can pack useful detail into a box without bloating horizontal extent — provided each line stays short.

Don't write:

```
auth: "Auth service (issues and validates session tokens; refreshes the cache on miss)"
```

Do write:

```
auth: "Auth service\ntoken issue\n+ refresh"
```

Same information, narrower box, taller box. Width matters; height doesn't.

## Compactness scales with block count

The 2500-px width target tightens or loosens depending on how many blocks you have:

| Block count | Label discipline |
|--|--|
| **Few blocks** (≤ ~6 named, single column or 2 side-by-side) | You can afford richer labels — multi-line, sub-bullets, even small tables. There's nothing else to spread the canvas; one or two boxes claiming wider widths just pad them out. |
| **Many blocks** (≥ ~10 named, ≥ 3 side-by-side at any layer) | Compactness is mandatory. Multiple side-by-side boxes each at "comfortable" width sums to a 4000+ px canvas, and the on-screen text gets crushed. Strip every label to its minimum. |

In other words: the cost of a long label is proportional to how many other boxes are competing for horizontal space. A 4-block diagram with rich text reads fine. A 15-block diagram with the same per-box text becomes unreadable on phones.

Decision rule: count side-by-side boxes at the widest layer of the layout. If that count is ≥3, compact every label. If it's 1–2, you can spend your width budget on richer labels.

## D2 source preamble (use this template)

```d2
# Diagram title comment
# Render:
#   d2 --layout=elk --pad=40 \
#      --font-regular ~/.local/share/fonts/RobotoMono-Regular.ttf \
#      --font-bold    ~/.local/share/fonts/RobotoMono-Bold.ttf \
#      --font-italic  ~/.local/share/fonts/RobotoMono-Italic.ttf \
#      diagram.d2 diagram.svg
#
#   rsvg-convert -w 1600 diagram.svg > diagram.png

vars: {
  d2-config: {
    layout-engine: elk
  }
}

direction: down

# Every class sets BOTH fill AND font-color so contrast is explicit.
# Light fills get dark text; dark fills get light text. Never rely on D2 defaults.
classes: {
  # Light backgrounds — dark text (#1a1a1a or near-black)
  hand:   { style: { font-size: 36; fill: "#ffffff"; stroke: "#444";    font-color: "#1a1a1a" } }
  gen:    { style: { font-size: 36; fill: "#fff3bf"; stroke: "#a37e00"; font-color: "#1a1a1a" } }
  vendor: { style: { font-size: 36; fill: "#e8e8e8"; stroke: "#666";    font-color: "#1a1a1a" } }
  rust:   { style: { font-size: 36; fill: "#d6eaf8"; stroke: "#1f5f8b"; font-color: "#0f172a" } }
  group:  { style: { font-size: 48; fill: "#fafafa"; stroke: "#222";    font-color: "#0f172a"; bold: true } }
  light:  { style: { font-size: 36; fill: "#e8f5e9"; stroke: "#2e7d32"; font-color: "#1a1a1a" } }
  warn:   { style: { font-size: 36; fill: "#fff9c4"; stroke: "#f57c00"; font-color: "#1a1a1a" } }
  cool:   { style: { font-size: 36; fill: "#e3f2fd"; stroke: "#1976d2"; font-color: "#0f172a" } }
  pink:   { style: { font-size: 36; fill: "#fce4ec"; stroke: "#c2185b"; font-color: "#1a1a1a" } }
  orange: { style: { font-size: 36; fill: "#fff3e0"; stroke: "#ef6c00"; font-color: "#1a1a1a" } }

  # Dark backgrounds — light text (#ffffff or #f5f5f5)
  hw:     { style: { font-size: 40; fill: "#f1948a"; stroke: "#922b21"; font-color: "#1a1a1a"; bold: true } }
  navy:   { style: { font-size: 36; fill: "#0f172a"; stroke: "#1976d2"; font-color: "#ffffff" } }
  dark:   { style: { font-size: 36; fill: "#374151"; stroke: "#111827"; font-color: "#ffffff" } }
}

# Apply class to a shape:
#   foo.class: hand
#   foo: "Some hand-written code"
```

The colour palette has semantic meaning you can reuse across diagrams:

| Class    | Fill      | Font color  | Meaning                              |
|----------|-----------|-------------|--------------------------------------|
| `hand`   | `#ffffff` | `#1a1a1a`   | hand-written code                    |
| `gen`    | `#fff3bf` | `#1a1a1a`   | auto-generated build artifact        |
| `vendor` | `#e8e8e8` | `#1a1a1a`   | vendored / upstream code             |
| `rust`   | `#d6eaf8` | `#0f172a`   | Rust component                       |
| `hw`     | `#f1948a` | `#1a1a1a`   | hardware                             |
| `group`  | `#fafafa` | `#0f172a`   | container / layer / module boundary  |
| `light`  | `#e8f5e9` | `#1a1a1a`   | "good" / safe / OK                   |
| `warn`   | `#fff9c4` | `#1a1a1a`   | warning / caveat                     |
| `cool`   | `#e3f2fd` | `#0f172a`   | informational / neutral              |
| `pink`   | `#fce4ec` | `#1a1a1a`   | memory / data                        |
| `orange` | `#fff3e0` | `#1a1a1a`   | engine / functional unit             |
| `navy`   | `#0f172a` | `#ffffff`   | dark callout                         |
| `dark`   | `#374151` | `#ffffff`   | system block                         |

## Contrast quick-check table

If you must invent a fill color, pair it from this table:

| Fill lightness  | Use font-color |
|-----------------|----------------|
| Very light (`#fafafa`–`#fff9c4`) | `#1a1a1a` (near-black) |
| Light pastel (`#d6eaf8`–`#fce4ec`)| `#0f172a` (deep navy) |
| Medium (`#f1948a`, `#90caf9`)    | `#1a1a1a` if luminance > 0.5, else `#ffffff` |
| Dark (`#1976d2`, `#374151`)      | `#ffffff` (white) |
| Very dark (`#0f172a`, `#000`)    | `#f5f5f5` (off-white) |

**Never** ship a diagram with `font-color` unset on a colored shape. The default is "auto" but D2's auto-pick has known failures (light-grey-on-pastel happens routinely).

## Avoiding text overlapping borders

D2 sets shape size from text size, but multi-line markdown labels and long single-line labels frequently end up touching the box edge. Three remedies, in order of preference:

1. **Shorten the label.** "Application Programming Interface (API)" → "API". The legend table belongs in the markdown above, not in the diagram.
2. **Use multi-line with explicit width.** If you genuinely need 2-3 lines of text inside a shape:

   ```d2
   foo: |md
     ## Title
     - bullet 1
     - bullet 2
   | {
     style.font-size: 32
     width: 480
   }
   ```

   `width` forces D2 to give the shape enough horizontal room. Without it, ELK packs to the minimum and clips.

3. **Use `--pad=40` or higher when rendering.** This sets the per-shape padding D2 applies. Default is 20; bump to 40 for diagrams with dense labels.

If you see text touching a border in the rendered PNG, it's a *bug in the D2 source*, not a rendering quirk. Fix at the source.

## Render recipe

```bash
REG=~/.local/share/fonts/RobotoMono-Regular.ttf
BLD=~/.local/share/fonts/RobotoMono-Bold.ttf
ITL=~/.local/share/fonts/RobotoMono-Italic.ttf

# 1. Source-of-truth SVG
d2 --layout=elk --pad=30 \
   --font-regular "$REG" --font-bold "$BLD" --font-italic "$ITL" \
   diagram.d2 diagram.svg

# 2. Materialize a fixed-width PNG for predictable markdown rendering
rsvg-convert -w 1600 diagram.svg > diagram.png
```

## Embed in markdown

```markdown
![Description of the diagram](./diagram.png)

Source: [diagram.d2](./diagram.d2) · vector: [diagram.svg](./diagram.svg)
```

Always link the `.d2` source — readers (and you) will edit-and-rerender,
not paint pixels. Always link the `.svg` too — it's the zoom-friendly
view for someone who wants pixel-perfect detail.

## Why these specific font sizes

The 36pt body / 48pt title numbers above are calibrated against the formula in "On-screen text size: the math" earlier in this file. They assume:

- SVG natural canvas around **2300–2500 px wide** (achievable with disciplined compact labels)
- PNG rendered at 1500–1600 px wide and fit to a ~800 px content column
- Resulting on-screen body text around **12–15 CSS px**, which matches an ASCII reference at 14pt — the legibility bar

If your SVG natural width exceeds 2500 px, the answer is **not** "bump font-size further" — that just grows the SVG and the on-screen text stays the same. The answer is **shrink the labels** until the SVG fits under that width target.

Edge labels need explicit `style.font-size: 32-36; style.bold: true` per-edge, because D2's default edge label is smaller than body.

## Common pitfalls

### 1. Legend stealing the right column

Don't put a legend block inside the D2 graph. ELK will lay it out as a
parallel column to the main flow, halving the horizontal real-estate of
every other shape.

**Fix:** Put the colour key in the markdown text *above* the image. The
diagram itself uses class names; the markdown text decodes them.

### 2. Build/auxiliary panel placed at the top

If you have a "build pipeline" or "side panel" container with no
incoming runtime edge, ELK puts it in the same rank as the topmost
runtime shape (or above it). Result: layout chaos.

**Fix:** Either give the panel a fake incoming edge (`runtime_top -> panel:
"" { style.opacity: 0 }`), or split into two D2 files and embed both
images sequentially in markdown.

### 3. Tiny edge labels

Default edge label font is the same size as default body — but visually
they look smaller because they're not in a box.

**Fix:** Per-edge:
```d2
a -> b: "label text" {
  style.font-size: 36
  style.bold: true
}
```

### 4. Default font sizes are 16/28

Without explicit `style.font-size`, D2 uses 16pt body / 28pt title. Both
become illegible (< 5px effective) when GitHub fits a 4000px-wide SVG
to a ~1000px column.

**Fix:** Always set explicit `font-size` in `classes`. See template above.

### 5. Markdown column scales SVG unpredictably

`![](file.svg)` in GitHub markdown displays the SVG at its declared
width, capped to the column — but different markdown renderers behave
differently.

**Fix:** Render SVG → PNG at 1600px wide, embed the PNG. SVG stays as
the link below for "click to view full vector."

## Layout strategies

### Top-down (architecture / call-flow)

```d2
direction: down
```

Boxes stack vertically. Edges flow top→bottom. Best for layered systems
(client → API → cache → database).

### Left-to-right (process / state machine)

```d2
direction: right
```

Best for stateful flows where progression reads as time.

### Mixed (containers with their own direction)

```d2
direction: down

main_flow: {
  direction: down
  a -> b -> c
}

side_panel: {
  direction: right
  x -> y -> z
}
```

Useful when one part of the diagram is sequential and another is parallel.

## Examples

Consider a web-service architecture diagram as a full worked example — a
request flows Client → API → Cache → Database, with a Worker pool draining a
Queue off to the side:
- Source: `diagrams/web-service-architecture.d2`
- Render: `diagrams/web-service-architecture.{svg,png}`
- Embedded in: `web-service-architecture.md`

That diagram demonstrates:
- 4 nested containers (CLIENT / EDGE / SERVICES / DATA)
- Per-shape classing (hand / gen / vendor / rust / hw)
- Cross-container edges with labels
- Solid runtime edges + dashed future-direction edges
- ELK directed layout with `direction: down`
