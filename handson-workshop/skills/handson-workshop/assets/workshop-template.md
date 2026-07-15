# {{TOPIC}} — Hands-On Workshop ({{CONTEXT}})

> {{ONE_LINE_DESCRIPTION}}

**Time required:** {{ESTIMATE}}
**Difficulty:** {{LEVEL}}
**Final exam:** [exam.html](exam.html) (15-20 questions, auto-graded, 70/100 to pass)

Each module has the same shape:

- **Goal** — one sentence
- **Setup** — what state your system should be in
- **Commands** — exact lines to copy
- **Expected output** — the literal output captured from a real run
- **Diagram** — best-fit diagram explaining the model: block, sequence, flowchart, state
  machine, venn, or a chart (bar / histogram / box plot), used when prose alone is not enough
- **Sample code** — for technical topics: a verbatim excerpt from the experiment script, or a
  minimal runnable illustration snippet with its output captured
- **Quiz** — discovery prompts, with a link to the answer key

## Table of Contents

- [Prerequisites](#prerequisites)
- [Module 0: Vocabulary primer](#module-0-vocabulary-primer)
- [Module 1: {{NAME_1}}](#module-1-{{slug_1}})
- [Module 2: {{NAME_2}}](#module-2-{{slug_2}})
- [Module 3: {{NAME_3}}](#module-3-{{slug_3}})
- [Module 4: {{NAME_4}}](#module-4-{{slug_4}})
- [Final Exam](#final-exam)
- [Answer Key](#answer-key)
- [Reproducing this workshop](#reproducing-this-workshop)
- [What's next](#whats-next)

## Prerequisites

- **Hardware:** {{HARDWARE}}
- **Software:** {{SOFTWARE}}
- **Background:** {{KNOWLEDGE}}

If you want to recreate the experiments yourself, jump to [Reproducing this workshop](#reproducing-this-workshop). Otherwise, the captured output is included inline so you can read along.

---

## Module 0: Vocabulary primer

*(Optional but strongly recommended for jargon-heavy topics. Skip if every reader already knows every term you'll use.)*

This module defines every load-bearing acronym used later in plain English. Read it once; refer back as needed. Every term that appears in **bold** anywhere in Modules 1–N should appear here first.

### Group A — {{the most fundamental terms}}

- **{{TERM 1}}** — {{2-3 sentence plain-English explanation; do not use any acronyms not yet defined}}.
- **{{TERM 2}}** — {{...}}.

### Group B — {{the next layer}}

- **{{TERM 3}}** — {{...}}.

(Continue grouping by topic — don't dump all 30 acronyms into one undifferentiated bullet list.)

If a term is so central it'll be re-introduced inline in a module, that's fine — the goal is that no reader hits a sentence containing three new acronyms in a row.

---

## Module 1: {{NAME_1}}

**Goal.** {{one-sentence goal}}

**Setup.** {{required state}}

### Concept

{{2-4 paragraphs grounding the reader in the model.}}

![Module 1 architecture](diagrams/module-1.png)

*(D2 source: [`diagrams/module-1.d2`](diagrams/module-1.d2))*

### Commands

```bash
{{actual commands a learner copies}}
```

### Expected output

```
{{verbatim output captured from a real run}}
```

(Captured in [`captures/module-1.log`](captures/module-1.log), lines NN-MM.)

Notice that {{specific observation}} — this is what makes {{concept}} work.

### Quiz 1 {#quiz-1}

1. {{Question testing the core concept}}
2. {{Question requiring connection to a captured value}}
3. {{Question that requires reasoning, not recall}}

→ [Answer Key — Module 1](#answer-key--module-1)

---

## Module 2: {{NAME_2}}

**Goal.** {{...}}

**Setup.** {{...}}

### Concept

{{...}}

![Module 2 diagram](diagrams/module-2.png)

### Commands

```bash
{{...}}
```

### Expected output

```
{{...}}
```

### Quiz 2 {#quiz-2}

1. {{...}}
2. {{...}}
3. {{...}}

→ [Answer Key — Module 2](#answer-key--module-2)

---

## Module 3: {{NAME_3}}

(Same shape: Goal / Setup / Concept / Diagram / Commands / Expected output / Quiz)

### Quiz 3 {#quiz-3}

1. {{...}}
2. {{...}}
3. {{...}}

→ [Answer Key — Module 3](#answer-key--module-3)

---

## Module 4: {{NAME_4}}

(Same shape.)

### Quiz 4 {#quiz-4}

1. {{...}}
2. {{...}}
3. {{...}}

→ [Answer Key — Module 4](#answer-key--module-4)

---

## Final Exam

When you have completed every module, take the **[Final Exam](exam.html)**.

- 15-20 questions covering every module
- Auto-graded out of 100
- Passing score: 70/100
- No time limit; retake as many times as you like

---

## Answer Key

### Answer Key — Module 1 {#answer-key--module-1}

1. **{{answer 1}}** — {{explanation that references the module's concept}}
2. **{{answer 2}}** — {{explanation}}
3. **{{answer 3}}** — {{explanation}}

↑ [Back to Quiz 1](#quiz-1)

### Answer Key — Module 2 {#answer-key--module-2}

1. **{{answer}}** — {{explanation}}
2. **{{answer}}** — {{explanation}}
3. **{{answer}}** — {{explanation}}

↑ [Back to Quiz 2](#quiz-2)

### Answer Key — Module 3 {#answer-key--module-3}

(...)

↑ [Back to Quiz 3](#quiz-3)

### Answer Key — Module 4 {#answer-key--module-4}

(...)

↑ [Back to Quiz 4](#quiz-4)

---

## Reproducing this workshop

*(Optional section — keep only if experiments require a specific environment.)*

```bash
# Worktree at the exact tag used to capture the outputs above
git worktree add -b workshop-{{slug}} ../{{worktree-name}} {{tag-or-sha}}
cd ../{{worktree-name}}

# Build / configure
{{build commands}}

# Boot or attach
{{boot commands}}
```

To re-capture each module's output:

| Module | Command(s) | Capture file |
|--------|------------|--------------|
| 1 | `{{cmd}}` | `captures/module-1.log` |
| 2 | `{{cmd}}` | `captures/module-2.log` |
| 3 | `{{cmd}}` | `captures/module-3.log` |
| 4 | `{{cmd}}` | `captures/module-4.log` |

---

## What's next

- {{follow-up topic 1}} — see {{path/to/related/report}}
- {{follow-up topic 2}}
- {{related upstream documentation}}
