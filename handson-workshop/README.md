# handson-workshop

A kit for authoring **self-contained, auto-graded hands-on workshops** for any technical topic.

Contains two skills:

- **skills/handson-workshop** — the workshop authoring workflow.
- **skills/handson-diagrams** — companion diagramming guidance (D2 / ASCII / Mermaid / Python).

See the [repository README](../README.md) for installation (Claude Code + Codex).

## What it produces

The skill supports **two output shapes**. For short/medium workshops it writes a single scrolling
page; for large or heavily-expanded ones it writes a multi-page "wiki" (one page per module).

**Single-page** (default) — for a topic slug like `http-caching`:

```
http-caching/
├── WORKSHOP.md       # modules: goal, setup, commands, real captured output, a diagram, a quiz
├── WORKSHOP.html     # styled, self-contained: sidebar ToC, collapsible answer keys, highlighted code
├── exam.html         # standalone, auto-graded: 15-20 questions, 1-100 score, 70 to pass
├── diagrams/         # D2 source + rendered PNG/SVG (also matplotlib plots for quantitative topics)
└── captures/         # real command output the workshop cites
```

**Multi-page "wiki"** — a landing page plus one page per module, each its own file, with a
persistent left sidebar (every page listed, the current one highlighted, its sections nested) and
prev/next navigation:

```
batchnorm-vanishing-gradients/
├── content/
│   ├── wiki.json     # manifest: title + ordered list of pages
│   ├── index.md      # landing / overview page
│   └── module-N.md   # one markdown file per module (quiz + answer key live IN each page)
├── index.html        # generated landing page
├── module-N.html     # generated per-module pages
├── exam.html         # linked from the sidebar
├── diagrams/
└── captures/
```

Every generated `.html` is inlined (CSS, JS, images), so the pages open straight from the
filesystem and can be published to any static host.

## Prerequisites

```bash
pip install markdown beautifulsoup4 pygments        # HTML generator
curl -fsSL https://d2lang.com/install.sh | sh -s -- # D2 (diagrams)
sudo apt install -y librsvg2-bin                     # rsvg-convert (SVG -> PNG)
```

A given workshop topic may need more (a compiler, container runtime, database, etc.) — the skill's
systems-exploration phase detects that and asks before installing anything.

## Authoring a workshop

```text
/handson-workshop <topic>
```

The skill runs an **interview** (audience level, depth, time budget, scope check, and — for large
topics — single-page vs multi-page wiki), then a **systems-exploration** pass (confirm the host can
reproduce the experiments, fill gaps with your approval), then researches, captures real output,
and generates the artifacts above.

To regenerate the HTML after editing the content:

```bash
# single-page
python3 skills/handson-workshop/assets/workshop-html-generator.py <slug>/WORKSHOP.md

# multi-page wiki
python3 skills/handson-workshop/assets/wiki-generator.py <slug>/content/wiki.json
```

## Assets

| File | Purpose |
|------|---------|
| `skills/handson-workshop/assets/workshop-template.md` | Starting point for `WORKSHOP.md`. |
| `skills/handson-workshop/assets/workshop-html-generator.py` | Renders `WORKSHOP.md` → self-contained `WORKSHOP.html` (single-page). |
| `skills/handson-workshop/assets/wiki-generator.py` | Renders `content/*.md` + `wiki.json` → a multi-page "wiki" (landing page + one page per module) with a persistent cross-page sidebar. Reuses the single-page generator's styling. |
| `skills/handson-workshop/assets/exam-template.html` | Starting point for the auto-graded `exam.html`. |
| `skills/handson-workshop/assets/serve-workshop.sh` | Serve a workshop dir over HTTP for local/LAN preview. |
| `skills/handson-workshop/assets/pico.classless.min.css` | Bundled Pico CSS (MIT) used by the generator. |
