#!/usr/bin/env python3
"""release-gate — fail-closed checks that authorize a push from this repo.

Stdlib only, on purpose: same constraint as the client-template `bin/skills`.

Origin is what `plugin marketplace add` fetches, so a push here is a release to
everyone who installed the factory. The builder reviews skill *output*, never
diffs, so no human reads this code before it ships. This gate is the only thing
between a defect and every installer, and it fails closed: a check it cannot
evaluate is a failure, never a pass.

TWO MODES, and the distinction is load-bearing:

    release      authorizes a push. Runs every check, against one immutable
                 commit, with the base derived from the actual push refspec.
                 Accepts no flag that could weaken a check.
    diagnostic   tells you what would happen. Accepts --check, --base, and
                 --allow-new-skill. Prints that it authorizes nothing, and
                 exits 2 on success so no caller can mistake it for a pass.

Everything is read from the commit being pushed, never the working tree. A
working-tree read would let an uncommitted repair mask a defect in the commit
that actually ships.

Checks:

    versions     plugin.json's version is the release unit; both marketplace.json
                 version fields must equal it.
    range        every path touched by every outgoing commit is authorized --
                 not just the net difference between endpoints, because a file
                 added then deleted inside the range still ships in history.
    surface      the plugin surface is well-formed and portable: manifests
                 parse, `skills` is a relative link to .claude/skills, every
                 skill carries strict frontmatter with name + description.
    new-skills   a skill name present at HEAD but absent at the base must carry
                 a committed `public_safe: true`. Compares name sets, so a
                 rename into a new public name cannot evade it.

Usage:

    release-gate.py --release --remote-sha <sha> [--local-sha <sha>]
    release-gate.py                              # diagnostic, all checks
    release-gate.py --check versions --base X    # diagnostic, one check
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(os.environ.get("RELEASE_GATE_ROOT") or Path(__file__).resolve().parent.parent)
PLUGIN_JSON = ".claude-plugin/plugin.json"
MARKETPLACE_JSON = ".claude-plugin/marketplace.json"
SKILLS_DIR = ".claude/skills"
SKILLS_LINK = "skills"
SKILLS_LINK_TARGET = ".claude/skills"

ZERO_SHA = "0" * 40

# Paths this repo may publish. Prefixes end in "/" so a prefix can never match a
# sibling that merely starts with the same letters -- `skills` without the slash
# authorized `skills-private/` and `skillsecrets.env`.
AUTHORIZED_PREFIXES = (
    ".claude-plugin/",
    ".claude/skills/",
    "demos/",
    "docs/",
    "githooks/",
    "scripts/",
    "templates/",
    "tests/",
)
AUTHORIZED_FILES = (
    ".gitignore",
    "AGENTS.md",
    "CLAUDE.md",
    "LICENSE",
    "README.md",
    "skills",  # the distribution symlink itself, exact match only
)


class CheckFailure(Exception):
    """A check reached a definite negative verdict."""


def git(*args: str, cwd: Path | None = None) -> str:
    proc = subprocess.run(
        ("git", "-C", str(cwd or REPO_ROOT), *args), capture_output=True, text=True
    )
    if proc.returncode != 0:
        raise CheckFailure(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


def show(rev: str, path: str) -> str:
    """Read a path out of a commit. Never the working tree."""
    try:
        return git("show", f"{rev}:{path}")
    except CheckFailure:
        raise CheckFailure(f"{path} is missing at {rev}")


def read_json_at(rev: str, path: str) -> dict:
    try:
        return json.loads(show(rev, path))
    except json.JSONDecodeError as exc:
        raise CheckFailure(f"{path} is not valid JSON at {rev}: {exc}")


def parse_frontmatter(text: str) -> dict[str, str]:
    """Strict flat `key: value` frontmatter reader.

    Deliberately not a YAML parser -- but strict about the delimiters, because a
    lax reader passes a skill whose frontmatter the real plugin loader rejects,
    shipping a skill that silently fails to load for installers. Opening and
    closing lines must equal `---` exactly, and a duplicate key is an error.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise CheckFailure("frontmatter must open with a line containing exactly ---")
    fields: dict[str, str] = {}
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return fields
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[:1].isspace():
            continue  # nested value; out of this reader's scope
        key, sep, value = line.partition(":")
        if not sep:
            raise CheckFailure(f"frontmatter line {i} is not `key: value`: {line!r}")
        key = key.strip()
        if key in fields:
            raise CheckFailure(f"duplicate frontmatter key {key!r}")
        fields[key] = value.strip().strip("'\"")
    raise CheckFailure("frontmatter is not closed by a line containing exactly ---")


# --- base resolution --------------------------------------------------------


