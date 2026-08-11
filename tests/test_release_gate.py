"""Tests for scripts/release-gate.py — the fail-closed release gate.

Every test runs the real script as a subprocess against a throwaway git
fixture. `RELEASE_GATE_ROOT` redirects the gate at that fixture so the suite
never inspects the real checkout or its remote.

The gate is the only automated check between a defect and every plugin
installer, so the suite is deliberately weighted toward *negative* verdicts and
toward bypasses. A gate proven only on its happy path is not proven fail-closed.

Classes ending in `Bypass` are regressions for specific holes found in review;
each names the hole it pins.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GATE = REPO_ROOT / "scripts" / "release-gate.py"

DIAGNOSTIC_CLEAN = 2  # a clean diagnostic run authorizes nothing

SKILL_MD = """---
name: sample-skill
description: A sample skill used only as a test fixture.
---

# Sample

## Gotchas
"""


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


class GateFixture(unittest.TestCase):
    """A minimal but structurally valid factory repo with a bare remote."""

    def setUp(self):
        # resolve(): macOS hands out /var/... which is a symlink to /private/var.
        self.tmp = Path(tempfile.mkdtemp(prefix="release-gate-test-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.repo = self.tmp / "repo"
        self.repo.mkdir()

        self.git("init", "--quiet", "--initial-branch=main")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "Test")

        self.write_manifests(version="1.0.0")
        write(self.repo / ".claude/skills/sample-skill/SKILL.md", SKILL_MD)
        (self.repo / "skills").symlink_to(".claude/skills")
        write(self.repo / "README.md", "# fixture\n")
        self.commit("baseline")

        self.remote = self.tmp / "remote.git"
        subprocess.run(("git", "init", "--quiet", "--bare", str(self.remote)), check=True)
        self.git("remote", "add", "origin", str(self.remote))
        self.git("push", "--quiet", "-u", "origin", "main")
        self.base_sha = self.git("rev-parse", "HEAD").strip()

    # --- helpers ---------------------------------------------------------

    def git(self, *args):
        return subprocess.run(
            ("git", "-C", str(self.repo), *args), capture_output=True, text=True, check=True
        ).stdout

    def commit(self, message):
        self.git("add", "-A")
        self.git("commit", "--quiet", "-m", message)

    def write_manifests(self, version, marketplace_version=None):
        marketplace_version = marketplace_version or version
        write(
            self.repo / ".claude-plugin/plugin.json",
            json.dumps({"name": "fixture", "version": version, "skills": "./skills/"}),
        )
        write(
            self.repo / ".claude-plugin/marketplace.json",
            json.dumps({
                "name": "fixture",
                "metadata": {"version": marketplace_version},
                "plugins": [{"name": "fixture", "version": marketplace_version}],
            }),
        )

    def run_gate(self, *args):
        env = dict(os.environ, RELEASE_GATE_ROOT=str(self.repo))
        return subprocess.run(
            (sys.executable, str(GATE), "--json", *args),
            capture_output=True, text=True, env=env,
        )

    def release(self, *args):
        """Authorizing mode, based at the remote's current sha."""
        return self.run_gate("--release", "--remote-sha", self.base_sha, *args)

    def verdict(self, result, check):
        for entry in json.loads(result.stdout)["checks"]:
            if entry["check"] == check:
                return entry
        self.fail(f"no {check!r} verdict in {result.stdout}")

    def assertBlocked(self, result, check=None, contains=None):
        self.assertEqual(result.returncode, 1, result.stdout or result.stderr)
        if check:
            entry = self.verdict(result, check)
            self.assertEqual(entry["status"], "fail", entry)
            if contains:
                self.assertIn(contains, entry["detail"])

    def assertAuthorized(self, result):
        self.assertEqual(result.returncode, 0, result.stdout or result.stderr)
        self.assertTrue(json.loads(result.stdout)["ok"])


class Modes(GateFixture):
    def test_clean_release_authorizes(self):
        self.assertAuthorized(self.release())

    def test_clean_diagnostic_does_not_authorize(self):
        result = self.run_gate()
        self.assertEqual(result.returncode, DIAGNOSTIC_CLEAN, result.stdout)
        self.assertTrue(json.loads(result.stdout)["ok"])

    def test_release_rejects_check_subsetting(self):
        result = self.release("--check", "versions")
        self.assertEqual(result.returncode, 1)
        self.assertIn("--check", result.stderr)

    def test_release_rejects_explicit_base(self):
        result = self.release("--base", "HEAD")
        self.assertEqual(result.returncode, 1)
        self.assertIn("--base", result.stderr)

    def test_release_requires_remote_sha(self):
        result = self.run_gate("--release")
        self.assertBlocked(result, "base")


