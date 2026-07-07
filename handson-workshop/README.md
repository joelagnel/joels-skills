# handson-workshop

A kit for authoring **self-contained, auto-graded hands-on workshops** for any technical topic.

Contains two skills:

- **skills/handson-workshop** — the workshop authoring workflow.
- **skills/handson-diagrams** — companion diagramming guidance (D2 / ASCII / Mermaid / Python).

See the [repository README](../README.md) for installation (Claude Code + Codex).

## What it produces

For a topic slug like `http-caching`, the skill writes:

```
http-caching/
├── WORKSHOP.md       # modules: goal, setup, commands, real captured output, a diagram, a quiz
├── WORKSHOP.html     # styled, self-contained: sidebar ToC, collapsible answer keys, highlighted code
├── exam.html         # standalone, auto-graded: 15-20 questions, 1-100 score, 70 to pass
├── diagrams/         # D2 source + rendered PNG/SVG
└── captures/         # real command output the workshop cites
```

Everything in `WORKSHOP.html` / `exam.html` is inlined (CSS, JS, images), so they open straight from
the filesystem and can be published to any static host.

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

The skill runs an **interview** (audience level, depth, time budget, scope check), then a
**systems-exploration** pass (confirm the host can reproduce the experiments, fill gaps with your
approval), then researches, captures real output, and generates the three artifacts above.

To regenerate the HTML after editing `WORKSHOP.md`:

```bash
python3 skills/handson-workshop/assets/workshop-html-generator.py <slug>/WORKSHOP.md
```

## Assets

| File | Purpose |
|------|---------|
| `skills/handson-workshop/assets/workshop-template.md` | Starting point for `WORKSHOP.md`. |
| `skills/handson-workshop/assets/workshop-html-generator.py` | Renders `WORKSHOP.md` → self-contained `WORKSHOP.html`. |
| `skills/handson-workshop/assets/exam-template.html` | Starting point for the auto-graded `exam.html`. |
| `skills/handson-workshop/assets/serve-workshop.sh` | Serve a workshop dir over HTTP for local/LAN preview. |
| `skills/handson-workshop/assets/pico.classless.min.css` | Bundled Pico CSS (MIT) used by the generator. |