def resolve_release_base(remote_sha: str) -> str:
    """The commit the remote ref is currently at, per the push refspec.

    Release mode never accepts a caller-chosen base: `--base HEAD` would reduce
    both range-sensitive checks to an empty, trivially-passing set.
    """
    if not remote_sha:
        raise CheckFailure("release mode requires --remote-sha from the push refspec")
    if remote_sha == ZERO_SHA:
        # Creating the remote ref. Everything not already on some remote ref is
        # outgoing; fall back to the empty tree if this is the first push ever.
        try:
            remotes = git("rev-list", "--remotes").split()
        except CheckFailure:
            remotes = []
        if not remotes:
            return git("hash-object", "-t", "tree", "/dev/null").strip()
        return remotes[0]
    git("cat-file", "-e", f"{remote_sha}^{{commit}}")
    return remote_sha


def resolve_diagnostic_base(explicit: str | None) -> str:
    if explicit:
        return git("rev-parse", "--verify", f"{explicit}^{{commit}}").strip()
    branch = git("branch", "--show-current").strip()
    for candidate in (f"origin/{branch}" if branch else "", "origin/HEAD"):
        if not candidate:
            continue
        try:
            return git("rev-parse", "--verify", f"{candidate}^{{commit}}").strip()
        except CheckFailure:
            continue
    raise CheckFailure("no base ref could be resolved -- pass --base")


# --- checks -----------------------------------------------------------------


def check_versions(head: str) -> str:
    plugin = read_json_at(head, PLUGIN_JSON)
    market = read_json_at(head, MARKETPLACE_JSON)

    canonical = plugin.get("version")
    if not canonical:
        raise CheckFailure("plugin.json has no version field")

    found = {"plugin.json:version": canonical}
    found["marketplace.json:metadata.version"] = (market.get("metadata") or {}).get("version")
    plugins = market.get("plugins") or []
    if not plugins:
        raise CheckFailure("marketplace.json lists no plugins")
    found["marketplace.json:plugins[0].version"] = plugins[0].get("version")

    mismatched = {k: v for k, v in found.items() if v != canonical}
    if mismatched:
        detail = ", ".join(f"{k}={v!r}" for k, v in sorted(mismatched.items()))
        raise CheckFailure(f"version drift -- plugin.json declares {canonical!r} but {detail}")
    return f"all three version fields agree at {canonical} (read from {head[:8]})"


def outgoing_commits(base: str, head: str) -> list[str]:
    return git("rev-list", f"{base}..{head}").split()


def touched_paths(base: str, head: str) -> set[str]:
    """Every path touched by every outgoing commit.

    NOT `git diff base...head` -- that reports the net difference between two
    trees, so a file added in one outgoing commit and deleted in a later one
    never appears, while still shipping in the pushed history.
    """
    paths: set[str] = set()
    for sha in outgoing_commits(base, head):
        # --no-commit-id: without it diff-tree prefixes the sha, which then reads
        # as an unauthorized path.
        out = git("diff-tree", "--root", "--no-commit-id", "--no-renames",
                  "-r", "-z", "--name-only", sha)
        for entry in out.split("\0"):
            if entry.strip():
                paths.add(entry.strip())
    return paths


def check_range(base: str, head: str) -> str:
    paths = touched_paths(base, head)
    if not paths:
        return "nothing outgoing"
    unauthorized = sorted(
        p for p in paths if not p.startswith(AUTHORIZED_PREFIXES) and p not in AUTHORIZED_FILES
    )
    if unauthorized:
        raise CheckFailure(
            "outgoing commits touch unauthorized paths: " + ", ".join(unauthorized)
        )
    n = len(outgoing_commits(base, head))
    return f"{len(paths)} path(s) across {n} outgoing commit(s), all authorized"


def skill_names_at(rev: str) -> set[str]:
    """Skill names present at a revision, keyed on the SKILL.md manifest."""
    try:
        listing = git("ls-tree", "-r", "--name-only", rev, "--", SKILLS_DIR)
    except CheckFailure:
        return set()
    names = set()
    for line in listing.splitlines():
        rel = line.strip()[len(SKILLS_DIR) + 1 :]
        parts = rel.split("/")
        if len(parts) == 2 and parts[1] == "SKILL.md":
            names.add(parts[0])
    return names


def check_surface(head: str) -> str:
    """Verify the published surface in a clean checkout of the pushed commit."""
    with tempfile.TemporaryDirectory(prefix="release-gate-") as tmp:
        clean = Path(tmp) / "checkout"
        subprocess.run(
            ("git", "clone", "--quiet", "--no-hardlinks", "--no-checkout",
             str(REPO_ROOT), str(clean)),
            capture_output=True, text=True, check=True,
        )
        subprocess.run(
            ("git", "-C", str(clean), "checkout", "--quiet", "--detach", head),
            capture_output=True, text=True, check=True,
        )

        plugin = read_json_at(head, PLUGIN_JSON)
        read_json_at(head, MARKETPLACE_JSON)

        declared = (plugin.get("skills") or "./skills/").lstrip("./").rstrip("/")
        link = clean / declared
        if not link.is_symlink():
            raise CheckFailure(
                f"{declared!r} must be a symlink to {SKILLS_LINK_TARGET!r}; a real "
                "directory silently stops tracking .claude/skills/ updates"
            )
        target = os.readlink(link)
        if os.path.isabs(target) or Path(os.path.normpath(target)).as_posix() != SKILLS_LINK_TARGET:
            raise CheckFailure(
                f"{declared!r} points at {target!r}; it must be the relative path "
                f"{SKILLS_LINK_TARGET!r}, or installers get a broken link"
            )

        names = sorted(skill_names_at(head))
        if not names:
            raise CheckFailure(f"{declared!r} contains no skills at {head[:8]}")
        for name in names:
            fields = parse_frontmatter(show(head, f"{SKILLS_DIR}/{name}/SKILL.md"))
            for required in ("name", "description"):
                if not fields.get(required):
                    raise CheckFailure(f"{name}/SKILL.md frontmatter is missing {required!r}")

        broken = sorted(
            str(p.relative_to(clean))
            for p in clean.rglob("*")
            if p.is_symlink() and not p.exists()
        )
        if broken:
            raise CheckFailure("broken symlinks in a clean checkout: " + ", ".join(broken))

    return f"{len(names)} skill(s) well-formed and portable at {head[:8]}"


