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

    def test_tag_on_a_published_commit_pushes(self):
        """A rollback tag points at a deliberately older state.

        Gating it would evaluate that old tree against current release rules and
        fail, making the rollback affordance unpublishable — the exact tag the
        review gate depends on.
        """
        old = self.git("rev-parse", "HEAD").strip()
        write(self.repo / "docs/notes.md", "notes\n")
        self.commit("docs: notes")
        self.git("push", "--quiet", "origin", "main")
        self.git("tag", "-a", "sample-skill/rollback-1", old, "-m", "last accepted")
        result = subprocess.run(
            ("git", "-C", str(self.repo), "push", "origin", "sample-skill/rollback-1"),
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("already-published", result.stderr + result.stdout)

    def test_tag_on_an_unpublished_commit_is_still_gated(self):
        write(self.repo / "stray/secrets.txt", "oops\n")
        self.commit("stray")
        self.git("tag", "-a", "sneaky-1", "HEAD", "-m", "smuggle")
        result = subprocess.run(
            ("git", "-C", str(self.repo), "push", "origin", "sneaky-1"),
            capture_output=True, text=True,
        )
        self.assertNotEqual(result.returncode, 0, "a tag on unpushed content must be gated")

    def test_add_then_delete_secret_is_blocked_at_the_push(self):
        before = self.remote_head()
        write(self.repo / "private/client-secrets.md", "CLIENT SECRET\n")
        self.commit("add secret")
        self.git("rm", "--quiet", "private/client-secrets.md")
        self.commit("remove secret")
        result = self.push()
        self.assertNotEqual(result.returncode, 0, "push should have been blocked")
        self.assertEqual(self.remote_head(), before)

    def test_uninstalled_hook_lets_a_bad_push_through(self):
        """Pins the residual risk: the gate is opt-in per clone.

        Nothing inside a repo can set its own core.hooksPath, so a fresh clone
        pushes unguarded until something installs the hook. The factory's
        preflight is what installs it (CLAUDE.md, "Install the hook yourself"),
        which covers every clone the factory actually drives — but a clone
        nobody drives stays exposed.

        This test asserts the exposure rather than the protection, on purpose.
        If a future change makes an uninstalled clone safe, this test fails and
        the README's honesty caveat can come out with it.

        It points hooksPath at an EMPTY directory rather than unsetting it. An
        unset value falls through to the machine's global config, so on a
        developer with a global husky hook this asserted the wrong thing — and
        could fail for a reason that has nothing to do with the gate. Empty
        means "no hook ran" hermetically.

        Scope: this says nothing about server-side enforcement. It pins that no
        LOCAL gate ran, which is the claim the README makes.
        """
        before = self.remote_head()
        empty_hooks = self.repo / "no-hooks"
        empty_hooks.mkdir()
        self.git("config", "core.hooksPath", "no-hooks")
        write(self.repo / "stray/secrets.txt", "oops\n")
        self.commit("stray")
        result = self.push()
        self.assertEqual(
            result.returncode, 0,
            "expected an unguarded push; if this now fails, the gap is closed",
        )
        self.assertNotIn(
            "release gate", (result.stderr + result.stdout).lower(),
            "the gate ran despite no hook being installed",
        )
        self.assertNotEqual(
            self.remote_head(), before,
            "unauthorized content reached the remote, as an uninstalled hook allows",
        )


class SecretsSweep(unittest.TestCase):
    """Pins that tests/secrets-sweep.sh can actually FAIL.

    These controls were run by hand once and written into a dated verification
    record, which is exactly the "verified once, never again" shape the drills
    exist to replace. The sweep spends no model session, so nothing justified
    leaving it out of the suite.

    Each case names the evasion class it pins. The content cases matter most:
    the first version of the sweep required a QUOTED value, so three genuine
    credential shapes — every one of them the way a real .env is written —
    passed CLEAN.
    """

    SWEEP = REPO_ROOT / "tests" / "secrets-sweep.sh"

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sweep-test-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        for args in (
            ("init", "--quiet", "--initial-branch=main"),
            ("config", "user.email", "test@example.com"),
            ("config", "user.name", "Test"),
        ):
            subprocess.run(("git", "-C", str(self.repo), *args), check=True)

    def commit_files(self, files, message="fixture"):
        for rel, text in files.items():
            write(self.repo / rel, text)
        subprocess.run(("git", "-C", str(self.repo), "add", "-Af"), check=True)
        subprocess.run(
            ("git", "-C", str(self.repo), "commit", "--quiet", "-m", message), check=True
        )

    def sweep(self):
        return subprocess.run(
            (str(self.SWEEP), str(self.repo)), capture_output=True, text=True
        )

    def assert_detects(self, label):
        result = self.sweep()
        self.assertEqual(
            result.returncode, 1,
            f"sweep reported clean on {label}\n{result.stdout}\n{result.stderr}",
        )

    def test_clean_repo_with_env_example_passes(self):
        self.commit_files({
            ".env.example": "ANTHROPIC_API_KEY=\nWORKSPACE_ID=\n",
            "README.md": "# fixture\n",
        })
        result = self.sweep()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_secret_added_then_deleted_is_still_found(self):
        """The class the tree-only scan misses and the whole reason for a sweep."""
        self.commit_files({"leak.txt": "AKIA0987654321ZZZZZZ\n"}, "add")
        subprocess.run(("git", "-C", str(self.repo), "rm", "--quiet", "leak.txt"), check=True)
        subprocess.run(
            ("git", "-C", str(self.repo), "commit", "--quiet", "-m", "remove"), check=True
        )
        self.assert_detects("a secret added then deleted")

    def test_env_at_any_depth_is_found(self):
        self.commit_files({"a/b/c/.env": "TOKEN=abc\n"})
        self.assert_detects("a .env nested three directories deep")

    def test_unquoted_uppercase_assignment_is_found(self):
        """AWS_SECRET_ACCESS_KEY=... — unquoted and uppercase, as every .env writes it."""
        self.commit_files(
            {".env.example": "AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMIK7MDENGbPxRfiCYEXAMPLEKEY\n"}
        )
        self.assert_detects("an unquoted uppercase assignment")

    def test_unquoted_yaml_password_is_found(self):
        self.commit_files({"config.yml": "password: hunter2hunter2hunter2hunter2hunter2\n"})
        self.assert_detects("an unquoted YAML password")

    def test_shell_export_is_found(self):
        self.commit_files({"setup.sh": "export DB_PASSWORD=s3cretV4lueThatIsQuiteLongIndeed99\n"})
        self.assert_detects("an unquoted shell export")

    def test_jwt_is_found(self):
        self.commit_files(
            {"t.js": 'const t="eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.sig";\n'}
        )
        self.assert_detects("a JWT")

    def test_allowlist_is_path_scoped_not_pattern_scoped(self):
        """A key at a non-allowlisted path is found even when its content is identical
        to content that IS allowlisted elsewhere. Pins that the allowlist never
        silences a pattern globally."""
        secret = "AKIAABCDEFGHIJKLMNOP\n"
        self.commit_files({"docs/notes.md": secret})
        self.assert_detects("an allowlisted-content string at a non-allowlisted path")


class ShellDrillSyntax(unittest.TestCase):
    """`bash -n` over every shell drill.

    The drills are excluded from the suite because their behavioral halves spend
    real model sessions, but that left them with no guard at all — a typo would
    surface only when someone ran one by hand, weeks later.
    """

    def test_every_shell_script_parses(self):
        scripts = sorted((REPO_ROOT / "tests").glob("*.sh")) + [REPO_ROOT / "githooks/pre-push"]
        self.assertGreaterEqual(len(scripts), 4, "expected the drills to be discovered")
        for script in scripts:
            with self.subTest(script=script.name):
                result = subprocess.run(
                    ("bash", "-n", str(script)), capture_output=True, text=True
                )
                self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
