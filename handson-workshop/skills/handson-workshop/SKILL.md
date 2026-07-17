---
name: handson-workshop
description: Create a comprehensive, self-contained hands-on workshop for any technical topic. Use when the user invokes /handson-workshop <topic> (e.g., /handson-workshop "git internals", /handson-workshop "HTTP caching", /handson-workshop sqlite). First interviews the user to gauge audience knowledge-level and desired depth, including a short batch of technical multiple-choice questions that calibrates depth beyond self-report, then explores the local system to confirm the tooling needed to reproduce the experiments (offering to install missing prerequisites with the user's approval), and may suggest narrowing an over-broad topic into a smaller starter workshop plus a follow-on series. Then it produces (1) WORKSHOP.md with modules — each containing a best-fit diagram (block, sequence, flowchart, state machine, venn, or a bar/histogram/box chart), sample code for technical topics, hands-on commands with real captured output, and a quiz that links to an answer key — (2) WORKSHOP.html, a styled, self-contained HTML version with sidebar ToC, collapsible answer keys, and syntax-highlighted code, and (3) a standalone exam.html with 15-20 auto-graded questions (1-100 score, 70 to pass). Workshops are grounded in concrete output, not invented examples. For large or multi-module workshops it can instead emit a multi-page "wiki" (a landing page plus one page per module, with a persistent cross-page sidebar and prev/next navigation) via a separate generator.
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
current working directory. `<slug>` is hyphen-case derived from the topic (e.g., "HTTP caching" →
`http-caching`). If the user names a different output root, honor it; otherwise use `./<slug>/`
and `mkdir -p` it.

There are **two output shapes** — pick per the interview (see the *single-page vs multi-page*
question in Phase 0):

**Single-page** (default for short/medium workshops) — one long scrolling page with an in-page
table-of-contents sidebar:

```
./<slug>/
├── WORKSHOP.md       # main workshop (links to WORKSHOP.html and exam.html)
├── WORKSHOP.html     # styled, self-contained HTML version (built by workshop-html-generator.py)
├── exam.html         # standalone, auto-graded final exam
├── diagrams/         # diagram source + rendered PNG/SVG (if pre-rendering)
├── captures/         # logs, command output, transcripts (real experiment output)
└── snippets/         # standalone runnable illustration snippets (technical topics; see step 3)
```

**Multi-page "wiki"** (for large / deep / heavily-expanded workshops, or when the user asks for it)
— a landing page plus one page per module, each its own file, with a persistent left sidebar
listing every page (current one highlighted, its sections nested) and prev/next links. Prefer this
when a workshop has grown past what one scroll comfortably holds, or when each module wants room to
expand independently:

```
./<slug>/
├── content/
│   ├── wiki.json     # manifest: title + ordered list of pages (see step 5b)
│   ├── index.md      # landing / overview page
│   ├── module-0.md   # one markdown file per module (quiz + answer key live IN each page)
│   └── module-N.md
├── index.html        # generated landing page  (built by wiki-generator.py)
├── module-0.html     # generated per-module pages
├── module-N.html
├── exam.html         # standalone, auto-graded final exam (linked from the sidebar)
├── diagrams/         # referenced from content/ as ../diagrams/foo.png
├── captures/
└── snippets/         # standalone runnable illustration snippets (technical topics; see step 3)
```

In the multi-page shape there is **no `WORKSHOP.md`**; the landing page (`index.html`) is the entry
point and acts as the roadmap/table-of-contents. Each module page carries its own quiz and
collapsible answer key.

## Workflow

The workflow has two front-loaded phases (**Phase 0 — Interview & scope**, **Phase 1 — Systems
exploration**) followed by the authoring steps. Do the phases in order; do not start drafting
until both are done.

### Phase 0 — Interview & scope

Before researching anything, interview the user to shape the workshop. In Claude Code use
`AskUserQuestion` for the multiple-choice parts. In Codex use the `request_user_input` tool,
which has the same shape: a batch of questions, each with a short header (12 chars or fewer),
2-3 option labels with one-line descriptions, and a free-form "Other" choice that the client
adds automatically. Codex caps each call at 3 questions (and prefers 1), so run the interview
as two or three consecutive calls rather than one big batch. In tools with neither, ask the
questions conversationally. Skip any question whose answer is already obvious from the topic
or the request.

**Gauge the audience and desired depth** (this is what makes the workshop tailored rather than
one-size-fits-all). Ask a short batch (≈3–5) covering:

- **Knowledge level** for this topic: *Beginner* (new to it), *Intermediate* (has used it, wants
  depth), or *Advanced* (wants internals / edge cases).
- **Familiarity with the prerequisites** — so Module 0 (vocabulary/setup) can be sized right.
- **Desired outcome** — what should the reader be able to *do* when finished?
- **Time budget / target length** — maps to module count (short ≈ 3–4 modules, half-day ≈ 6–8).
- **Style**: exercise-driven (tool/command focus) vs tutorial-driven (concept tour).
- **Output shape** (only worth asking when the topic is large or the user wants depth):
  *single-page* (one scroll, default) vs *multi-page wiki* (a landing page + one page per module
  with a persistent cross-page sidebar). Recommend the wiki when you expect more than ~5–6
  substantial modules or a lot of per-module detail; otherwise single-page.

**Calibrate with technical multiple-choice questions — don't trust self-report alone.**
Self-assessed level is noisy: "intermediate" means something different to everyone, and readers
routinely under- or over-sell themselves. After the self-report batch, run a short **diagnostic
batch** of 3–5 topic-specific technical multiple-choice questions that climb the difficulty
ladder:

- one **vocabulary** question — can they pick the correct definition of the topic's most
  load-bearing term?
- one or two **working-knowledge** questions — "what happens when …?", "which of these does X?"
- one or two **internals / edge-case** questions — the kind only someone who has debugged the
  thing answers correctly.

Write them like good quiz questions: one clearly correct answer, and distractors that are each
a *real, common misconception* rather than filler, so a wrong answer carries information. Frame
the batch as tuning, not testing: "A few quick technical questions so the workshop lands at the
right depth — guessing is fine." Use the same question tool as the self-report batch.

Combine the diagnostic with the self-report, and let **demonstrated performance win** when the
two disagree:

| Diagnostic outcome | Treat as |
|--------------------|----------|
| Misses the vocabulary question | Beginner (whatever was self-reported); Module 0 required |
| Vocabulary + working knowledge right, internals missed | Intermediate; each missed internals question becomes an explicit target for the module that covers it |
| Everything right, including internals | Advanced; skip Module 0, push the experiments deeper |

The specific wrong answers are worth more than the score: every distractor the user picked
names a live misconception. Note which were chosen and wire each into the module that touches
it — address it head-on ("a common assumption is X; the next measurement tests it"), and reuse
it as that module's predict step or as a quiz distractor. Skip the diagnostic only when the
user's level is already demonstrated (they built the system, or the conversation makes it
obvious) or they explicitly decline the interview.

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

