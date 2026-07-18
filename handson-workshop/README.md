# HOW — the hands-on workshop kit

A kit for authoring **self-contained, auto-graded hands-on workshops** for any technical topic,
grounded in **real captured command output**, not invented examples.

Contains two skills:

| Skill | What it does |
|-------|--------------|
| **skills/handson-workshop** | Interviews you to gauge audience level and depth (including a short technical multiple-choice diagnostic with an honest "I don't know" option), explores your machine to make the experiments reproducible (offering to install missing tools with your approval), and — if the topic is too big — suggests a smaller starter workshop plus a follow-on series. Then generates the workshop Markdown, styled self-contained HTML with five selectable color themes, and a standalone auto-graded exam. |
| **skills/handson-diagrams** | Companion diagramming guidance: **D2** (ELK layout) for architecture and sequence diagrams, non-Unicode **ASCII** for plain-text docs, **Mermaid** as a fallback, and **Python** charts (Matplotlib / Bokeh / Folium / Graphviz) for data. |

## Table of Contents

- [What it produces](#what-it-produces)
- [Prerequisites](#prerequisites)
- [Install — Claude Code](#install--claude-code)
- [Install — Codex](#install--codex)
- [Install — ChatGPT](#install--chatgpt)
- [Quickstart](#quickstart)
- [How a workshop is built](#how-a-workshop-is-built)
- [Regenerating the HTML](#regenerating-the-html)
- [Assets](#assets)
- [License](#license)

## What it produces

The skill supports **two output shapes**. For short/medium workshops it writes a single scrolling
page; for large or heavily-expanded ones it writes a multi-page "wiki" (one page per module).

**Single-page** (default) — each workshop lives in its own directory, created where you invoked
the skill and named after the topic (the workshop on "HTTP caching" becomes `http-caching/`):

```
http-caching/
├── WORKSHOP.md       # modules: goal, setup, commands, real captured output, a diagram, a quiz
├── WORKSHOP.html     # styled, self-contained: sidebar ToC, theme picker, collapsible answer keys
├── exam.html         # standalone, auto-graded: 15-20 questions, 1-100 score, 70 to pass
├── diagrams/         # D2 source + rendered PNG/SVG (also matplotlib plots for quantitative topics)
├── captures/         # real command output the workshop cites
└── snippets/         # standalone runnable illustration snippets (technical topics)
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
filesystem and can be published to any static host. Pages carry **five selectable color themes**
(aurora vivid-dark default, midnight, synthwave, paper, sepia) with a swatch picker in the
sidebar; the exam follows the reader's saved choice and grades numeric answers by value
(0.25 = .25 = 1/4).

## Prerequisites

Install these on the machine where you *author* workshops:

```bash
pip install markdown beautifulsoup4 pygments        # HTML generator
curl -fsSL https://d2lang.com/install.sh | sh -s -- # D2 (diagrams)
sudo apt install -y librsvg2-bin                    # rsvg-convert (SVG -> PNG)
```

A given workshop topic may need more (a compiler, container runtime, database, etc.) — the skill's
systems-exploration phase detects that and asks before installing anything.

## Install — Claude Code

**Via the plugin marketplace (recommended):**

```text
/plugin marketplace add joelagnel/joels-skills
/plugin install handson-workshop
```

**Or symlink the skills manually** (from a checkout of this repo, at the repo root):

```bash
ln -s "$PWD/handson-workshop/skills/handson-workshop" ~/.claude/skills/handson-workshop
ln -s "$PWD/handson-workshop/skills/handson-diagrams" ~/.claude/skills/handson-diagrams
```

Invoke with `/handson-workshop <topic>`.

## Install — Codex

`skill-installer` is a **Codex skill** — you run it from *inside* Codex as `$skill-installer`, not
as a shell command. Ask it to install the two skills from this repo:

```text
$skill-installer install handson-workshop and handson-diagrams from github joelagnel/joels-skills
```

Under the hood, `skill-installer` runs its own bundled `install-skill-from-github.py` (that helper
ships with the Codex skill — you don't invoke it from this repo). The equivalent call passes both
skill paths to a single `--path`:

```bash
install-skill-from-github.py --repo joelagnel/joels-skills \
  --path handson-workshop/skills/handson-workshop handson-workshop/skills/handson-diagrams
```

Each skill installs into `$CODEX_HOME/skills/` (default `~/.codex/skills/`), named from the path
basename — so `handson-workshop` and `handson-diagrams`. Restart Codex to pick up new skills.

Invoke with `$handson-workshop <topic>` — Codex invokes skills as `$name`, not the `/name`
slash-command form Claude Code uses.

## Install — ChatGPT

Both skills are packaged as zips following the
[Agent Skills open standard](https://agentskills.io/specification), ready for
[ChatGPT's skills page](https://chatgpt.com/skills):

1. Download `handson-workshop-<version>.zip` and `handson-diagrams-<version>.zip` from the
   [latest release](https://github.com/joelagnel/joels-skills/releases/latest).
2. On [chatgpt.com/skills](https://chatgpt.com/skills), upload each zip to install the skill.

Each zip contains the skill folder at its root (`SKILL.md`, resources, `LICENSE.txt`, and
`agents/openai.yaml` UI metadata). To rebuild the packages from a checkout (repo root):

```bash
python3 tools/package_chatgpt_skills.py <version>    # writes dist/<skill>-<version>.zip
```

## Quickstart

```text
/handson-workshop "git internals"      # Claude Code
$handson-workshop "git internals"      # Codex
```

The skill will interview you, check your system, and (with your approval) fill any tool gaps
before producing `./git-internals/WORKSHOP.md`, `WORKSHOP.html`, and `exam.html`.

Preview the result — the HTML is fully self-contained, so just open it:

```bash
xdg-open git-internals/WORKSHOP.html          # or open it in any browser
# or serve it to other devices on your LAN:
bash handson-workshop/skills/handson-workshop/assets/serve-workshop.sh git-internals
```

## How a workshop is built

1. **Interview & scope** — gauge audience level (self-report plus a short technical
   multiple-choice diagnostic with an "I don't know" option), desired outcome, and time budget;
   split an over-broad topic into a starter workshop + series roadmap.
2. **Systems exploration** — probe the host for the compilers / containers / VMs / CLIs the topic
   needs; surface gaps and, with your approval, install what's missing so experiments are real.
3. **Research & capture** — run commands, save real output.
4. **Author** — write modules (goal, setup, commands, captured output, best-fit diagrams, sample
   code, a quiz), then generate the themed HTML and the auto-graded exam. Short/medium topics
   become one scrolling `WORKSHOP.html`; large ones become a multi-page wiki (`index.html` + one
   page per module) via `wiki-generator.py`. Every page reads complete on its own — the
   experiment script and log are optional cross-checks.

## Regenerating the HTML

The Markdown files are the **source**; the `.html` files beside them are **generated output**.
To edit a workshop, edit its Markdown (`WORKSHOP.md`, or `content/*.md` in the wiki shape) and
re-run the generator. The generator only rewrites the `.html` files — your Markdown is never
touched — and it is idempotent, so re-run it as often as you like.

Using `git-internals/` as the example workshop directory (see
[What it produces](#what-it-produces)), and with the generator paths relative to this kit
directory (use the installed skill's `assets/` path if you are not in a repo checkout):

```bash
# single-page: rewrites git-internals/WORKSHOP.html beside the .md
python3 skills/handson-workshop/assets/workshop-html-generator.py git-internals/WORKSHOP.md

# multi-page wiki: rewrites index.html and module-*.html at the workshop root
python3 skills/handson-workshop/assets/wiki-generator.py git-internals/content/wiki.json
```

## Assets

| File | Purpose |
|------|---------|
| `skills/handson-workshop/assets/workshop-template.md` | Starting point for `WORKSHOP.md`. |
| `skills/handson-workshop/assets/workshop-html-generator.py` | Renders `WORKSHOP.md` → self-contained `WORKSHOP.html` (single-page). Owns the theme system and attribution footer. |
| `skills/handson-workshop/assets/wiki-generator.py` | Renders `content/*.md` + `wiki.json` → a multi-page "wiki" (landing page + one page per module) with a persistent cross-page sidebar. Reuses the single-page generator's styling. |
| `skills/handson-workshop/assets/exam-template.html` | Starting point for the auto-graded `exam.html` (themed; value-based numeric grading). |
| `skills/handson-workshop/assets/serve-workshop.sh` | Serve a workshop dir over HTTP for local/LAN preview. |
| `skills/handson-workshop/assets/pico.classless.min.css` | Bundled Pico CSS (MIT) used by the generator. |

## License

Apache-2.0 — see the repository's [LICENSE](../LICENSE) and [NOTICE](../NOTICE).