def check_new_skills(base: str, head: str, allowed: frozenset[str]) -> str:
    """Any skill name at HEAD that was absent at base must be classified.

    Compares name sets rather than diff status: git can report a rename as `R`,
    so an existing skill moved into a new public name would never show up as an
    addition.
    """
    new = skill_names_at(head) - skill_names_at(base)
    if not new:
        return "no new skills in range"

    unclassified = []
    for name in sorted(new):
        if name in allowed:
            continue
        try:
            fields = parse_frontmatter(show(head, f"{SKILLS_DIR}/{name}/SKILL.md"))
        except CheckFailure:
            fields = {}
        if fields.get("public_safe", "").lower() != "true":
            unclassified.append(name)

    if unclassified:
        raise CheckFailure(
            "new skill(s) not classified public-safe: "
            + ", ".join(unclassified)
            + " -- add a committed `public_safe: true` to the skill's frontmatter, "
            "or keep the skill in the private hub"
        )
    return f"{len(new)} new skill(s) classified public-safe"


CHECKS = ("versions", "range", "surface", "new-skills")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--release", action="store_true",
                        help="authorizing mode: all checks, base from the push refspec")
    parser.add_argument("--remote-sha", help="release mode: current sha of the remote ref")
    parser.add_argument("--local-sha", help="release mode: sha being pushed (default HEAD)")
    parser.add_argument("--check", choices=CHECKS, action="append", dest="checks")
    parser.add_argument("--base")
    parser.add_argument("--allow-new-skill", action="append", default=[], metavar="NAME")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)

    # Release mode accepts nothing that could weaken a check.
    if args.release:
        for flag, value in (("--check", args.checks), ("--base", args.base),
                            ("--allow-new-skill", args.allow_new_skill)):
            if value:
                print(f"release mode does not accept {flag}", file=sys.stderr)
                return 1

    results: list[dict[str, str]] = []
    failed = False
    base = head = None

    try:
        if args.release:
            head = git("rev-parse", "--verify",
                       f"{args.local_sha or 'HEAD'}^{{commit}}").strip()
            base = resolve_release_base(args.remote_sha or "")
        else:
            head = git("rev-parse", "--verify", "HEAD^{commit}").strip()
            base = resolve_diagnostic_base(args.base)
    except CheckFailure as exc:
        results.append({"check": "base", "status": "fail", "detail": str(exc)})
        failed = True

    selected = CHECKS if args.release else (args.checks or list(CHECKS))
    allowed = frozenset() if args.release else frozenset(args.allow_new_skill)

    if not failed:
        runners = {
            "versions": lambda: check_versions(head),
            "range": lambda: check_range(base, head),
            "surface": lambda: check_surface(head),
            "new-skills": lambda: check_new_skills(base, head, allowed),
        }
        for name in selected:
            try:
                results.append({"check": name, "status": "pass", "detail": runners[name]()})
            except CheckFailure as exc:
                results.append({"check": name, "status": "fail", "detail": str(exc)})
                failed = True
            except Exception as exc:  # fail closed
                results.append({"check": name, "status": "fail",
                                "detail": f"could not evaluate: {exc}"})
                failed = True

    mode = "release" if args.release else "diagnostic"
    if args.as_json:
        print(json.dumps({"ok": not failed, "mode": mode, "base": base,
                          "head": head, "checks": results}, indent=2))
    else:
        for entry in results:
            print(f"{'ok  ' if entry['status'] == 'pass' else 'FAIL'} "
                  f"{entry['check']}: {entry['detail']}")
        if failed:
            print("\nrelease gate: BLOCKED")
        elif args.release:
            print("\nrelease gate: PASS -- push authorized")
        else:
            print("\nrelease gate: diagnostic only -- this run authorizes nothing")

    if failed:
        return 1
    # Exit 2 on a clean diagnostic run so `release-gate.py && git push` cannot
    # mistake a partial, base-spoofable check for authorization.
    return 0 if args.release else 2


if __name__ == "__main__":
    sys.exit(main())