- Recommend slicing it into a foundational **"Workshop 1"** plus focused follow-ons
  (Workshop 2, 3, …), each sized to one sitting, and
- Present the **series plan**: each workshop's slice and what it assumes from the earlier ones.

Let the user accept the series plan, pick a different slicing, trim to just Workshop 1, or
explicitly override and proceed as one full-size workshop. Producing one bloated workshop is a
failure mode — a series of focused ones is almost always the better outcome.

**One invocation builds the whole series.** When the user accepts the series plan, do not defer
the follow-ons to future runs: this same invocation builds every workshop in the series. Run
Phase 0 once, up front, for all of them (one interview covers audience, depth, shape, and the
slicing approval; do not re-interview per workshop), and run Phase 1 once against the union of
tooling the whole series needs. Then build the workshops in dependency order, Workshop 1 first,
each into its own sibling `<slug>/` directory with its own modules, captures, and exam. Wire
the series together: each landing page carries a short series section listing every installment
with links, plus explicit predecessor/successor pointers ("builds on Workshop 1's ..."). Later
workshops assume the reader finished the earlier ones, so their vocabulary primers stay lean and
reference back instead of re-teaching. The full-size override is the one case that stays a
single workshop (usually the multi-page wiki shape).

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

(Best-fit diagram if it explains the model better than prose — see step 4.
Sample code if the concept manifests in code — see the sample-code rule below.)

**Question.** Discovery prompt; 2-4 sub-questions if useful.

