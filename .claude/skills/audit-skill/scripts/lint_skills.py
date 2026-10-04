#!/usr/bin/env python3
"""lint_skills — the mechanical half of a skill audit.

Stdlib only (Python 3.9+), so it runs in any repo with no install step:

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
PIPE_TO_SHELL_RE = re.compile(
    r"\b(curl|wget)\b(?:(?!\b(?:curl|wget)\b)[^|`;\n])*\|\s*(sudo\s+)?((ba|z)?sh|python3?|node|perl|ruby)\b"
    r"|\b((ba|z)?sh|source)\s+<\(\s*(curl|wget)\b")
TIME_BOMB_RE = re.compile(
    r"\b(before|after|until|as of)\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+20\d\d\b",
    re.IGNORECASE,
)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
CONTENTS_RE = re.compile(r"^(#{1,6}\s*)?(\*\*)?(table of contents|contents|toc)(\*\*)?:?\s*$", re.IGNORECASE)
INSTALL_RE = re.compile(r"\b(pip3?|uv pip|uv add|poetry add|pipx|npm|pnpm|yarn|bun|brew|apt(-get)?)\s+(install|add|i)\b|requirements\.txt|package\.json|pyproject\.toml")
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
# Keys this factory (and its skill-home template) reads at top level. Kept there on purpose:
# `bin/skills vendor update` rewrites them in place. Reported as facts, with the upload caveat.
FACTORY_KEYS = {"static", "tier", "upstream", "public_safe"}
# sys.stdlib_module_names arrived in 3.10; macOS still ships 3.9. A fallback list that is
# merely incomplete only costs a spurious H1 finding, never a crash.
STDLIB = set(getattr(sys, "stdlib_module_names", ())) or {
    "abc", "argparse", "array", "ast", "asyncio", "base64", "bisect", "calendar", "collections",
    "concurrent", "contextlib", "copy", "csv", "ctypes", "dataclasses", "datetime", "decimal",
    "difflib", "email", "enum", "errno", "fnmatch", "fractions", "functools", "gc", "getpass",
    "glob", "gzip", "hashlib", "heapq", "hmac", "html", "http", "importlib", "inspect", "io",
    "ipaddress", "itertools", "json", "logging", "math", "mimetypes", "multiprocessing", "operator",
    "os", "pathlib", "pickle", "platform", "pprint", "queue", "random", "re", "secrets", "select",
    "shlex", "shutil", "signal", "socket", "sqlite3", "ssl", "stat", "statistics", "string",
    "struct", "subprocess", "sys", "tarfile", "tempfile", "textwrap", "threading", "time",
    "timeit", "tomllib", "traceback", "types", "typing", "unicodedata", "unittest", "urllib",
    "uuid", "warnings", "weakref", "xml", "zipfile", "zlib", "zoneinfo"}
MAX_DISCOVERY_DEPTH = 6
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
        if p.name in ("", ".", ".."):
            p = p.resolve()
        if not p.exists():
            raise SystemExit(f"lint_skills: no such path: {raw}")
        if (p / "SKILL.md").is_file():
            found.append(p)
            continue
        roots = [p / ".claude" / "skills", p / ".agents" / "skills", p / "skills"]
        roots = [r for r in roots if r.is_dir()] or [p]
        before = len(found)
        for root in roots:
            for child in sorted(root.iterdir()):
                if child.is_dir() and (child / "SKILL.md").is_file():
                    found.append(child)
        if len(found) == before:
            found.extend(walk_for_skills(p))
        else:
            known = {f.resolve() for f in found}
            extra = [w for w in walk_for_skills(p) if w.resolve() not in known]
            if extra:
                print(f"lint_skills: {len(extra)} other SKILL.md folder(s) under {raw} were not scanned "
                      "(outside .claude/skills, .agents/skills, skills); pass them explicitly to include: "
                      + ", ".join(str(e) for e in extra[:5]), file=sys.stderr)
    seen, unique = set(), []
    for f in found:
        key = f.resolve()
        if key not in seen:
            seen.add(key)
            unique.append(f)
    return unique


def walk_for_skills(root: Path) -> list[Path]:
    """Bounded search for nested layouts (plugins/*/skills/*, category folders)."""
    hits: list[Path] = []
    stack = [(root, 0)]
    while stack:
        here, depth = stack.pop()
        try:
            children = sorted(here.iterdir())
        except OSError:
            continue
        for child in children:
            if not child.is_dir() or child.name in SKIP_DIRS:
                continue
            if child.name.startswith(".") and child.name not in (".claude", ".agents"):
                continue
            if (child / "SKILL.md").is_file():
                hits.append(child)
            elif depth + 1 < MAX_DISCOVERY_DEPTH:
                stack.append((child, depth + 1))
    return sorted(hits)


def repo_root(path: Path) -> Path | None:
    for cand in [path.resolve(), *path.resolve().parents]:
        if (cand / ".git").exists():
            return cand
    return None


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


YAML_INDICATORS = tuple("[]{}&*!|>%@`")


def yaml_hazards(fields: dict[str, str], plain: dict[str, int]) -> list[tuple[int, str]]:
    """Plain (unquoted, non-block) values that a real YAML parser rejects or misreads.

    This reader is lenient on purpose, but Claude Code is not: a frontmatter block that
    fails to parse loads with every field silently dropped, so the skill keeps its name
    and loses its description -- it stops triggering. `Triggers on: x` inside a plain
    value is the classic cause.
    """
    out = []
    for key, line in plain.items():
        text = fields.get(key, "")
        if re.search(r":(\s|$)", text):
            out.append((line, f"{key}: unquoted value contains ': ' — YAML rejects the whole frontmatter "
                              "and the skill loads with no description; use a `>-` block or quote it"))
        elif text.startswith(YAML_INDICATORS):
            out.append((line, f"{key}: unquoted value starts with {text[0]!r}, which YAML reads as syntax; "
                              "use a `>-` block or quote it"))
        elif re.search(r"\s#", text):
            out.append((line, f"{key}: ' #' starts a YAML comment, so the rest of the value is cut; "
                              "use a `>-` block or quote it"))
    return out


def split_frontmatter(lines: list[str], plain: dict[str, int] | None = None
                      ) -> tuple[dict[str, str], int, str | None]:
    """Flat key: value reader, plus one nested level under `metadata:`.

    Returns (fields, body_start_index, error). Folded/indented continuation lines are
    joined onto their key; `metadata` sub-keys land in fields as "metadata.<key>".
    If `plain` is given, it is filled with {key: line} for unquoted, non-block values.
    """
    if not lines or lines[0].strip() != "---":
        return {}, 0, "SKILL.md does not open with a --- frontmatter line"
    fields: dict[str, str] = {}
    plain = {} if plain is None else plain
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
        if v and v not in (">", ">-", "|", "|-", ">+", "|+") and v[0] not in "'\"":
            plain[key] = i + 1
        fields[key] = "" if v in (">", ">-", "|", "|-", ">+", "|+") else v.strip("'\"")
    return fields, 0, "frontmatter is never closed by a --- line"


def slug(text: str) -> str:
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[`*_]", "", text).strip().lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


# --- checks -----------------------------------------------------------------


def check_frontmatter(rep: SkillReport, skill_md: Path, lines: list[str], folder: str) -> int:
    plain: dict[str, int] = {}
    fields, body_start, err = split_frontmatter(lines, plain)
    rep.facts["frontmatter_keys"] = sorted(fields)
    if err:
        rep.add("A1", "fix", skill_md, 1, err)
        return body_start
    for line, message in yaml_hazards(fields, plain):
        rep.add("A1", "fix", skill_md, line, message)
    name, desc = fields.get("name", ""), fields.get("description", "")
    if not name:
        rep.add("A1", "fix", skill_md, 1, "frontmatter has no name")
    else:
        if len(name) > MAX_NAME:
            rep.add("A1", "fix", skill_md, 2, f"name is {len(name)} chars (max {MAX_NAME})")
        if not NAME_RE.match(name):
            rep.add("A1", "fix", skill_md, 2, f"name {name!r} must be lowercase letters, digits, single hyphens")
        if any(w in name for w in RESERVED_NAME_WORDS):
            rep.add("A1", "check", skill_md, 2, f"name {name!r} contains a reserved word (anthropic/claude); "
                    "claude.ai upload and the Skills API reject it, Claude Code does not")
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
    unknown = sorted(top - SPEC_KEYS - CLAUDE_CODE_KEYS - FACTORY_KEYS)
    rep.facts["claude_code_only_keys"] = sorted(top & CLAUDE_CODE_KEYS)
    rep.facts["factory_keys"] = sorted(top & FACTORY_KEYS)
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
    root = repo_root(skill_dir)
    for n, target, is_claim in local_links(skill_md, lines):
        hit = resolve_target(skill_dir, skill_md, target)
        if hit is None:
            if not is_claim or "<" in target or "*" in target:
                continue
            if root is not None and (root / target).exists():
                rep.add("C6", "check", skill_md, n, f"{target!r} lives outside the skill folder (a repo path); "
                        "it will not travel when the skill is installed elsewhere")
            else:
                rep.add("C6", "check", skill_md, n, f"link target {target!r} not found")
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


def check_untrusted(rep: SkillReport, skill_dir: Path) -> None:
    """D2: downloaded code piped straight into a shell, anywhere in the skill (code blocks included)."""
    for f in sorted(skill_dir.rglob("*")):
        if not f.is_file() or f.suffix not in (".md", ".sh", ".py", ".js", ".mjs", ".ts"):
            continue  # never .env or other extensionless files: they may hold secrets
        if set(f.relative_to(skill_dir).parts[:-1]) & SKIP_DIRS:
            continue
        try:
            lines = read_lines(f)
        except OSError:
            continue
        prose = {n for n, _ in prose_lines(lines)} if f.suffix == ".md" else set()
        for n, line in enumerate(lines, start=1):
            for m in PIPE_TO_SHELL_RE.finditer(line):
                # Negation belongs to this command, not any earlier warning on the line.
                prefix = line[:m.start()]
                suffix = line[m.end():]
                before = re.search(
                    r"\b(?:never|don't|do not|avoid)\s+(?:(?:run|running|execute|executing|"
                    r"use|using|pipe|piping)\s+)?[`\s]*$", prefix, re.IGNORECASE)
                after = re.match(
                    r"[`\s]*(?:—|–|--|:)\s*(?:never|don't|do not)\s+"
                    r"(?:do|run|execute|use)\s+(?:this|that|it)\s*[.!]?\s*$",
                    suffix, re.IGNORECASE)
                level = "check" if n in prose and (before or after) else "fix"
                message = (f"{m.group(0)!r} appears in a warning; verify the surrounding guidance"
                           if level == "check" else
                           f"{m.group(0)!r} runs downloaded code unseen; download, "
                           "check, then run — or vendor the script into the skill")
                rep.add("D2", level, f, n, message)


def check_gotchas(rep: SkillReport, skill_md: Path, lines: list[str]) -> None:
    if not any(re.match(r"^#{2,3}\s+(gotchas|common pitfalls|pitfalls)\b", l, re.IGNORECASE) for _, l in prose_lines(lines)):
        rep.add("J1", "check", skill_md, len(lines), "no ## Gotchas section")


DOCSTRING_RE = re.compile(r'("""|\'\'\')(?:.|\n)*?\1')
PEP723_RE = re.compile(r"^# /// script\s*$", re.MULTILINE)
TOP_IMPORT_RE = re.compile(r"(?:import\s+([\w.]+(?:\s*,\s*[\w.]+)*)|from\s+([\w.]+)\s+import)\b")


def required_imports(text: str, suffix: str, local: set[str]) -> set[str]:
    """Third-party modules a script cannot run without.

    Only top-level imports count: an indented import sits in a try/except or a
    function and is optional by construction. Docstrings are stripped first so
    prose that mentions importing never reads as code.
    """
    mods: set[str] = set()
    if suffix == ".py":
        for line in DOCSTRING_RE.sub("", text).splitlines():
            m = TOP_IMPORT_RE.match(line)
            if not m:
                continue
            names = m.group(1).split(",") if m.group(1) else [m.group(2)]
            for name in names:
                mod = name.strip().split(".")[0]
                if mod and mod not in STDLIB and mod not in local and mod != "__future__":
                    mods.add(mod)
    elif suffix in (".js", ".mjs", ".ts"):
        for m in JS_IMPORT_RE.finditer(text):
            mod = (m.group(1) or m.group(2) or "").replace("node:", "")
            mod = "/".join(mod.split("/")[:2]) if mod.startswith("@") else mod.split("/")[0]
            if mod and mod not in NODE_BUILTINS:
                mods.add(mod)
    return mods


def check_scripts(rep: SkillReport, skill_dir: Path, skill_text: str) -> None:
    scripts = [p for p in sorted(skill_dir.rglob("*"))
               if p.is_file() and p.suffix in (".py", ".js", ".mjs", ".ts", ".sh")
               and not (set(p.relative_to(skill_dir).parts[:-1]) & SKIP_DIRS)]
    rep.facts["scripts"] = [p.relative_to(skill_dir).as_posix() for p in scripts]
    manifests = " ".join(
        p.read_text(encoding="utf-8", errors="replace")
        for p in skill_dir.rglob("*")
        if p.name in ("requirements.txt", "pyproject.toml", "package.json") and p.is_file()
    )
    skill_has_install = bool(INSTALL_RE.search(skill_text))
    for s in scripts:
        rel = s.relative_to(skill_dir).as_posix()
        if s.name not in skill_text and rel not in skill_text:
            rep.add("H2", "check", s, 1, f"{rel} is never mentioned in SKILL.md (say when to run it, and whether to run or read it)")
        try:
            text = s.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if PEP723_RE.search(text):
            continue  # inline script metadata declares its own dependencies
        local = {p.stem for p in s.parent.glob("*.py")}
        header = "\n".join(text.splitlines()[:30])
        undeclared, unnamed = [], []
        for mod in sorted(required_imports(text, s.suffix, local)):
            word = re.compile(r"(?<![\w-])" + re.escape(mod) + r"(?![\w-])", re.IGNORECASE)
            if word.search(manifests) or (INSTALL_RE.search(header) and word.search(header)):
                continue
            if skill_has_install and word.search(skill_text):
                continue
            (unnamed if skill_has_install else undeclared).append(mod)
        if undeclared:
            rep.add("H1", "fix", s, 1, f"{rel} needs {', '.join(undeclared)} but nothing says how to install it")
        if unnamed:
            rep.add("H1", "check", s, 1, f"{rel} needs {', '.join(unnamed)}; SKILL.md has an install line "
                    "but it does not name this package")


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
    check_untrusted(rep, skill_dir)
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
    except Exception as exc:  # a crash must read as "scan failed", never as "no findings"
        print(f"lint_skills: scan failed: {type(exc).__name__}: {exc}", file=sys.stderr)
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
