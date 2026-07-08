# joels-skills

A collection of installable **skills** for [Claude Code](https://claude.com/claude-code) and
[Codex](https://developers.openai.com/codex/). Each skill is a plain `SKILL.md` (plus optional
`assets/`/`references/`), so the same files work in both tools.

## Table of Contents

- [What's inside](#whats-inside)
- [Prerequisites](#prerequisites)
- [Install — Claude Code](#install--claude-code)
- [Install — Codex](#install--codex)
- [Quickstart](#quickstart)
- [How a workshop is built](#how-a-workshop-is-built)
- [License](#license)

## What's inside

### `handson-workshop` (kit)

A kit that turns any technical topic into a **self-contained, auto-graded hands-on workshop**. It
bundles two skills:

| Skill | What it does |
|-------|--------------|
| **handson-workshop** | Interviews you to gauge audience level and depth, explores your machine to make the experiments reproducible (offering to install missing tools with your approval), and — if the topic is too big — suggests a smaller starter workshop plus a follow-on series. Then generates `WORKSHOP.md`, a styled self-contained `WORKSHOP.html` (sidebar ToC, collapsible answer keys, syntax highlighting), and a standalone `exam.html` with 15–20 auto-graded questions (1–100 score, 70 to pass). For large workshops it can instead emit a multi-page **wiki** — a landing page plus one page per module, with a persistent cross-page sidebar and prev/next navigation. |
| **handson-diagrams** | Companion diagramming guidance: **D2** (ELK layout) for architecture diagrams, non-Unicode **ASCII** for plain-text docs, **Mermaid** as a fallback, and **Python** charts (Bokeh / Matplotlib / Folium / Graphviz) for data. |

Workshops are grounded in **real captured command output**, not invented examples.

## Prerequisites

Install these on the machine where you *author* workshops (a given workshop topic may also need its
own extra tooling — the skill detects that and asks):

```bash
# HTML generator (Python 3)
pip install markdown beautifulsoup4 pygments

# Diagram rendering (D2 + SVG->PNG)
curl -fsSL https://d2lang.com/install.sh | sh -s --
sudo apt install -y librsvg2-bin        # provides rsvg-convert (or: brew install librsvg)
```

## Install — Claude Code

**Via the plugin marketplace (recommended):**

```text
/plugin marketplace add joelagnel/joels-skills
/plugin install handson-workshop
```

(Replace `joelagnel/joels-skills` with the GitHub `owner/repo` once published, or pass a local
path: `/plugin marketplace add ~/repo/joels-skills`.)

**Or symlink the skills manually:**

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
basename — so `handson-workshop` and `handson-diagrams`. The `SKILL.md` files use no
Claude-Code-only dynamic syntax, so they run unchanged in Codex. Restart Codex to pick up new skills.

> Codex also supports *plugins* for distributing reusable skills; a Codex-plugin wrapper for this
> kit is a possible future addition. For now the Codex side is a direct skill install.

## Quickstart

```text
/handson-workshop "git internals"
```

The skill will interview you, check your system, and (with your approval) fill any tool gaps before
producing `./git-internals/WORKSHOP.md`, `WORKSHOP.html`, and `exam.html`.

Preview the result — the HTML is fully self-contained, so just open it:

```bash
xdg-open git-internals/WORKSHOP.html          # or open it in any browser
# or serve it to other devices on your LAN (serve-workshop.sh ships in the skill's assets/,
# run from a checkout of this repo or use the installed skill's path):
bash handson-workshop/skills/handson-workshop/assets/serve-workshop.sh git-internals
```

## How a workshop is built

1. **Interview & scope** — gauge audience level (Beginner / Intermediate / Advanced), desired
   outcome, and time budget; split an over-broad topic into a starter workshop + series roadmap.
2. **Systems exploration** — probe the host for the compilers / containers / VMs / CLIs the topic
   needs; surface gaps and, with your approval, install what's missing so experiments are real.
3. **Research & capture** — run commands, save real output.
4. **Author** — write modules (goal, setup, commands, captured output, a diagram, a quiz), then
   generate the styled HTML and the auto-graded exam. Short/medium topics become one scrolling
   `WORKSHOP.html`; large ones become a multi-page wiki (`index.html` + one page per module) via
   `wiki-generator.py`.

## License

Apache-2.0 — see [LICENSE](LICENSE) and [NOTICE](NOTICE). Bundles [Pico CSS](https://picocss.com/) (MIT).
