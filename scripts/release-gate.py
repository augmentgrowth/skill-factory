#!/usr/bin/env python3
"""release-gate — fail-closed checks that run before every push from this repo.

Stdlib only, on purpose: same constraint as the client-template `bin/skills`.

Origin is what `plugin marketplace add` fetches, so a push here is a release to
everyone who installed the factory. There is no human diff review anywhere in
the loop — the builder reviews skill *output*, not code — so this gate is the
only thing standing between a defect and every installer. Every check fails
closed: an error the gate cannot evaluate is a failure, never a pass.

Checks:

    versions     plugin.json's version is the release unit; both marketplace.json
                 version fields must equal it.
    range        every path in the outgoing commit range is release-authorized.
    surface      the plugin surface is well-formed in a clean checkout of HEAD
                 (manifests parse, the skills link resolves, every skill has a
                 SKILL.md carrying name + description, no broken links).
    new-skills   a skill added in the outgoing range must be classified
                 public-safe before it can ship.

Usage:

    release-gate.py                      run every check against origin/<branch>
    release-gate.py --json               machine-readable result
    release-gate.py --check versions     run one check
    release-gate.py --base origin/main   compare against an explicit ref
    release-gate.py --allow-new-skill X  classify skill X public-safe for this run

Exit status is 0 only when every selected check passes.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# The repo under inspection. Defaults to this script's own repo; the env var
# exists so the test suite can point the real script at a throwaway fixture
# instead of the working checkout.
REPO_ROOT = Path(os.environ.get("RELEASE_GATE_ROOT") or Path(__file__).resolve().parent.parent)
PLUGIN_JSON = Path(".claude-plugin/plugin.json")
MARKETPLACE_JSON = Path(".claude-plugin/marketplace.json")

# Paths this repo is allowed to publish. A push carrying anything else is not a
# release we authorized -- it is someone's stray work riding along. Path-scoped
# staging governs one commit; it does not govern what a push sends.
AUTHORIZED_PREFIXES = (
    ".claude-plugin/",
    ".claude/skills/",
    "demos/",
    "docs/",
    "scripts/",
    "skills",
    "templates/",
    "tests/",
)
AUTHORIZED_FILES = (
    ".gitignore",
    "AGENTS.md",
    "CLAUDE.md",
    "LICENSE",
    "README.md",
)

SKILLS_DIR = Path(".claude/skills")


class CheckFailure(Exception):
    """A check reached a definite negative verdict."""


def git(*args: str, cwd: Path | None = None) -> str:
    proc = subprocess.run(
        ("git", "-C", str(cwd or REPO_ROOT), *args),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise CheckFailure(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


def read_json(path: Path, root: Path | None = None) -> dict:
    full = (root or REPO_ROOT) / path
    try:
        return json.loads(full.read_text())
    except FileNotFoundError:
        raise CheckFailure(f"{path} is missing")
    except json.JSONDecodeError as exc:
        raise CheckFailure(f"{path} is not valid JSON: {exc}")


def parse_frontmatter(text: str) -> dict[str, str]:
    """Minimal YAML-frontmatter reader: flat `key: value` pairs only.

    Deliberately not a YAML parser. The gate needs `name`, `description`, and
    `public_safe`; anything structured is out of scope and a full parser would
    be a dependency this repo does not carry.
    """
    if not text.startswith("---"):
        return {}
    _, _, rest = text.partition("---")
    body, sep, _ = rest.partition("\n---")
    if not sep:
        return {}
    fields: dict[str, str] = {}
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or line[:1].isspace():
            continue
        key, sep, value = stripped.partition(":")
        if sep:
            fields[key.strip()] = value.strip().strip("'\"")
    return fields


def resolve_base(explicit: str | None) -> str:
    """The ref the outgoing range is measured against."""
    if explicit:
        return explicit
    branch = git("branch", "--show-current").strip()
    if not branch:
        raise CheckFailure("detached HEAD -- pass --base explicitly")
    remote = f"origin/{branch}"
    try:
        git("rev-parse", "--verify", "--quiet", remote)
    except CheckFailure:
        # An unpushed branch has no upstream yet; the whole branch is outgoing.
        return "origin/HEAD"
    return remote


def outgoing_paths(base: str) -> list[str]:
    diff = git("diff", "--name-only", f"{base}...HEAD")
    return [line for line in diff.splitlines() if line.strip()]


# --- checks -----------------------------------------------------------------


def check_versions() -> str:
    """plugin.json's version is the single source of truth (KTD: release unit)."""
    plugin = read_json(PLUGIN_JSON)
    market = read_json(MARKETPLACE_JSON)

    canonical = plugin.get("version")
    if not canonical:
        raise CheckFailure("plugin.json has no version field")

    found = {"plugin.json:version": canonical}
    metadata = market.get("metadata") or {}
    found["marketplace.json:metadata.version"] = metadata.get("version")

    plugins = market.get("plugins") or []
    if not plugins:
        raise CheckFailure("marketplace.json lists no plugins")
    found["marketplace.json:plugins[0].version"] = plugins[0].get("version")

    mismatched = {k: v for k, v in found.items() if v != canonical}
    if mismatched:
        detail = ", ".join(f"{k}={v!r}" for k, v in sorted(mismatched.items()))
        raise CheckFailure(
            f"version drift -- plugin.json declares {canonical!r} but {detail}"
        )
    return f"all three version fields agree at {canonical}"


