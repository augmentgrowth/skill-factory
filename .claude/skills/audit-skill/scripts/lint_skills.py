#!/usr/bin/env python3
"""lint_skills — the mechanical half of a skill audit.

Stdlib only (Python 3.10+), so it runs in any repo with no install step:

    python3 <this-skill>/scripts/lint_skills.py <path> [<path> ...] [--json]

A <path> may be one skill folder (holds SKILL.md), a folder of skill folders, or a
repo root (its .claude/skills/, .agents/skills/ and skills/ are scanned).

It answers only questions a regex can answer honestly: limits, structure, links,
counts. Every finding names the rubric rule it evidences (see
../references/rubric.md) and a file:line. Judgment rules (degrees of freedom,
whether a description triggers well, whether a check loop exists) belong to the
reader, not this script — it hands them facts, not verdicts.

Findings are data, not failure: a completed scan exits 0 however many it found.
Exit 1 means the scan itself could not run (bad path, unreadable file).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

MAX_SKILL_LINES = 500
TOC_THRESHOLD = 100
MAX_NAME = 64
MAX_DESCRIPTION = 1024
RESERVED_NAME_WORDS = ("anthropic", "claude")
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
# Emphatic words that current models over-weight. Acronyms (API, JSON) never count.
SHOUTY = ("MUST", "NEVER", "ALWAYS", "CRITICAL", "IMPORTANT", "REQUIRED", "DO NOT",
          "MANDATORY", "ABSOLUTELY", "UNDER NO CIRCUMSTANCES")
SHOUTY_RE = re.compile(r"\b(" + "|".join(re.escape(w) for w in SHOUTY) + r")\b")
SHOUTY_LIMIT = 5  # occurrences per file before it reads as shouting
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
BACKTICK_PATH_RE = re.compile(r"`((?:\.{1,2}/)?(?:[\w.-]+/)*[\w.-]+\.(?:md|py|sh|js|ts|json|yaml|yml|txt))`")
BACKSLASH_PATH_RE = re.compile(r"\b[\w.-]+\\[\w.-]+\\?[\w.-]*\.(?:py|md|sh|js|ts|json|txt)\b")
TIME_BOMB_RE = re.compile(
    r"\b(before|after|until|as of)\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+20\d\d\b",
    re.IGNORECASE,
)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
CONTENTS_RE = re.compile(r"^(#{1,6}\s*)?(\*\*)?(table of contents|contents|toc)(\*\*)?:?\s*$", re.IGNORECASE)
INSTALL_RE = re.compile(r"\b(pip3?|uv pip|uv add|poetry add|pipx|npm|pnpm|yarn|bun|brew|apt(-get)?)\s+(install|add|i)\b|requirements\.txt|package\.json|pyproject\.toml")
PY_IMPORT_RE = re.compile(r"^\s*(?:import\s+([\w.]+)|from\s+([\w.]+)\s+import)", re.MULTILINE)
JS_IMPORT_RE = re.compile(r"""(?:require\(\s*['"]([^'"./][^'"]*)['"]\s*\)|from\s+['"]([^'"./][^'"]*)['"])""")
NODE_BUILTINS = {"fs", "path", "os", "child_process", "url", "util", "crypto", "http", "https",
                 "stream", "events", "readline", "process", "assert", "zlib", "buffer", "net"}
SPEC_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
# Claude Code reads these; strict validators (claude.ai upload, Skills API, OpenAI quick_validate)
# reject them. Fine for a Claude-Code-only skill, so they are reported as facts, not findings.
CLAUDE_CODE_KEYS = {"when_to_use", "argument-hint", "arguments", "disable-model-invocation",
                    "user-invocable", "disallowed-tools", "model", "effort", "context", "agent",
                    "background", "hooks", "paths", "shell"}
TARGET_MODEL_KEYS = ("target-models", "target_models")
SKIP_DIRS = {"cases", "evals", ".git", "node_modules", "__pycache__", ".venv", "venv"}
NON_REFERENCE_FILES = {"SKILL.md", "CHANGELOG.md", "README.md", "LICENSE.md", "LICENSE.txt"}


@dataclass
class Finding:
    rule: str
    level: str          # "fix" = rule broken; "check" = a reader must judge it
    file: str
    line: int
    message: str


@dataclass
class SkillReport:
    skill: str
    path: str
    facts: dict = field(default_factory=dict)
    findings: list[Finding] = field(default_factory=list)

    def add(self, rule: str, level: str, file: Path | str, line: int, message: str) -> None:
        rel = Path(file).relative_to(self.path).as_posix() if Path(file).is_absolute() else str(file)
        self.findings.append(Finding(rule, level, rel, line, message))


# --- discovery --------------------------------------------------------------


def discover(paths: list[str]) -> list[Path]:
    found: list[Path] = []
    for raw in paths:
        p = Path(raw).expanduser()
        if not p.exists():
            raise SystemExit(f"lint_skills: no such path: {raw}")
        if (p / "SKILL.md").is_file():
            found.append(p)
            continue
        roots = [p / ".claude" / "skills", p / ".agents" / "skills", p / "skills"]
        roots = [r for r in roots if r.is_dir()] or [p]
        for root in roots:
            for child in sorted(root.iterdir()):
                if child.is_dir() and (child / "SKILL.md").is_file():
                    found.append(child)
    seen, unique = set(), []
    for f in found:
        key = f.resolve()
        if key not in seen:
            seen.add(key)
            unique.append(f)
    return unique


# --- text helpers -----------------------------------------------------------


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def prose_lines(lines: list[str]) -> list[tuple[int, str]]:
    """(1-based line number, text) for lines outside fenced code blocks."""
    out, fenced = [], False
    for i, line in enumerate(lines, start=1):
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
            continue
        if not fenced:
            out.append((i, line))
    return out


def strip_inline_code(text: str) -> str:
    return re.sub(r"`[^`]*`", "", text)


def split_frontmatter(lines: list[str]) -> tuple[dict[str, str], int, str | None]:
    """Flat key: value reader, plus one nested level under `metadata:`.

    Returns (fields, body_start_index, error). Folded/indented continuation lines are
    joined onto their key; `metadata` sub-keys land in fields as "metadata.<key>".
    """
    if not lines or lines[0].strip() != "---":
        return {}, 0, "SKILL.md does not open with a --- frontmatter line"
    fields: dict[str, str] = {}
    key = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return fields, i + 1, None
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[:1].isspace() and key == "metadata":
            k, sep, v = line.strip().partition(":")
            if sep:
                fields[f"metadata.{k.strip()}"] = v.strip().strip("'\"")
            continue
        if line[:1].isspace() and key:
            fields[key] = (fields[key] + " " + line.strip()).strip()
            continue
        k, sep, v = line.partition(":")
        if not sep:
            return fields, 0, f"frontmatter line {i + 1} is not key: value"
        key = k.strip()
        v = v.strip()
        fields[key] = "" if v in (">", ">-", "|", "|-") else v.strip("'\"")
    return fields, 0, "frontmatter is never closed by a --- line"


def slug(text: str) -> str:
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[`*_]", "", text).strip().lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


# --- checks -----------------------------------------------------------------


def check_frontmatter(rep: SkillReport, skill_md: Path, lines: list[str], folder: str) -> int:
    fields, body_start, err = split_frontmatter(lines)
    rep.facts["frontmatter_keys"] = sorted(fields)
    if err:
        rep.add("A1", "fix", skill_md, 1, err)
        return body_start
    name, desc = fields.get("name", ""), fields.get("description", "")
    if not name:
        rep.add("A1", "fix", skill_md, 1, "frontmatter has no name")
    else:
        if len(name) > MAX_NAME:
            rep.add("A1", "fix", skill_md, 2, f"name is {len(name)} chars (max {MAX_NAME})")
        if not NAME_RE.match(name):
            rep.add("A1", "fix", skill_md, 2, f"name {name!r} must be lowercase letters, digits, single hyphens")
        if any(w in name for w in RESERVED_NAME_WORDS):
            rep.add("A1", "fix", skill_md, 2, f"name {name!r} contains a reserved word (anthropic/claude)")
        if name != folder:
            rep.add("A1", "fix", skill_md, 2, f"name {name!r} does not match its folder {folder!r}")
    if not desc:
        rep.add("A1", "fix", skill_md, 1, "frontmatter has no description")
        return body_start
    rep.facts["description_chars"] = len(desc)
    if len(desc) > MAX_DESCRIPTION:
        rep.add("A2", "fix", skill_md, 1, f"description is {len(desc)} chars (max {MAX_DESCRIPTION}); the tail is cut")
    if re.search(r"<[^>]+>", desc):
        rep.add("A2", "fix", skill_md, 1, "description contains angle-bracket tags")
    if re.match(r"^(i|i'm|i can|you|you can|we)\b", desc.strip(), re.IGNORECASE):
        rep.add("A3", "fix", skill_md, 1, "description is not in third person (starts with I/you/we)")
    if not re.search(r"\b(use (it |this )?(when|for|whenever)|triggers? on|fires (on|when)|when (the user|someone|a user|you))", desc, re.IGNORECASE):
        rep.add("A3", "check", skill_md, 1, "description has no explicit when-to-use clause ('Use when…')")
    top = {k for k in fields if not k.startswith("metadata.")}
    unknown = sorted(top - SPEC_KEYS - CLAUDE_CODE_KEYS)
    rep.facts["claude_code_only_keys"] = sorted(top & CLAUDE_CODE_KEYS)
    for k in unknown:
        rep.add("A4", "check", skill_md, frontmatter_line(lines, k),
                f"frontmatter key {k!r} is outside the spec: ignored by Claude Code and Codex, rejected by "
                "claude.ai upload, the Skills API and OpenAI's validator; move it under metadata as a string")
    if "model" in top:
        rep.add("A4", "check", skill_md, frontmatter_line(lines, "model"),
                "`model:` switches the model in Claude Code; if it only documents the target, use metadata target-models")
    declared = next((fields[f"metadata.{k}"] for k in TARGET_MODEL_KEYS if f"metadata.{k}" in fields), "")
    rep.facts["target_models"] = declared
    if not declared:
        rep.add("G1", "check", skill_md, 1, "no metadata target-models naming the model(s) this skill is written for")
    return body_start


def frontmatter_line(lines: list[str], key: str) -> int:
    for i, line in enumerate(lines[1:], start=2):
        if line.strip() == "---":
            break
        if line.startswith(f"{key}:"):
            return i
    return 1


def check_size(rep: SkillReport, skill_md: Path, lines: list[str]) -> None:
    rep.facts["skill_md_lines"] = len(lines)
    if len(lines) >= MAX_SKILL_LINES:
        rep.add("C1", "fix", skill_md, MAX_SKILL_LINES, f"SKILL.md is {len(lines)} lines (keep under {MAX_SKILL_LINES}; split into references)")


SKILL_RELATIVE = ("references/", "scripts/", "assets/", "examples/", "templates/", "./")


def local_links(path: Path, lines: list[str]) -> list[tuple[int, str, bool]]:
    """Relative file targets a markdown file points at: (line, target, is_claim).

    is_claim marks a target that unambiguously claims to live in this skill: a
    markdown link, or a backticked path under a skill-relative folder. A bare
    backticked `CLAUDE.md` may name a file anywhere, so it counts toward "is this
    reference linked" but is never reported as broken.
    """
    out = []
    for n, line in prose_lines(lines):
        for m in LINK_RE.finditer(line):
            target = m.group(1).split("#", 1)[0]
            if target and not re.match(r"^[a-z]+:", target) and not target.startswith("/"):
                out.append((n, target, True))
        for m in BACKTICK_PATH_RE.finditer(line):
            out.append((n, m.group(1), m.group(1).startswith(SKILL_RELATIVE)))
    return out


def resolve_target(skill_dir: Path, from_file: Path, target: str) -> Path | None:
    for base in (from_file.parent, skill_dir):
        cand = (base / target).resolve()
        if cand.exists():
            return cand
    return None


def check_references(rep: SkillReport, skill_dir: Path, skill_md: Path, lines: list[str]) -> None:
    linked_from_skill: set[Path] = set()
    for n, target, is_claim in local_links(skill_md, lines):
        hit = resolve_target(skill_dir, skill_md, target)
        if hit is None:
            if is_claim and "<" not in target and "*" not in target:
                rep.add("C6", "check", skill_md, n, f"link target {target!r} not found from the skill folder")
            continue
        linked_from_skill.add(hit)

    md_files = [p for p in sorted(skill_dir.rglob("*.md"))
                if p.name not in NON_REFERENCE_FILES and not (set(p.relative_to(skill_dir).parts[:-1]) & SKIP_DIRS)]
    rep.facts["reference_files"] = [p.relative_to(skill_dir).as_posix() for p in md_files]
    for ref in md_files:
        resolved = ref.resolve()
        rel = ref.relative_to(skill_dir).as_posix()
        ref_lines = read_lines(ref)
        if resolved not in linked_from_skill:
            linked_from_other = any(
                resolve_target(skill_dir, other, t) == resolved
                for other in md_files if other != ref
                for _, t, _ in local_links(other, read_lines(other))
            )
            if linked_from_other:
                rep.add("C2", "fix", ref, 1, f"{rel} is reachable only through another reference file (nested); link it directly from SKILL.md")
            else:
                rep.add("C3", "check", ref, 1, f"{rel} is never linked from SKILL.md; Claude will not know it exists")
        check_toc(rep, ref, ref_lines)


def check_toc(rep: SkillReport, ref: Path, lines: list[str]) -> None:
    if len(lines) <= TOC_THRESHOLD:
        return
    prose = prose_lines(lines)
    headings = [(n, slug(m.group(2))) for n, l in prose if (m := HEADING_RE.match(l)) and len(m.group(1)) >= 2]
    toc_at = None
    for idx, (n, l) in enumerate(prose[:40]):
        if CONTENTS_RE.match(l.strip()):
            toc_at = idx
            break
    rel = ref.name
    if toc_at is None:
        rep.add("C4", "fix", ref, 1, f"{rel} is {len(lines)} lines with no Contents list at the top")
        return
    items = []
    for n, l in prose[toc_at + 1:toc_at + 60]:
        m = re.match(r"^\s*(?:[-*+]|\d+\.)\s+(.*)$", l)
        if m:
            items.append(slug(m.group(1)))
        elif l.strip() and items:
            break
    heading_slugs = {h for _, h in headings if h not in ("contents", "table of contents", "toc")}
    missing = [h for h in heading_slugs
               if not any(h == i or i.startswith(h + " ") or h.startswith(i + " ") for i in items)]
    if missing:
        rep.add("C4", "check", ref, prose[toc_at][0],
                f"Contents list does not cover {len(missing)} heading(s): " + ", ".join(sorted(missing)[:5]))


def check_language(rep: SkillReport, skill_dir: Path) -> None:
    files = [skill_dir / "SKILL.md"] + [p for p in sorted(skill_dir.rglob("*.md"))
                                         if p.name not in NON_REFERENCE_FILES
                                         and not (set(p.relative_to(skill_dir).parts[:-1]) & SKIP_DIRS)]
    total = 0
    for f in files:
        hits = []
        for n, line in prose_lines(read_lines(f)):
            text = strip_inline_code(line)
            for m in SHOUTY_RE.finditer(text):
                hits.append((n, m.group(1)))
            if m := BACKSLASH_PATH_RE.search(text):
                rep.add("C5", "fix", f, n, f"Windows-style path {m.group(0)!r}; use forward slashes")
            if m := TIME_BOMB_RE.search(text):
                rep.add("B3", "check", f, n, f"date-conditional instruction {m.group(0)!r} will go stale")
        total += len(hits)
        if len(hits) >= SHOUTY_LIMIT:
            sample = ", ".join(f"L{n} {w}" for n, w in hits[:6])
            rep.add("G2", "check", f, hits[0][0], f"{len(hits)} all-caps emphatic words ({sample}); current models over-apply these")
    rep.facts["shouty_words"] = total


def check_gotchas(rep: SkillReport, skill_md: Path, lines: list[str]) -> None:
    if not any(re.match(r"^#{2,3}\s+(gotchas|common pitfalls|pitfalls)\b", l, re.IGNORECASE) for _, l in prose_lines(lines)):
        rep.add("J1", "fix", skill_md, len(lines), "no ## Gotchas section")


def check_scripts(rep: SkillReport, skill_dir: Path, skill_text: str) -> None:
    scripts = [p for p in sorted(skill_dir.rglob("*"))
               if p.is_file() and p.suffix in (".py", ".js", ".mjs", ".ts", ".sh")
               and not (set(p.relative_to(skill_dir).parts[:-1]) & SKIP_DIRS)]
    rep.facts["scripts"] = [p.relative_to(skill_dir).as_posix() for p in scripts]
    stdlib = set(sys.stdlib_module_names)
    has_install = bool(INSTALL_RE.search(skill_text))
    for s in scripts:
        rel = s.relative_to(skill_dir).as_posix()
        if s.name not in skill_text and rel not in skill_text:
            rep.add("H2", "check", s, 1, f"{rel} is never mentioned in SKILL.md (say when to run it, and whether to run or read it)")
        try:
            text = s.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        third_party: set[str] = set()
        if s.suffix == ".py":
            local = {p.stem for p in s.parent.glob("*.py")}
            for m in PY_IMPORT_RE.finditer(text):
                mod = (m.group(1) or m.group(2) or "").split(".")[0]
                if mod and mod not in stdlib and mod not in local and mod != "__future__":
                    third_party.add(mod)
        elif s.suffix in (".js", ".mjs", ".ts"):
            for m in JS_IMPORT_RE.finditer(text):
                mod = (m.group(1) or m.group(2) or "").replace("node:", "").split("/")[0]
                if mod and mod not in NODE_BUILTINS:
                    third_party.add(mod)
        if third_party and not has_install:
            rep.add("H1", "fix", s, 1,
                    f"{rel} imports {', '.join(sorted(third_party))} but SKILL.md has no install line next to its use")


def check_evals(rep: SkillReport, skill_dir: Path) -> None:
    has = any((skill_dir / d).exists() for d in ("cases", "evals", "evals.json", "tests"))
    rep.facts["has_cases_or_evals"] = has
    if not has:
        rep.add("K1", "check", skill_dir / "SKILL.md", 1, "no cases/ or evals/ — nothing to replay to prove a change kept the skill working")


def lint(skill_dir: Path) -> SkillReport:
    skill_md = skill_dir / "SKILL.md"
    rep = SkillReport(skill=skill_dir.name, path=str(skill_dir))
    lines = read_lines(skill_md)
    check_frontmatter(rep, skill_md, lines, skill_dir.name)
    check_size(rep, skill_md, lines)
    check_references(rep, skill_dir, skill_md, lines)
    check_language(rep, skill_dir)
    check_gotchas(rep, skill_md, lines)
    check_scripts(rep, skill_dir, "\n".join(lines))
    check_evals(rep, skill_dir)
    rep.findings.sort(key=lambda f: (f.level != "fix", f.rule, f.file, f.line))
    return rep


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("paths", nargs="*", default=["."])
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args(argv)
    try:
        skills = discover(args.paths)
        reports = [lint(s) for s in skills]
    except (OSError, UnicodeError) as exc:
        print(f"lint_skills: scan failed: {exc}", file=sys.stderr)
        return 1
    if args.as_json:
        print(json.dumps([{**asdict(r), "findings": [asdict(f) for f in r.findings]} for r in reports], indent=2))
        return 0
    if not reports:
        print("lint_skills: no skills found (looked for folders containing SKILL.md)")
        return 0
    for r in reports:
        fixes = sum(f.level == "fix" for f in r.findings)
        checks = len(r.findings) - fixes
        print(f"\n== {r.skill}  ({r.facts.get('skill_md_lines')} lines, {fixes} fix, {checks} check)  {r.path}")
        for f in r.findings:
            print(f"  {f.level:5} {f.rule:3} {f.file}:{f.line}  {f.message}")
    total = sum(len(r.findings) for r in reports)
    print(f"\n{len(reports)} skill(s) scanned, {total} finding(s). Findings are evidence for the rubric, not verdicts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
