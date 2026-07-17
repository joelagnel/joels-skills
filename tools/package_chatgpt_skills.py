#!/usr/bin/env python3
"""Package the joels-skills skills as agentskills.io-standard zips for ChatGPT.

Builds dist/<name>-<version>.zip for each skill, with the skill folder at the
zip root (handson-workshop/SKILL.md, ...), per the Agent Skills specification
(https://agentskills.io/specification) and ChatGPT's skill upload
(https://chatgpt.com/skills).

What it does per skill:
  - stages the source skill dir, excluding __pycache__ / *.pyc
  - rewrites SKILL.md frontmatter: packaged description (spec caps it at 1024
    chars; the repo copy of handson-workshop is longer), plus license,
    compatibility, and metadata (author/version/homepage)
  - bundles LICENSE.txt and NOTICE.txt from the repo root
  - writes agents/openai.yaml (ChatGPT UI metadata)
  - validates the spec constraints (name charset/length, name == dir name,
    description length)

Usage: tools/package_chatgpt_skills.py <version>     e.g. 1.0.0
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS_SRC = REPO / "handson-workshop" / "skills"
DIST = REPO / "dist"

# Packaged descriptions must be <= 1024 chars (agentskills.io spec). The repo
# copy of handson-workshop's description is longer, so it gets this variant.
PACKAGED_DESC = {
    "handson-workshop": (
        "Create a comprehensive, self-contained hands-on workshop for any "
        "technical topic, grounded in real experiments and captured output "
        "rather than invented examples. Use when the user asks for a "
        "workshop, hands-on tutorial, or guided learning material (e.g. "
        "'create a workshop on git internals', 'teach me HTTP caching "
        "hands-on'). First interviews the user to gauge audience level and "
        "desired depth (including quick technical multiple-choice "
        "questions), verifies the local tooling can reproduce the "
        "experiments, and can split an over-broad topic into a focused "
        "series. Produces workshop Markdown with modules (best-fit "
        "diagrams, sample code, real command output, quizzes with answer "
        "keys), a styled self-contained HTML version or a multi-page wiki, "
        "and a standalone auto-graded exam (15-20 questions, pass at "
        "70/100)."
    ),
    # handson-diagrams' repo description already fits; None = keep as-is.
    "handson-diagrams": None,
}

COMPATIBILITY = {
    "handson-workshop": (
        "Best in a code-execution environment with python3 (markdown, "
        "beautifulsoup4, pygments, latex2mathml) for HTML generation and "
        "d2 + rsvg-convert for diagram rendering."
    ),
    "handson-diagrams": (
        "Diagram rendering needs d2 and rsvg-convert; charts need python3 "
        "with matplotlib or bokeh."
    ),
}

OPENAI_YAML = {
    "handson-workshop": """interface:
  display_name: "Hands-On Workshop Creator"
  short_description: "Build hands-on workshops from real experiments"
  default_prompt: "Use $handson-workshop to create a hands-on workshop on a topic of your choice."
""",
    "handson-diagrams": """interface:
  display_name: "Hands-On Diagrams"
  short_description: "Clear D2, ASCII, and chart diagrams for docs"
  default_prompt: "Use $handson-diagrams to pick and render the right diagram for this document."
""",
}

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def rewrite_frontmatter(skill_md: Path, name: str, version: str) -> None:
    text = skill_md.read_text()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        sys.exit(f"{skill_md}: no YAML frontmatter")
    body = text[m.end():]

    desc = PACKAGED_DESC.get(name)
    if desc is None:
        for line in m.group(1).split("\n"):
            if line.startswith("description:"):
                desc = line[len("description:"):].strip()
                break
    assert desc, f"{name}: no description"

    fm = "\n".join(
        [
            "---",
            f"name: {name}",
            f"description: {desc}",
            "license: Apache-2.0 (see LICENSE.txt)",
            f"compatibility: {COMPATIBILITY[name]}",
            "metadata:",
            '  author: "Joel Fernandes (joelagnel)"',
            f'  version: "{version}"',
            '  homepage: "https://github.com/joelagnel/joels-skills"',
            "---",
            "",
        ]
    )
    skill_md.write_text(fm + body)

    # Spec validation.
    if not NAME_RE.match(name) or len(name) > 64:
        sys.exit(f"{name}: invalid skill name")
    if not (1 <= len(desc) <= 1024):
        sys.exit(f"{name}: description is {len(desc)} chars (limit 1024)")
    if len(COMPATIBILITY[name]) > 500:
        sys.exit(f"{name}: compatibility exceeds 500 chars")


def package(name: str, version: str) -> Path:
    src = SKILLS_SRC / name
    stage = DIST / "stage" / name
    if stage.exists():
        shutil.rmtree(stage)
    shutil.copytree(
        src, stage, ignore=shutil.ignore_patterns("__pycache__", "*.pyc")
    )

    rewrite_frontmatter(stage / "SKILL.md", name, version)
    shutil.copy(REPO / "LICENSE", stage / "LICENSE.txt")
    shutil.copy(REPO / "NOTICE", stage / "NOTICE.txt")
    (stage / "agents").mkdir(exist_ok=True)
    (stage / "agents" / "openai.yaml").write_text(OPENAI_YAML[name])

    zip_path = DIST / f"{name}-{version}.zip"
    zip_path.unlink(missing_ok=True)
    subprocess.run(
        ["zip", "-q", "-r", str(zip_path), name],
        cwd=DIST / "stage",
        check=True,
    )
    return zip_path


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    version = sys.argv[1].lstrip("v")
    DIST.mkdir(exist_ok=True)
    for name in ("handson-workshop", "handson-diagrams"):
        zp = package(name, version)
        size_kb = zp.stat().st_size // 1024
        print(f"built {zp.relative_to(REPO)} ({size_kb} KB)")


if __name__ == "__main__":
    main()