→ [Answer Key — Module N](#answer-key--module-n)
```

Let the Phase 0 depth rubric drive the module count. Place all answer keys in a single section at
the end.

**Present every capture in three beats: the code, the output, the walkthrough.** A capture
teaches only when the reader can see what ran and what the numbers say, so structure each one
the same way:

1. **The code that emits it.** Quote the exact lines, including the `print`/`log` calls that
   write the output. This is stricter than it sounds: a snippet that merely computes related
   values, followed by output none of the shown lines print, breaks the chain of custody.
   Introduce the block with narrative provenance (next rule): which pass of the script, what it
   does, which log lines it writes.
2. **The output, verbatim.**
3. **A "let's go deeper" walkthrough** that reads the key figures aloud: what each column or
   field means, and which value the argument turns on.

A worked before/after, from a real review. The weak version showed a two-moons *generation*
snippet, then this output, then a bare citation:

```text
samples: 1000 (500 per class), noise sigma = 0.1
split: 800 train / 200 test
(Captured in captures/results.log lines 8-10.)
```

The generation code never prints those lines, the citation names a file the reader has no way
to browse, and the numbers are left to speak for themselves. The fixed version runs the three
beats: "Section 1's pass then shuffles, holds out a test set, and logs the dataset's vital
signs; these `log(...)` lines write the capture below, at lines 8-10:", then the actual
`log(f"  samples: ...")` lines, then the output, then "Let's go deeper: 1,000 points, perfectly
balanced at 500 per class, so 50% accuracy is exactly the coin-flip baseline; 200 points held
out, so every accuracy quoted is on data the network never saw."

The bar: a reader should never meet a number without knowing what ran to produce it and what it
is telling them.

**Cite the producer, not just the artifact — and do it as narrative, not a bracketed
afterthought.** Every capture must be traceable to the run that produced it: the script (linked
to its source-listing page, see the wiki notes), its section marker, and the log lines. But
weave that provenance into the sentence that *introduces* the capture, rather than a mechanical
parenthetical trailing it. "(Captured in `captures/results.log` lines 14–15.)" after the block
reads as random; "(Measured by the [S3] pass; log lines 25 and 29.)" is traceable but still
reads as bureaucracy. The narrative form teaches: "When [Section 3's pass of the experiment
script](experiment-source.html) runs (it is the part that constructs the networks and inspects
their starting state), these are the statistics obtained (`captures/results.log` lines 25 and
29):" followed by the output block. Name the pass, gloss what it does in one clause, give the
log lines, then show the capture. And spell section markers out as readable phrases ("Section
3's pass of the experiment script", hyperlinked to the source page). Prose must never make the
reader decode a bracket code like "[S3]" cold: use one only after the module itself has clearly
defined what it means, and if the definition lives elsewhere (another module, the source page,
the log), hyperlink the code to that definition with a brief gloss inline.

**Quoted snippets are verbatim, or explicitly abridged — never paraphrased.** Readers copy
snippets and diff them against the source, so every code fence must match the script
byte-for-byte as a *contiguous* region. Don't inline constants the real code keeps in
variables, don't collapse two lines into one, and never drop `...` placeholders *inside* a
fence. If lines must be omitted, split into two verbatim fences and put the elision in the
prose between them, with the link to the full source-listing page alongside. Verify
mechanically after drafting: check that each `python` fence matches a contiguous slice of the
script (a ten-line checker beats eyeballing; real audits caught both a paraphrased line that
never existed in the script and a fence missing one interior line). One deliberate exception:
a **minimal-essence illustration** — a few lines that teach the *idea* of a mechanism without
the real script's generality. Allowed, but the introducing sentence must visibly label it
("boiled down to its essence", "an illustration, simplified from the real code") and pair it
with a link to the real implementation on the source page. Never pass an essence snippet off
as a quote, and whitelist it explicitly in the fence checker.

**The main path teaches; the harness stays backstage.** A reader must be able to complete a
module's conceptual journey without opening the experiment script or the raw log — those are
provenance, not required reading. Show code on the main path only when *every line shown
serves the lesson*. The real failure this rule comes from: a module quoted the experiment's
full generalized `forward()` (normalizer slots, an inactive residual branch, record-keeping
dicts, comments pointing at a later module) to teach three ideas — save each activation, ask
autograd to retain its gradient, read `activation.grad` after `backward()`. The generality
buried the lesson. The fix: state the idea as numbered steps, show the smallest verbatim
snippet that runs the measurement (often 3–5 lines), put the PyTorch/tool mechanics in a
collapsible optional section as a labeled minimal-essence illustration, and link the full
implementation on the Source page for the curious. Two corollaries:

- **Never show plotting or logging code on the main path.** Colors, `semilogy` calls, and
  format strings teach nothing about the topic; the chart itself plus a one-clause "computed
  and logged by Section N's pass" citation carries all the provenance.
- **Inactive machinery must not surface in the main path.** A shared experiment class serving
  many variants is *good design* (one code path is itself a control — variants differ only in
  options); the mistake is only making the reader tour it. If an identity normalizer or a
  disabled branch shows up in something you quote, either quote a smaller region or spend at
  most one sentence turning it into a foreshadow of the module that activates it.

**Technical topics teach through sample code, not just commands and prose.** For
computing-related topics, a short code sample is often the clearest statement of a concept —
an API's contract, a data structure's shape, a race window, a syscall sequence. Any module
whose concept manifests in code should show some, drawn from one of two sources:

1. **An excerpt from the experiment / reproducer script** — prefer this; it is already
   grounded, and the verbatim-quoting rules above apply unchanged.
2. **A purpose-written illustration snippet** — brand-new code written only to teach, for when
   the experiment script has no suitably small region. Three rules keep these honest:
   - **Run it.** A snippet that shows output is an experiment: execute it, save the source
     under `snippets/`, capture its output like any other run, and cite both. Code that
     genuinely cannot run (pseudo-code sketching an algorithm) must show no output, and the
     introducing sentence must label it pseudo-code.
   - **Label it.** Introduce it as standalone teaching code ("a minimal, self-contained
     snippet — not part of the experiment script") so it is never mistaken for the real
     implementation. Same honesty bar as the minimal-essence rule above.
   - **Keep it minimal.** Every line shown serves the lesson (the main-path rule applies);
     if it needs imports and boilerplate to run, show only the teaching region and note that
     the file in `snippets/` holds the runnable whole.

   A snippet shown in full in the module body needs no Source page of its own. When only its
   teaching region is shown, the runnable whole is a raw artifact like the experiment script:
   in the wiki shape, render it on a Source page (one page can hold every snippet) per the
   never-hyperlink-raw-files rule in step 5b, and link the prose mention to that page.

**Shape measurement modules as predict → run → observe → explain.** The weak shape is
read-prose → inspect-script → inspect-log → read-interpretation. The strong shape:

1. **Predict** — before showing any result, have the reader commit (a one-line callout: "if
   each layer keeps a tenth of the signal, how much survives four layers? Write it down").
2. **Run** — one small command or snippet produces the measurement (see the main-path rule
   above for how much code that should be).
3. **Observe** — lead with the most intuitive artifact (a diagram or plot of the measured
   thing), then the core numbers as a *designed* table (next rule). Let the prediction land
   or break here.
4. **Explain** — only now the formula/mechanism, tied to quantities the reader just saw.
   When the explanation must *diagnose* between causes, present the competing hypotheses
   first, each with what it would predict in the measurements, then reveal the measured
   verdict. "It's not saturation" discovered beats "it's not saturation" asserted.

Close the loop with a **change-one-variable exercise**: name the script's knobs (depth,
width, activation, init scale), ask for a prediction per turn of a knob, and wire each to a
measurement the script already logs so the reader can check immediately.

**The core result gets a designed table, not a log dump.** The single most important
measurement in the workshop deserves the most deliberate presentation, not a monospace
capture with nine columns. Build a small markdown table: ordered in the direction the
narrative travels (e.g. the direction the gradient flows), with a derived column that does
the division for the reader ("retained from previous layer: 12%, 10%, 9.6%"), introducing
**one quantity at a time** (the traveling signal first; the per-parameter gradient as its
consequence, second). The raw capture still appears — linked, or shown later at the moment
its extra columns become relevant (e.g. in the diagnosis step) — because it proves
provenance; but it is the instrument readout, not the lesson. And state the scope of the
numbers explicitly: exact norms depend on seed, width, and batch, so tell the reader "rerun
in the pinned environment and the log matches byte for byte; change anything and every digit
moves — the finding is the ratio structure, not the digits."

**The experiment script is reader-facing — comment it like a teaching artifact.** It gets
rendered as the Source page and copied by readers, so a banner comment per section is not
enough: give the module a docstring, every function a docstring, and intersperse why-comments
throughout the body in the **annotated-walkthrough style** — a standalone comment line above
each logical step, with a blank line between steps — rather than sparse trailing comments:

```python
        # Set the manual seed so that different configurations (norm/act/...)
        # start with the exact same weight values, for a fair comparison.
        torch.manual_seed(SEED)

        # Dimensions: input (2 features) -> depth hidden layers -> output.
        dims = [2] + [WIDTH] * depth
```

Since quoted snippets must stay verbatim, write the comments *before* quoting — and re-run the
script afterward to prove the captured log is byte-identical.

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

**The overview — and every forward reference — speaks only the reader's starting vocabulary.**
The landing/overview page (single-page: everything before Module 0; wiki: `index.md`) is read
before anything has been taught, so it must be fully understandable with nothing but the
prerequisites from Phase 0. The same goes for forward references anywhere ("as Module 5 will
show…"), for module-opening "Goal" lines, and for takeaway/summary bullets that preview a later
module's finding. The jargon rule above has a blind spot here: the overview *wants* to preview
the punchline, and the punchline usually involves concepts only a later module introduces. The
fix is not to define those concepts on the landing page (that bloats it) — it is to **phrase
previews as outcomes, not mechanisms**: tease *what the reader will find*, in plain words, and
leave the *vocabulary of how* to the module that teaches it.

Wrong (real example, from an overview page): "the standard explanation for why batch norm helps
('it keeps the sigmoid out of its saturated region') is measurably wrong for this network" —
the reader doesn't yet know what batch norm computes, what saturation means, or that a standard
explanation exists. Right: "along the way you'll test the most common textbook explanation for
*why* the fix works — and find, by direct measurement, that it's wrong for this very network."
A second real example, from an early module's takeaway bullets: "every trip through a sigmoid
*multiplies* a gradient by at most 0.25" — asserted before anything explained why backprop is
multiplicative. Either add the two-sentence build-up (rates chain by multiplying) right there,
or phrase the takeaway without the unearned mechanism.

Litmus test: reread the overview and each module's opening and closing lines pretending you know
only the stated prerequisites plus what earlier pages taught. Any clause that would make that
reader ask "what's that?" or "why would it work that way?" gets a build-up, a rephrase to its
outcome, or the axe. Run this as an explicit audit pass after drafting, not as a hope.

**Coherence audit: every "the X" points at something on the page, every heading is cashed
below it.** After drafting, reread each page top to bottom and check three things (each a
real reader flag):

- **Antecedents.** "The fact", "this problem", "check it": whatever the phrase points at
  must sit within the previous sentence or two, on the same page. If the referent is far
  away, restate it ("check the claim just made: does 'bank' really get the same row in
  both matrices?") instead of pointing at it.
- **Headings are promises.** The first paragraph under a heading must explicitly connect
  to the heading's claim. Real failure: a heading said "the lookup table cannot see the
  sentence" and the paragraph below said only "the table has one row per word", leaving
  the reader to derive the chain themselves (one row = one fixed meaning = the same
  vector in every sentence).
- **One name per concept, one meaning per name.** When a synonym enters, connect it
  explicitly ("the weights, each word's blending recipe"); never reuse a phrase with a
  second meaning nearby. Real failure: "one row per word" meaning one row per vocabulary
  word in the table, then one row per sentence position in the matrix, two sentences
  later.

**Goal lines pose the question; they don't preprint the answer.** A measurement module's
**Goal** (and its blurb on the landing page) should be inquiry-driven — what will be measured
and what the measurement will decide — not a spoiler of the measured value. Real example:
"measure the per-layer gradient cliff: a factor of ~0.1 per layer" hands over the punchline
the module exists to let the reader discover (and kills the predict step). Better: "measure
how much gradient survives at each layer, and use the measurements to decide whether the loss
comes from saturation, weight scale, or their combination." The same goes for charts: **a
figure shown in module N must not carry a later module's cure** (the fix's curve sitting next
to the failure answers a question the reader hasn't asked yet). Render a solo variant of the
figure for module N, show the comparison in the module that introduces the fix, and if you
want the pull-forward, make it an explicit one-sentence teaser at the module's end ("next, the
same measurement with X added").

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

A corollary: **a formula with a one-line gloss is still only naming.** BCE presented as
`L = −[y ln p + (1−y)ln(1−p)]` plus "the negative log of the probability on the correct answer"
was flagged by a real reader as "not really explained — a passing mention." Explaining a formula
means walking why it has its shape: what need rules out the naive alternative (accuracy is a
staircase with no slope to follow), what each piece does (the y and 1−y factors select the
branch — say so explicitly), and worked values at the extremes (right = 0, shrug = ln 2,
confidently wrong = unbounded). If the reader could not re-derive the formula's *purpose* after
your paragraph, it was a mention, not an explanation.

**Verify the mechanism by measurement — don't repeat the textbook story on faith.** The whole
point of a grounded workshop is that you can *check* the causal claim, not just the numbers. Before
you write "X happens because Y," measure Y in the same script that produces your other captures. It
is common to find that the textbook explanation for a phenomenon is wrong *for your specific
setup*, and catching that makes the workshop far better than the ones that parrot the standard
story. (Real example from the batch-norm workshop: the standard "batch norm helps because it keeps
the sigmoid out of its saturated, flat region" turned out to be false at initialization — a
one-line measurement showed the plain network's average slope was already 0.24, near the 0.25
maximum, *not* saturated. The real mechanism was scale-preservation across depth. Measuring the
pre-activations is what surfaced the correct story.) When your mechanism claim depends on an
internal quantity (a slope, a variance, a distribution, a rate), **print that quantity** and cite
it like any other captured number. Two sharpenings, both from real reader pushback:

- **A mean can hide a tail.** When the argument is "not X" and the evidence is an average
  ("mean slope 0.24, so not saturated"), also print a distribution statistic: the fraction of
  units beyond a threshold, a min/median, or a histogram. "Mean slope 0.242, units with slope
  < 0.05: 0.0%" closes the loophole the mean alone leaves open.
- **Name metrics neutrally.** A column called `W shrink` presumes the value is below 1 and
  confuses the reader the first time a configuration amplifies. Prefer direction-neutral
  names (`W gain`, "RMS matrix gain") and let the measured value say which way it goes.

**Develop the intuition for a mechanism — don't just assert it.** When a step in your explanation
rests on *how* or *why* something works (not merely *that* it does), build the reader up to it
instead of stating it as a fact to memorize. Assert-it-cold writing — "the gradient is multiplied
at each layer", "the WAL is fsync'd before the commit returns", "the lock is dropped before the
callback fires" — leaves a beginner nodding without understanding. Earn the claim: give the
plain-English reason, an analogy or a small worked example, and *then* the formal statement. Litmus
test: for every "because" and every mechanism your argument leans on, ask *"could a reader who has
never seen this reconstruct why — or are they taking my word for it?"* If the latter, add the
build-up. (Real example from the batch-norm workshop: an early draft asserted "backprop multiplies
the gradient by one factor per layer"; the fix developed *why* the signal travels backward and
*why* the chain rule makes it a product — a relay of per-layer "conversion rates" with a
`0.2 × 0.1 = 0.02` worked example — *before* leaning on that fact.) This is the twin of the
load-bearing-objects rule above: that one says show the *property*; this one says show the
*reasoning* that uses it.

**Corner the mechanism with failed attempts before you build it.** Naming the problem is not
the same as making the reader feel why *this* mechanism is the answer. Before presenting a
design (a blend, a cache, a lock, a normalizer), run the argument as attempts:

1. State the problem as a concrete failure the reader can verify on real numbers.
2. Show the **do-nothing counterfactual** — what happens *without* the mechanism — ideally as
   a one-line logical or measured consequence ("the input row is identical in both sentences,
   and identical inputs give identical outputs, so no downstream computation can ever recover
   the context").
3. Try the **naive simplest fix** first, worked out on the same real numbers, and let its
   specific failure *name the requirement* the real design satisfies.
4. Only then introduce the mechanism, which now arrives as the unique survivor of the
   failures rather than as a gift from the author.

(Real example, from reader feedback on the attention workshop: the weighted blend was
introduced as "the simplest possible flow is averaging", and the reader asked why blend at
all. The fix walked the chain: no mixing is *provably* context-blind; an equal average
repairs that but pastes one sentence-summary vector over every word and gives filler words a
full share; those two failures force exactly per-word, relevance-weighted mixing — which is
what attention is.) Two placement notes: the mechanism's *name* belongs at this moment too —
once the requirement is on the table, "those per-word mixing weights are the *attention*"
lands as a summary instead of jargon — and the naive attempt is a natural predict moment
("one problem gets fixed and a new one appears; name both before reading on").

**Data needs a story: before, after, and what the mechanism did.** A table of numbers
never speaks for itself. Present it as a narrative that uncovers its real meaning: here
is the data *without* the mechanism, here it is *with* it, and the mechanism did X and Y.
When a module's payoff is a transformation, tell that story on one concrete datum:

1. **Before** — the input as a small labeled table, plus what it means in plain words
   ("bank's row reads: maybe water, maybe money, no evidence either way; definitely a
   place").
2. **The work** — each contribution as a full table row (weight times vector, every
   slot), with the sum as the last row, so the reader watches the output get built.
3. **After** — input and output side by side, each change named and explained ("water
   0.3 → 0.435: river poured its water in; money 0.3 → 0.149: nobody else brought any").
   End on what the output now means, against what the input meant; that contrast is the
   meaning the raw numbers were hiding ("was: ambiguously both kinds of bank; now: given
   'river' is nearby, the water kind").

(Real example: the attention workshop showed bank's logged output vectors and traced just
two multiplications in a dense paragraph; the reader called it "terse and dense". The fix
was this story — bank's row before blending, the three weighted rows and their sum, then
the before/after with the changes named: blending raised water and cut money, so "bank"
now leans to the river meaning.)

The intermediate numbers may be plain arithmetic derived from logged values (state the
derivation, cite the logged inputs, and note when rounding can drift the last digit
against the logged output) — no need to re-run the experiment and shift every downstream
log citation. Litmus test: could the reader rebuild the output from the input with a
pencil, using only what is on the page?

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

**Match the diagram type to the relationship it must show — a block diagram is not the
default.** Ask first what *kind* of thing the reader needs to see, then pick the form that
shows it (the full selection guide is in the handson-diagrams skill under "Diagram Type
Selection"):

| The idea to show | Best-fit diagram | Tool |
|------------------|------------------|------|
| Components and how they connect (architecture, pipeline, layers) | Block diagram | D2 (ELK) |
| Who-talks-to-whom over time (protocol handshake, API call chain, IPC) | Sequence diagram | D2 `shape: sequence_diagram` |
| Branching decision logic (algorithm, retry policy, hit/miss path) | Flowchart | D2 |
| Lifecycle with states and transitions | State machine | D2 (see handson-diagrams `state-machines.md`) |
| Overlap / membership among a few sets (feature matrices, taxonomies) | Venn diagram | matplotlib (`matplotlib-venn`) |
| A handful of named quantities compared | Bar chart | matplotlib, from the experiment script |
| The distribution of many measurements | Histogram (one group); box plot (comparing groups) | matplotlib, from the experiment script |
| A function or measurement against a continuous variable | Line plot (log axis for geometric growth/decay) | matplotlib, from the experiment script |
| Events on a shared time axis | Timeline | ASCII |

The split to keep in mind: **D2 is for structure, plots are for quantities.** For *quantitative*
topics — anything involving a function, a distribution, a curve, a measurement over time — a
**plot of the real thing beats a box diagram every time**, and it's the most under-used tool in
weak workshops. Generate plots with matplotlib *inside the same experiment script that produces
your captures*, so they're real, not sketched:

- the actual **function** you're reasoning about (e.g. an activation and its derivative, a loss
  curve, a latency-vs-load curve) — annotate the load-bearing feature (the max, the knee, the
  saturation region);
- the actual **dataset** (a scatter of the real points), so the reader sees the problem;
- a **measured quantity across the run** (gradient size per layer, throughput per thread, a
  histogram of the distribution you claim shifts);
- a **worked illustration of the mechanism** (e.g. multiplying a sub-1 factor per layer on a log
  axis to show geometric decay).

A plot that comes straight from `experiment.py` is grounded the same way a captured log line is —
prefer it over an abstract drawing whenever the point is quantitative. Keep D2 for the structural
picture and reach for a plot for everything numeric.

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

**Tall/narrow diagrams are auto-sized — don't fight the column.** A vertical stack of a few boxes
(e.g. a layer stack, a backprop chain) is *portrait*: much taller than wide. Stretched to the full
content column it looks absurd and its own text balloons. The HTML generators handle this for you:
`embed_images()` reads each PNG's dimensions and, when height > 1.25× width, tags it
`class="img-portrait"`, which the stylesheet caps at ~380 px wide and centers. So render such
diagrams normally (`rsvg-convert -w 1500`) and let the generator shrink the *display* size — no
manual width juggling. Wide diagrams (charts, most architectures) are untouched and still fill the
column. When you screenshot to verify, confirm portrait diagrams render compact (not column-width)
and their text stays legible at the cap.

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
(`pip install markdown beautifulsoup4 pygments`), plus `latex2mathml` if the workshop contains
math (`pip install latex2mathml`). It produces a self-contained `WORKSHOP.html`
beside the markdown file with:

- **Sticky sidebar** ToC with JS scroll-position highlighting (h2 + h3 headings)
- **Quiz sections** rendered as blue callout boxes
- **Answer key sections** wrapped in collapsible `<details>` (click to reveal)
- **Optional deep-dive sections** — any h3/h4 with an explicit `{#optional--<slug>}` anchor
  (e.g. `### How was this measured? {#optional--how-measured-2}`) is wrapped in a collapsible
  `<details>` (violet accent, closed by default) and kept out of the sidebar nav. Use these to
  keep instrumentation, tool mechanics, and long derivations available but off the main
  teaching path; links targeting content inside still work (the anchor JS opens the box)
- **Syntax-highlighted code** via Pygments github-dark theme
- **Diagram PNGs/SVGs** embedded as base64 (fully self-contained, no external deps)
- **LaTeX math** — write display math as `$$...$$` and inline math as `\(...\)` in the markdown;
  the generator renders both to native MathML (no JS, no fonts, still fully self-contained).
  Bare single-dollar `$...$` is deliberately NOT supported (false positives on prices). Math
  inside code fences/spans is left alone. If `latex2mathml` is missing the source text passes
  through unchanged with a warning.
- **Copy-code buttons** — every code block gets a copy icon (async clipboard API on secure
  contexts, hidden-textarea fallback for plain-HTTP hosting). Anything a reader might want to
  paste — commands, snippets, the experiment script — should therefore live in a fenced code
  block, not in prose.
- **Responsive** — sidebar collapses to a hamburger menu on narrow viewports

Re-run this command any time WORKSHOP.md changes. The generator is idempotent.

### 5b. Multi-page "wiki" output (for large workshops)

When the workshop is large, deep, or heavily expanded — or the user asks for a wiki — build it as
**one page per module** instead of one long scroll. Use the companion generator
`assets/wiki-generator.py` (it reuses the exact same styling and JavaScript as the single-page
generator, so the two look identical; it only adds the cross-page sidebar and prev/next chrome).

Author the content as separate markdown files under `content/` — `index.md` (the landing/roadmap
page) plus `module-0.md`, `module-1.md`, … — and describe the page order in a `content/wiki.json`
manifest:

```json
{
  "title": "My Workshop",
  "output_dir": "..",
  "pages": [
    {"slug": "index",    "file": "index.md",    "nav": "Overview"},
    {"slug": "module-0", "file": "module-0.md", "nav": "0 · Basics"},
    {"slug": "module-1", "file": "module-1.md", "nav": "1 · Deeper"},
    {"slug": "exam",     "href": "exam.html",   "nav": "Final Exam", "external": true}
  ]
}
```

Then generate every page in one shot:

```bash
python3 <skill-dir>/assets/wiki-generator.py content/wiki.json
```

Notes specific to the wiki shape:

- `output_dir` is resolved relative to the manifest; use `".."` so pages land beside `diagrams/`
  and `captures/` at the workshop root. Reference images from the markdown as `../diagrams/foo.png`
  (they're embedded as base64, so the emitted HTML is still fully self-contained).
- Each module page holds **its own quiz and answer key** — use `### Quiz {#quiz-N}` and
  `### Answer Key {#answer-key--module-N}` within that page; the generator wraps them into the blue
  callout and collapsible `<details>` exactly as in the single-page flow, and prev/next links come
  from the manifest order. `{#optional--*}` deep-dive sections (step 5) work per page the same
  way.
- The exam is a prebuilt `exam.html`; list it as an `"external": true` page so it appears in the
  sidebar without the generator trying to render it. Point the exam's answer-explanation links at
  the module pages (`module-N.html`), not a `WORKSHOP.html`.
- Same dependencies (`markdown`, `beautifulsoup4`, `pygments`, `latex2mathml` for math). Re-run
  after any content change.
- **Never hyperlink raw non-HTML files** (the experiment script, log files) from wiki pages —
  static hosts and portals frequently 404 them. Instead render BOTH artifacts as wiki pages:
  the experiment script (a one-paragraph frame with the run command and determinism note, then
  one fenced block with the full script; nav e.g. "Source · experiment.py") and the captured
  log (nav e.g. "Log · results.log") with **line numbers prefixed** so the modules' "lines
  25 and 29" citations can be looked up directly. Link every prose mention of either artifact
  to its page — a line-number citation with no browsable target reads as random. Keep both
  regenerable: a tiny helper that rewrites the markdown from the real files beats
  hand-copying, which drifts.
- `index.md` is read first: it must pass the overview-vocabulary rule from step 3 — punchlines
  phrased as outcomes, no reliance on terms the modules will introduce.

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

- Link to `exam.html` near the top *and* in a final "Final Exam" section. (Single-page: from
  WORKSHOP.md. Wiki: from `index.md` and the last module page; the exam also sits in the sidebar.)
- Bidirectional quiz ↔ answer key links — both anchors must be explicit:
  - Quiz heading: `### Quiz N {#quiz-n}` + trailing `→ [Answer Key — Module N](#answer-key--module-n)`
  - Answer-key heading: `### Answer Key — Module N {#answer-key--module-n}` + trailing `↑ [Back to Quiz N](#quiz-n)`
  - In the wiki shape the quiz and its answer key live on the same module page, so these anchors
    resolve within that page.
- Answer-key explanations should reference the module (single-page: the section; wiki:
  `module-N.html`) that taught the concept.
- **Beware heading-slug drift between renderers.** GitHub and the Python-Markdown generator
  slugify headings differently — a heading with a spaced em-dash (`## Module 0 — Basics`) becomes
  `module-0--basics` on GitHub but `module-0-basics` in the generator, silently breaking a
  hand-written anchor in one of them. Avoid ` — ` in headings you link to (use a comma or reword),
  or rely on explicit `{#id}` anchors. After generating, audit that every in-page `href="#..."` has
  a matching `id=`, and every cross-page link resolves to a real file/anchor.
- If experiments need a specific environment, add a `## Reproducing this workshop` section with the
  exact setup / version / build steps used to capture the output.

### 8. View / share your workshop

The generated HTML (`WORKSHOP.html` for single-page, or `index.html` + `module-*.html` for the
wiki) and `exam.html` are fully self-contained (all CSS, JS, and images inlined), so there is
nothing to deploy — they work straight from the filesystem:

- **Open directly** in a browser (`file://…/WORKSHOP.html`, or `file://…/index.html` for a wiki), or
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
| Depth | Matched to the level the interview *and* diagnostic questions measured | One-size-fits-all, or trusting self-report blindly |
| Prerequisites | Confirmed installed (or gaps surfaced) before drafting | Commands the author can't actually run |
| Commands | Real captured output, cited to a file | Invented / handwave output |
| Captures | Citation names the producing script + section | "(captured in foo.log)" with no producer |
| Teaching path | Minimal lesson-serving snippets; harness behind optional sections | Framework `forward()` + plotting loops on the main path |
| Sample code | Verbatim script excerpts, or runnable snippets with captured output | Pseudo-code passing as real; snippet output never actually run |
| Core result | Designed table, one quantity at a time, ratios framed | Nine-column log dump as the primary presentation |
| Payoff data | Told as a story: before, each contribution, the sum, after, changes named | Log dump plus two multiplications in dense prose |
| Overview / previews | Outcomes in the reader's starting vocabulary | Leans on concepts a later module introduces |
| Diagrams | Explain the mental model; type fits the relationship (sequence for time-order, histogram for distributions) | Decorate; restate the prose; block diagram for everything |
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
  guessing them wastes the reader's time. And don't stop at self-report: the technical
  diagnostic questions (Phase 0) are what catch a self-described intermediate who is actually
  a beginner, and the reverse.
- **Don't fabricate command output.** If you can't run it, say "the output should resemble:" and
  label it explicitly. Prefer capturing real output even from a small probe.
- **Don't show snippet output you never ran.** A purpose-written illustration snippet is an
  experiment like any other: run it, keep the source in `snippets/`, capture the output, cite
  both (see step 3).
- **Don't default every illustration to a block diagram.** Time-ordered interactions want a
  sequence diagram, branching logic a flowchart, a distribution a histogram, set overlap a
  venn; pick the form that shows the relationship (see the table in step 4).
- **Don't install tooling silently.** Surface the gap, propose the fix, and install only after the
  user approves.
- **Don't write quizzes that pattern-match the prose.** A reader who skimmed should get them wrong;
  a reader who *understood* should get them right.
- **Don't write numerically ambiguous quiz questions.** If the answer is a product of N
  factors, the wording must pin N: "the gradient must cross six transformations, each
  retaining 0.1 — estimate what survives" is answerable; "a 6-hidden-layer network shows a
  factor of 0.1 per layer — estimate the ratio" is not, because the reader cannot tell how
  many multiplications separate the two quantities being compared.
- **Don't make the reader tour your instrumentation.** The main path never requires opening
  the experiment script or the raw log; measurement mechanics live in a collapsible
  `{#optional--*}` section and the full source stays on the Source page (see step 3).
- **Don't hand over a mechanism the problem hasn't forced yet.** "The fix is X" arriving
  before the reader has watched the do-nothing counterfactual and the naive attempt fail
  reads as a gift from the author; corner the design with failed attempts first (see step 3).
- **Don't compress a transformation into scalar highlights in prose.** If the payoff is
  "X became Y", tell the before/after story with every contribution and the visible sum
  in a table; a paragraph tracing one or two products through the blend is provenance,
  not teaching (see the data-needs-a-story rule in step 3).
- **Don't spoil the discovery.** Goal lines and landing-page blurbs pose the question rather
  than quoting the measured punchline, and a module's figures must not carry a later module's
  fix (teaser sentence at the end instead; see step 3).
- **Don't create a workshop without a reproducibility section** when experiments depend on specific
  software versions, hardware, or setup — future readers will not remember.
- **Don't preview mechanisms in vocabulary the reader doesn't have yet.** The overview and all
  forward references tease outcomes in plain language; the module that introduces a concept owns
  its vocabulary.
- **Don't use emoji or em-dashes** in workshop content (WORKSHOP.md, wiki pages, exam.html).
  Em-dashes read as mannered filler at scale — rewrite with commas, colons, parentheses,
  semicolons, or shorter sentences. En-dashes in numeric ranges ("lines 14–15") are fine.
  This includes generated chrome: page-title separators, exam headings, score strings.