class Versions(GateFixture):
    def test_drift_blocks(self):
        self.write_manifests(version="1.1.0", marketplace_version="1.0.0")
        self.commit("drift")
        self.assertBlocked(self.release(), "versions", "drift")

    def test_missing_version_blocks(self):
        write(self.repo / ".claude-plugin/plugin.json",
              json.dumps({"name": "fixture", "skills": "./skills/"}))
        self.commit("drop version")
        self.assertBlocked(self.release(), "versions")

    def test_unparseable_manifest_fails_closed(self):
        write(self.repo / ".claude-plugin/marketplace.json", "{not json")
        self.commit("break json")
        self.assertBlocked(self.release(), "versions")


class Range(GateFixture):
    def test_docs_only_passes_without_version_bump(self):
        write(self.repo / "docs/notes.md", "notes\n")
        self.commit("docs: notes")
        self.assertAuthorized(self.release())

    def test_unauthorized_path_blocks(self):
        write(self.repo / "stray/secrets.txt", "oops\n")
        self.commit("stray")
        self.assertBlocked(self.release(), "range", "stray/secrets.txt")

    def test_nothing_outgoing_passes(self):
        self.assertAuthorized(self.release())


class AddThenDeleteBypass(GateFixture):
    """Pins: a file added and deleted inside the outgoing range still ships.

    `git diff base...HEAD` reports the net difference between two trees, so the
    path is invisible there while remaining fully retrievable from the pushed
    history.
    """

    def test_secret_added_then_deleted_still_blocks(self):
        write(self.repo / "private/client-secrets.md", "CLIENT SECRET\n")
        self.commit("add secret")
        self.git("rm", "--quiet", "private/client-secrets.md")
        self.commit("remove secret")

        # The net diff is empty -- this is the trap.
        net = self.git("diff", "--name-only", f"{self.base_sha}...HEAD").strip()
        self.assertEqual(net, "", "fixture no longer reproduces the net-diff blind spot")
        # ...and the secret is still in the history about to be pushed.
        self.assertIn("CLIENT SECRET", self.git("show", "HEAD~1:private/client-secrets.md"))

        self.assertBlocked(self.release(), "range", "private/client-secrets.md")


class PrefixBypass(GateFixture):
    """Pins: `startswith("skills")` authorized siblings of the skills symlink."""

    def test_skills_lookalike_directory_blocks(self):
        write(self.repo / "skills-private/customer-data.md", "client data\n")
        self.commit("lookalike dir")
        self.assertBlocked(self.release(), "range", "skills-private/customer-data.md")

    def test_skills_lookalike_file_blocks(self):
        write(self.repo / "skillsecrets.env", "TOKEN=abc\n")
        self.commit("lookalike file")
        self.assertBlocked(self.release(), "range", "skillsecrets.env")


class DirtyTreeBypass(GateFixture):
    """Pins: an uncommitted repair must not mask a defect in the pushed commit."""

    def test_uncommitted_version_repair_does_not_rescue(self):
        self.write_manifests(version="1.1.0", marketplace_version="1.0.0")
        self.commit("commit the drift")
        self.write_manifests(version="1.1.0")  # repaired, NOT committed
        self.assertBlocked(self.release(), "versions", "drift")

    def test_uncommitted_classification_does_not_rescue(self):
        write(self.repo / ".claude/skills/client-work/SKILL.md", SKILL_MD)
        self.commit("add unclassified skill")
        write(self.repo / ".claude/skills/client-work/SKILL.md",
              SKILL_MD.replace("---\nname:", "---\npublic_safe: true\nname:", 1))
        self.assertBlocked(self.release(), "new-skills", "client-work")


class Surface(GateFixture):
    def test_wellformed_passes(self):
        self.assertAuthorized(self.release())

    def test_missing_description_blocks(self):
        write(self.repo / ".claude/skills/sample-skill/SKILL.md",
              "---\nname: sample-skill\n---\n\n# no description\n")
        self.commit("drop description")
        self.assertBlocked(self.release(), "surface", "description")

    def test_malformed_opening_delimiter_blocks(self):
        write(self.repo / ".claude/skills/sample-skill/SKILL.md",
              "---junk\nname: x\ndescription: y\n---\n")
        self.commit("bad opener")
        self.assertBlocked(self.release(), "surface")

    def test_unclosed_frontmatter_blocks(self):
        write(self.repo / ".claude/skills/sample-skill/SKILL.md",
              "---\nname: x\ndescription: y\n---broken\n")
        self.commit("bad closer")
        self.assertBlocked(self.release(), "surface")

    def test_duplicate_key_blocks(self):
        write(self.repo / ".claude/skills/sample-skill/SKILL.md",
              "---\nname: x\nname: y\ndescription: z\n---\n")
        self.commit("dupe key")
        self.assertBlocked(self.release(), "surface", "duplicate")


