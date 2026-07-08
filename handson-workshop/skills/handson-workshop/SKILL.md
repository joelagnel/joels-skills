---
name: handson-workshop
description: Create a comprehensive, self-contained hands-on workshop for any technical topic. Use when the user invokes /handson-workshop <topic> (e.g., /handson-workshop "git internals", /handson-workshop "HTTP caching", /handson-workshop sqlite). First interviews the user to gauge audience knowledge-level and desired depth, then explores the local system to confirm the tooling needed to reproduce the experiments (offering to install missing prerequisites with the user's approval), and may suggest narrowing an over-broad topic into a smaller starter workshop plus a follow-on series. Then it produces (1) WORKSHOP.md with modules — each containing a diagram, hands-on commands with real captured output, and a quiz that links to an answer key — (2) WORKSHOP.html, a styled, self-contained HTML version with sidebar ToC, collapsible answer keys, and syntax-highlighted code, and (3) a standalone exam.html with 15-20 auto-graded questions (1-100 score, 70 to pass). Workshops are grounded in concrete output, not invented examples.
---

# Hands-On Workshop Creator

Creates a hands-on workshop from a topic. Output: a markdown workshop with quizzes, a styled
self-contained HTML version, and a standalone auto-graded HTML exam.

The workshop is only as good as its grounding: every command shows **real, captured output**,
not invented examples. That is why the workflow front-loads an interview (to size depth to the
audience) and a systems-exploration pass (to make sure the authoring host can actually run the
experiments) before any drafting happens.

## Output location

By default, write the workshop into a directory named after the topic slug, created under the
current working directory:

```
./<slug>/
├── WORKSHOP.md       # main workshop (links to WORKSHOP.html and exam.html)
├── WORKSHOP.html     # styled, self-contained HTML version
├── exam.html         # standalone, auto-graded final exam
├── diagrams/         # diagram source + rendered PNG/SVG (if pre-rendering)
└── captures/         # logs, command output, transcripts (real experiment output)
```

`<slug>` is hyphen-case derived from the topic (e.g., "HTTP caching" → `http-caching`). If the
user names a different output root, honor it; otherwise use `./<slug>/` and `mkdir -p` it.

## Workflow

The workflow has two front-loaded phases (**Phase 0 — Interview & scope**, **Phase 1 — Systems
exploration**) followed by the authoring steps. Do the phases in order; do not start drafting
until both are done.

### Phase 0 — Interview & scope

Before researching anything, interview the user to shape the workshop. In Claude Code use
`AskUserQuestion` for the multiple-choice parts; in other tools ask conversationally. Skip any
question whose answer is already obvious from the topic or the request.

**Gauge the audience and desired depth** (this is what makes the workshop tailored rather than
one-size-fits-all). Ask a short batch (≈3–5) covering:

- **Knowledge level** for this topic: *Beginner* (new to it), *Intermediate* (has used it, wants
  depth), or *Advanced* (wants internals / edge cases).
- **Familiarity with the prerequisites** — so Module 0 (vocabulary/setup) can be sized right.
- **Desired outcome** — what should the reader be able to *do* when finished?
- **Time budget / target length** — maps to module count (short ≈ 3–4 modules, half-day ≈ 6–8).
- **Style**: exercise-driven (tool/command focus) vs tutorial-driven (concept tour).

**Depth rubric — map answers to workshop shape:**

| Level | Module 0 | Pace & depth | Quizzes / exam |
|-------|----------|--------------|----------------|
| Beginner | Required, generous | Explain prerequisites, gentle pace, fewer/simpler modules | Recall + comprehension |
| Intermediate | Optional | Assume basics, standard depth, moderate module count | Application-oriented |
| Advanced | Skip unless jargon-heavy | Internals, edge cases, harder experiments | Application + analysis |

**Scope check — suggest starting smaller when the topic is too big.** Before committing, estimate
the concept load: roughly how many modules the topic needs and whether it spans multiple large
subsystems. If it clearly exceeds one sitting (guidance: **> ~6–8 modules, or plainly
multi-domain**), stop and **propose narrowing**:

- Recommend a smaller, foundational **"Workshop 1"** to build now, and
- Sketch a **follow-on series roadmap** (Workshop 2, 3, …) for the rest.

Let the user accept the narrowed scope, pick a different starting slice, or explicitly override
and proceed full-size. Producing one bloated workshop is a failure mode — a focused starter plus a
roadmap is almost always the better outcome.

### Phase 1 — Systems exploration & prerequisites

Because the workshop is grounded in **real captured output**, the machine you author on must be
able to reproduce the experiments. Confirm that before drafting; fill gaps only with the user's
consent.

1. **Probe the environment (read-only).** Inventory what's installed that's relevant to the chosen
   topic and depth. Use non-destructive checks (`command -v <tool>`, `<tool> --version`, `uname
   -a`, `cat /etc/os-release`). Typical categories a workshop *might* need — a given topic may need
   all, some, or none:
   - Language toolchains / compilers: `gcc`, `clang`, `rustc`, `go`, `python3`, `node`
   - Build tools: `make`, `cmake`, `ninja`
   - Containers: `docker`, `podman`
   - Virtualization / emulation: `qemu`, `kvm`/`libvirt`, `vagrant`, and similar VM tooling
   - Package managers and language runtimes
   - Topic-specific CLIs, services, databases, or hardware/devices

2. **Map needs → capabilities → gaps.** From the modules you intend to write, derive the set of
   tools required to reproduce them, diff against what's present, and produce a short **gap list**.

3. **Ask, then provision (only with approval).** If prerequisites are missing, ask the user how to
   proceed **per gap**:
   - **Install it now** — with explicit approval, install via the system's package manager or the
     tool's official installer, then **re-verify** it works. Never install silently.
   - **Substitute** a lighter approach (e.g., a container instead of a full VM).
   - **Skip** that module's hands-on and make it conceptual (note this in Prerequisites).
   - **Re-scope** the topic to what the host can actually run (loops back to the Phase 0 scope
     check).

4. **Gate drafting on reproducibility.** Only once the environment can run the intended experiments
   — or the scope has been adjusted to fit — proceed to research, capture, and generation.

### 2. Research before drafting

Workshops are weak when grounded in invented examples. Strong workshops use **real captures**.

- Read source code and documentation for the topic.
- Run commands and save raw output (logs, tool output, transcripts) to `captures/`.
- If experiments need a specific environment (a VM, a container, a running service, a notebook),
  set it up (per Phase 1) and **cite the capture file + line numbers** in the workshop.
- Use `WebFetch`/`WebSearch` (or your tool's web-search equivalent) only for high-level context,
  not for fabricated command output.

### 3. Draft WORKSHOP.md

Copy `assets/workshop-template.md` to `WORKSHOP.md` and fill it in. Module structure:

```
## Module N: <Name>

**Goal.** One sentence.
**Setup.** What state the system should be in.
**Commands.** Exact lines to copy.
**Expected output.** Verbatim — cite source: (Captured in `captures/foo.log` line NN.)

(Diagram if it explains the model better than prose.)

**Question.** Discovery prompt; 2-4 sub-questions if useful.

→ [Answer Key — Module N](#answer-key--module-n)
```

Let the Phase 0 depth rubric drive the module count. Place all answer keys in a single section at
the end.

**Introduce jargon before using it.** For jargon-heavy topics (systems internals, networking,
databases, distributed systems), the first module after Prerequisites should be a **Module 0 —
Vocabulary primer** that defines every load-bearing term in plain English in two or three sentences
each. The reader should recognize every term in Modules 1+ before they get there. Don't drop a
reader into "the WAL is fsync'd before the commit returns" without first having said what a WAL is.

A second rule: **on first use within any module, define the term inline** even if it was defined in
Module 0. Re-stating "the write-ahead log (WAL)" is cheap; making the reader scroll back is not.
Treat each module as if a reader could land on it directly from a search.

Three signals that you owe the reader a Module 0:

1. The topic has more than ~10 acronyms/jargon terms used in the workshop body.
2. Any single sentence in your draft uses three or more acronyms back-to-back.
3. The audience level from Phase 0 is Beginner (or "first-time", "newcomers").

If any of those is true, write Module 0. If none are (e.g., the audience is the team that built the
system), Module 0 is optional.

**Explain the load-bearing objects, not just name them.** Naming a term (in Module 0 or inline) is
not the same as explaining how it *works*. If your argument's logic depends on how something
*behaves* — an activation's derivative, a loss's gradient, a normalizer's effect, a data structure's
invariant, a protocol's timing — then that behavior must be on the page **where it is first used**,
even for advanced audiences and even if the object is "basic." Litmus test: for every function,
operator, or component your explanation reasons about, ask *"does the reader need a specific property
of this to follow my point?"* If yes, show that property (measured, like everything else, where you
can). The classic failure is stating a conclusion — e.g. "gradients vanish because the sigmoid's
slope is ≤ 0.25" — while never showing what the sigmoid is or why its slope is ≤ 0.25, leaving the
reader to take the mechanism on faith. The audience level changes how *much* background to give,
never *whether* the load-bearing property itself appears.

### 4. Add diagrams

Use the companion **handson-diagrams** skill (installed alongside this one) for diagram guidance.
Preference: **D2 with ELK layout**, with `--font-regular` /
`--font-bold` always passed so D2's measurement font matches what `rsvg-convert` will rasterize
against. Without those flags D2 measures using one font and rsvg falls back to another (whatever
`fc-match` returns), and text overflows the box edges. Render recipe:

```bash
# Pick fonts that are actually on this system. Run `fc-match "Source Sans Pro"`
# to find what the rsvg fallback will be, then pass that to D2.
DEJAVU=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf
DEJAVU_BOLD=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf

d2 --layout=elk \
   --font-regular="$DEJAVU" --font-bold="$DEJAVU_BOLD" \
   diagrams/foo.d2 diagrams/foo.svg
rsvg-convert -w 1500 diagrams/foo.svg -o diagrams/foo.png
```

```markdown
![Architecture](diagrams/foo.png)
```

**Use the D2 preamble + classes from `handson-diagrams/references/d2-diagrams.md`** — do NOT
improvise per-shape `style.fill` / `style.stroke`. That file also explains the **on-screen-text
formula** that determines whether your diagram is readable on mobile, and the empirical rule: **SVG
natural width must stay under ~2500 px**, which means concise labels.

**Compact labels — details in the prose, not on the diagram.** A diagram's job is to anchor the
*model*: which boxes exist, how they connect, what the flow is. Educational detail (what a term
means, why two things relate) belongs in the surrounding markdown text.

How aggressive to be depends on **how many blocks the diagram has**:

- **Few blocks** (≤ ~6 named, 1–2 side-by-side at the widest layer) — labels can be multi-line and
  carry useful hints. Vertical stacking is free; the width budget isn't crowded. e.g.
  `"Auth service\ntoken issue\n+ refresh"` is fine here.
- **Many blocks** (≥ ~10 named, ≥3 side-by-side at any layer) — strip everything. e.g.
  `"Auth service"` only; the rest goes to prose.

The rule comes from the formula in `handson-diagrams/references/d2-diagrams.md` ("On-screen text
size: the math"): SVG natural width — the only thing that controls on-screen text size at a fixed
display width — is bounded by the widest single label times the number of side-by-side boxes at any
layer. Few side-by-side boxes means each one can be wider; many means each must be narrow.

What never changes:
- **Each individual line stays short.** Multi-line labels are fine, but each line is constrained —
  width is set by the widest line, not the total text.
- **Use short edge labels.** "requests (when target = cache)" → "to cache" (always; edges sit
  between boxes and inflate the canvas if labelled long).

**Pair the diagram with prose that covers the lost detail.** This is non-negotiable: every concept
that was on the verbose-version diagram must be in the prose. The prose should:

- Refer to diagram boxes and edges by their **visible label** ("the request handler in the API
  box", "the `cache read` edge", "step 4 in the diagram", "the `enqueue` edge between the API and
  the workers"). This is what makes the prose a guided tour rather than parallel content.
- Explain *what each named box does*, not just name it. The diagram says "Auth service"; the prose
  says "Auth service — the component that issues and validates session tokens. When a request
  arrives without a valid session, Auth is what mints a new token and refreshes the cache entry."
- Mention any annotation that's compressed on the diagram (`(1 per shard)`, `(paired 1:1 w/
  worker)`, `(xN, separate pods)`). These hint at a fact; the prose has to spell it out.

After rendering, **open each PNG in an image viewer at phone-column width (~360px) and verify**: can
you read every label? Is text inside the box (not touching the border)? Is the SVG natural width
under 2500 px? If any answer is "no", fix the source and re-render — don't ship.

Diagrams should **explain the model**, not decorate. If a paragraph already conveys the idea, skip
the diagram.

### 5. Generate WORKSHOP.html

After WORKSHOP.md is complete, generate the styled HTML version by running the generator that ships
in this skill's `assets/` directory:

```bash
# Adjust the path to wherever this skill is installed, e.g.
#   ~/.claude/skills/handson-workshop/assets/  (Claude Code)
#   ~/.codex/skills/handson-workshop/assets/   (Codex)
python3 <skill-dir>/assets/workshop-html-generator.py WORKSHOP.md
```

Requires Python 3 with `markdown`, `beautifulsoup4`, and `pygments`
(`pip install markdown beautifulsoup4 pygments`). It produces a self-contained `WORKSHOP.html`
beside the markdown file with:

- **Sticky sidebar** ToC with JS scroll-position highlighting (h2 + h3 headings)
- **Quiz sections** rendered as blue callout boxes
- **Answer key sections** wrapped in collapsible `<details>` (click to reveal)
- **Syntax-highlighted code** via Pygments github-dark theme
- **Diagram PNGs/SVGs** embedded as base64 (fully self-contained, no external deps)
- **Responsive** — sidebar collapses to a hamburger menu on narrow viewports

Re-run this command any time WORKSHOP.md changes. The generator is idempotent.

### 6. Build exam.html

Copy `assets/exam-template.html` to `exam.html`. The template is self-contained (HTML + CSS + JS,
no external deps) with auto-grading:

- 15-20 questions, distributed across modules (roughly proportional).
- Mix multiple choice (radio) and short answer (text input).
- Each `.question` div carries `data-id`, `data-answer` (lowercase, trimmed for matching),
  `data-explain` (shown after grading).
- Passing threshold: **70/100** (built into the JS).
- Replace the `{{TOPIC}}` placeholder in the title.

Weight the exam per the Phase 0 depth rubric (recall for Beginner; application/analysis for
Advanced).

### 7. Cross-link

- WORKSHOP.md → exam.html: link near the top *and* in a final "Final Exam" section.
- Bidirectional quiz ↔ answer key links — both anchors must be explicit:
  - Quiz heading: `### Quiz N {#quiz-n}` + trailing `→ [Answer Key — Module N](#answer-key--module-n)`
  - Answer-key heading: `### Answer Key — Module N {#answer-key--module-n}` + trailing `↑ [Back to Quiz N](#quiz-n)`
- Answer-key explanations should reference the module section that taught the concept.
- If experiments need a specific environment, add a `## Reproducing this workshop` section with the
  exact setup / version / build steps used to capture the output.

### 8. View / share your workshop

The generated `WORKSHOP.html` and `exam.html` are fully self-contained (all CSS, JS, and images
inlined), so there is nothing to deploy — they work straight from the filesystem:

- **Open directly** in a browser (`file://…/WORKSHOP.html`), or
- **Serve locally** to test on other devices on your network with the bundled helper:

  ```bash
  bash <skill-dir>/assets/serve-workshop.sh <slug>    # serves ./<slug>/ on http://localhost:8000
  ```

- **Publish** anywhere that hosts static files (GitHub Pages, Netlify, S3, any web server) — just
  copy the `<slug>/` directory across.

If you keep your workshops in a git repo, commit the `<slug>/` directory like any other artifact.

## Quality bar

| Component | Good | Bad |
|-----------|------|-----|
| Scope | Focused; over-broad topics split into a starter + roadmap | One bloated workshop covering everything |
| Depth | Matched to the audience level from the interview | One-size-fits-all regardless of audience |
| Prerequisites | Confirmed installed (or gaps surfaced) before drafting | Commands the author can't actually run |
| Commands | Real captured output, cited to a file | Invented / handwave output |
| Diagrams | Explain the mental model | Decorate; restate the prose |
| Quizzes | Test reasoning | Test trivia / surface recall |
| Exam | Cover every module | Lopsided to one topic |
| Reproducibility | Exact environment + version + steps | "Should work on most systems" |
| Shareable | Self-contained HTML opens anywhere; exam returns a 70+ pass | Broken links / missing assets |

## Reference archetypes

Two shapes work well; pick per the Phase 0 style answer:

- **Tool-focused / exercise-driven** — a series of numbered exercises around a single tool or
  command, each with setup, exact commands, captured output, and a question. One answer-key section
  at the end. Best when the goal is fluency with a specific tool.
- **Concept tutorial / tour-driven** — a guided tour through a subsystem's design, module by
  module, with diagrams anchoring the model and commands proving each claim. Best when the goal is
  understanding how something works.

## Anti-patterns

- **Don't skip the interview.** Depth and scope are the two biggest levers on workshop quality;
  guessing them wastes the reader's time.
- **Don't fabricate command output.** If you can't run it, say "the output should resemble:" and
  label it explicitly. Prefer capturing real output even from a small probe.
- **Don't install tooling silently.** Surface the gap, propose the fix, and install only after the
  user approves.
- **Don't write quizzes that pattern-match the prose.** A reader who skimmed should get them wrong;
  a reader who *understood* should get them right.
- **Don't create a workshop without a reproducibility section** when experiments depend on specific
  software versions, hardware, or setup — future readers will not remember.
- **Don't use emoji** in WORKSHOP.md or exam.html.