def check_range(base: str) -> str:
    paths = outgoing_paths(base)
    if not paths:
        return "nothing outgoing"

    unauthorized = [
        p
        for p in paths
        if not p.startswith(AUTHORIZED_PREFIXES) and p not in AUTHORIZED_FILES
    ]
    if unauthorized:
        raise CheckFailure(
            "outgoing range touches unauthorized paths: " + ", ".join(sorted(unauthorized))
        )
    return f"{len(paths)} outgoing path(s), all release-authorized"


def check_surface() -> str:
    """Verify the published plugin surface in a clean checkout of HEAD.

    A clean checkout is the point: the working tree can carry ignored or
    untracked files that make a broken surface look intact. This inspects only
    what a `plugin marketplace add` would actually fetch.
    """
    with tempfile.TemporaryDirectory(prefix="release-gate-") as tmp:
        clean = Path(tmp) / "checkout"
        subprocess.run(
            ("git", "clone", "--quiet", "--no-hardlinks", str(REPO_ROOT), str(clean)),
            capture_output=True,
            text=True,
            check=True,
        )

        plugin = read_json(PLUGIN_JSON, root=clean)
        read_json(MARKETPLACE_JSON, root=clean)

        declared = (plugin.get("skills") or "./skills/").lstrip("./").rstrip("/")
        skills_path = clean / declared
        if not skills_path.is_dir():
            raise CheckFailure(
                f"plugin.json points skills at {declared!r}, which is not a "
                "directory in a clean checkout"
            )

        skill_dirs = sorted(d for d in skills_path.iterdir() if d.is_dir())
        if not skill_dirs:
            raise CheckFailure(f"{declared!r} contains no skills in a clean checkout")

        for skill in skill_dirs:
            manifest = skill / "SKILL.md"
            if not manifest.is_file():
                raise CheckFailure(f"{skill.name} has no SKILL.md")
            fields = parse_frontmatter(manifest.read_text())
            for required in ("name", "description"):
                if not fields.get(required):
                    raise CheckFailure(
                        f"{skill.name}/SKILL.md frontmatter is missing {required!r}"
                    )

        broken = [
            str(p.relative_to(clean))
            for p in clean.rglob("*")
            if p.is_symlink() and not p.exists()
        ]
        if broken:
            raise CheckFailure("broken symlinks in a clean checkout: " + ", ".join(broken))

    return f"{len(skill_dirs)} skill(s) well-formed in a clean checkout"


def check_new_skills(base: str, allowed: set[str]) -> str:
    """A skill first appearing in this range must be classified public-safe.

    Skills are born under .claude/skills/, which IS the published surface via
    the `skills` link -- including frozen sample inputs under cases/. Classify
    deliberately or keep it in the private hub.
    """
    added = git("diff", "--name-only", "--diff-filter=A", f"{base}...HEAD")
    names: set[str] = set()
    for line in added.splitlines():
        if not line.strip():
            continue
        try:
            rel = Path(line.strip()).relative_to(SKILLS_DIR)
        except ValueError:
            continue
        # A skill is born when its SKILL.md appears. Keying on any added path
        # would flag an existing skill as new the moment it gains a case file
        # or a CHANGELOG line.
        if len(rel.parts) == 2 and rel.parts[1] == "SKILL.md":
            names.add(rel.parts[0])

    if not names:
        return "no new skills in range"

    unclassified = []
    for name in sorted(names):
        if name in allowed:
            continue
        manifest = REPO_ROOT / SKILLS_DIR / name / "SKILL.md"
        fields = parse_frontmatter(manifest.read_text()) if manifest.is_file() else {}
        if fields.get("public_safe", "").lower() != "true":
            unclassified.append(name)

    if unclassified:
        raise CheckFailure(
            "new skill(s) not classified public-safe: "
            + ", ".join(unclassified)
            + " -- add `public_safe: true` to the skill's frontmatter, pass "
            "--allow-new-skill, or keep the skill in the private hub"
        )
    return f"{len(names)} new skill(s) classified public-safe"


CHECKS = ("versions", "range", "surface", "new-skills")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", choices=CHECKS, action="append", dest="checks")
    parser.add_argument("--base", help="ref the outgoing range is measured against")
    parser.add_argument(
        "--allow-new-skill",
        action="append",
        default=[],
        dest="allow_new_skill",
        metavar="NAME",
        help="classify a newly added skill public-safe for this run",
    )
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)

    selected = args.checks or list(CHECKS)
    allowed = set(args.allow_new_skill)
    results: list[dict[str, str]] = []
    failed = False

    needs_base = any(c in ("range", "new-skills") for c in selected)
    base = None
    if needs_base:
        try:
            base = resolve_base(args.base)
        except CheckFailure as exc:
            results.append({"check": "base", "status": "fail", "detail": str(exc)})
            failed = True
            selected = [c for c in selected if c not in ("range", "new-skills")]

    runners = {
        "versions": check_versions,
        "range": lambda: check_range(base),
        "surface": check_surface,
        "new-skills": lambda: check_new_skills(base, allowed),
    }

    for name in selected:
        try:
            detail = runners[name]()
            results.append({"check": name, "status": "pass", "detail": detail})
        except CheckFailure as exc:
            results.append({"check": name, "status": "fail", "detail": str(exc)})
            failed = True
        except Exception as exc:  # fail closed: an unevaluable check is a failure
            results.append(
                {"check": name, "status": "fail", "detail": f"could not evaluate: {exc}"}
            )
            failed = True

    if args.as_json:
        print(json.dumps({"ok": not failed, "base": base, "checks": results}, indent=2))
    else:
        for entry in results:
            mark = "ok  " if entry["status"] == "pass" else "FAIL"
            print(f"{mark} {entry['check']}: {entry['detail']}")
        print("\nrelease gate: " + ("PASS" if not failed else "BLOCKED"))

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