class SymlinkTopologyBypass(GateFixture):
    """Pins: only `not p.exists()` was checked, so any locally-resolvable target passed."""

    def test_absolute_symlink_blocks(self):
        (self.repo / "skills").unlink()
        (self.repo / "skills").symlink_to(self.repo / ".claude/skills")
        self.commit("absolute link")
        self.assertBlocked(self.release(), "surface")

    def test_regular_directory_instead_of_symlink_blocks(self):
        (self.repo / "skills").unlink()
        write(self.repo / "skills/sample-skill/SKILL.md", SKILL_MD)
        self.commit("real dir")
        self.assertBlocked(self.release(), "surface", "symlink")

    def test_broken_link_blocks(self):
        (self.repo / "skills").unlink()
        (self.repo / "skills").symlink_to(".claude/nonexistent")
        self.commit("broken link")
        self.assertBlocked(self.release(), "surface")


class NewSkills(GateFixture):
    def test_unclassified_new_skill_blocks(self):
        write(self.repo / ".claude/skills/client-work/SKILL.md", SKILL_MD)
        self.commit("add client-work")
        self.assertBlocked(self.release(), "new-skills", "client-work")

    def test_committed_classification_passes(self):
        write(self.repo / ".claude/skills/client-work/SKILL.md",
              SKILL_MD.replace("---\nname:", "---\npublic_safe: true\nname:", 1))
        self.commit("add classified skill")
        self.assertAuthorized(self.release())

    def test_editing_existing_skill_is_not_new(self):
        write(self.repo / ".claude/skills/sample-skill/CHANGELOG.md", "[2026-08-11] edit\n")
        self.commit("touch existing")
        self.assertAuthorized(self.release())


class RenameEvasionBypass(GateFixture):
    """Pins: keying on diff status `A` missed a rename into a new public name."""

    def test_renamed_skill_is_treated_as_new(self):
        self.git("mv", ".claude/skills/sample-skill", ".claude/skills/client-work")
        self.commit("rename into a new public name")
        self.assertBlocked(self.release(), "new-skills", "client-work")


class AllowFlagBypass(GateFixture):
    """Pins: --allow-new-skill waved a skill through with no committed record."""

    def test_allow_flag_cannot_authorize(self):
        write(self.repo / ".claude/skills/client-work/SKILL.md", SKILL_MD)
        self.commit("add client-work")
        result = self.release("--allow-new-skill", "client-work")
        self.assertEqual(result.returncode, 1)
        self.assertIn("--allow-new-skill", result.stderr)


class PushEnforcement(GateFixture):
    """Pins: the gate must actually be wired to `git push`, not just documented.

    Copies the real script and the real hook into the fixture and drives an
    actual push, so this proves the enforcement path rather than the checks.
    """

    def setUp(self):
        super().setUp()
        for src, dst in (
            (GATE, self.repo / "scripts" / "release-gate.py"),
            (REPO_ROOT / "githooks" / "pre-push", self.repo / "githooks" / "pre-push"),
        ):
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            dst.chmod(0o755)
        self.git("config", "core.hooksPath", "githooks")
        self.commit("install the gate and its hook")
        self.git("push", "--quiet", "origin", "main")

    def remote_head(self):
        return subprocess.run(
            ("git", "-C", str(self.remote), "rev-parse", "main"),
            capture_output=True, text=True, check=True,
        ).stdout.strip()

    def push(self):
        return subprocess.run(
            ("git", "-C", str(self.repo), "push", "origin", "main"),
            capture_output=True, text=True,
        )

    def test_clean_push_succeeds(self):
        write(self.repo / "docs/notes.md", "notes\n")
        self.commit("docs: notes")
        result = self.push()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.remote_head(), self.git("rev-parse", "HEAD").strip())

    def test_failed_check_prevents_the_remote_ref_from_advancing(self):
        before = self.remote_head()
        write(self.repo / "stray/secrets.txt", "oops\n")
        self.commit("stray")
        result = self.push()
        self.assertNotEqual(result.returncode, 0, "push should have been blocked")
        self.assertIn("BLOCKED", result.stderr + result.stdout)
        self.assertEqual(self.remote_head(), before, "remote ref advanced despite a failed gate")

    def test_add_then_delete_secret_is_blocked_at_the_push(self):
        before = self.remote_head()
        write(self.repo / "private/client-secrets.md", "CLIENT SECRET\n")
        self.commit("add secret")
        self.git("rm", "--quiet", "private/client-secrets.md")
        self.commit("remove secret")
        result = self.push()
        self.assertNotEqual(result.returncode, 0, "push should have been blocked")
        self.assertEqual(self.remote_head(), before)


if __name__ == "__main__":
    unittest.main()
