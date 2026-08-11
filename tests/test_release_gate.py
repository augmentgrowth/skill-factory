"""Tests for scripts/release-gate.py — the fail-closed pre-push release gate.

Every test runs the real script as a subprocess against a throwaway git
fixture. `RELEASE_GATE_ROOT` redirects the gate at that fixture so the suite
never inspects the real checkout or its remote.

The gate exists because origin is the public plugin source and no human reviews
the diff, so the tests care most about the *negative* verdicts: drift, stray
paths, malformed skills, unclassified new skills. A gate that only proves the
happy path would not be fail-closed.
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


class GateTestCase(unittest.TestCase):
    """Builds a minimal but structurally valid factory repo in a temp dir."""

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

        self.git("add", "-A")
        self.git("commit", "--quiet", "-m", "baseline")
        # A bare remote so `origin/main` resolves the way it does in real use.
        self.remote = self.tmp / "remote.git"
        subprocess.run(
            ("git", "init", "--quiet", "--bare", str(self.remote)), check=True
        )
        self.git("remote", "add", "origin", str(self.remote))
        self.git("push", "--quiet", "origin", "main")

    # --- helpers ---------------------------------------------------------

    def git(self, *args):
        return subprocess.run(
            ("git", "-C", str(self.repo), *args),
            capture_output=True,
            text=True,
            check=True,
        ).stdout

    def write_manifests(self, version, marketplace_version=None):
        marketplace_version = marketplace_version or version
        write(
            self.repo / ".claude-plugin/plugin.json",
            json.dumps({"name": "fixture", "version": version, "skills": "./skills/"}),
        )
        write(
            self.repo / ".claude-plugin/marketplace.json",
            json.dumps(
                {
                    "name": "fixture",
                    "metadata": {"version": marketplace_version},
                    "plugins": [{"name": "fixture", "version": marketplace_version}],
                }
            ),
        )

    def run_gate(self, *args):
        env = dict(os.environ, RELEASE_GATE_ROOT=str(self.repo))
        return subprocess.run(
            (sys.executable, str(GATE), "--json", *args),
            capture_output=True,
            text=True,
            env=env,
        )

    def verdict(self, result, check):
        payload = json.loads(result.stdout)
        for entry in payload["checks"]:
            if entry["check"] == check:
                return entry
        self.fail(f"no {check!r} verdict in {payload}")

    def commit(self, message):
        self.git("add", "-A")
        self.git("commit", "--quiet", "-m", message)

    # --- versions --------------------------------------------------------

    def test_matching_versions_pass(self):
        result = self.run_gate("--check", "versions")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(self.verdict(result, "versions")["status"], "pass")

    def test_marketplace_drift_fails(self):
        self.write_manifests(version="1.1.0", marketplace_version="1.0.0")
        result = self.run_gate("--check", "versions")
        self.assertEqual(result.returncode, 1)
        verdict = self.verdict(result, "versions")
        self.assertEqual(verdict["status"], "fail")
        self.assertIn("drift", verdict["detail"])

    def test_missing_version_field_fails(self):
        write(
            self.repo / ".claude-plugin/plugin.json",
            json.dumps({"name": "fixture", "skills": "./skills/"}),
        )
        result = self.run_gate("--check", "versions")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.verdict(result, "versions")["status"], "fail")

    def test_unparseable_manifest_fails_closed(self):
        write(self.repo / ".claude-plugin/marketplace.json", "{not json")
        result = self.run_gate("--check", "versions")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.verdict(result, "versions")["status"], "fail")

    # --- range -----------------------------------------------------------

    def test_docs_only_change_passes_without_version_bump(self):
        write(self.repo / "docs/notes.md", "notes\n")
        self.commit("docs: add notes")
        result = self.run_gate("--check", "range", "--check", "versions")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(self.verdict(result, "range")["status"], "pass")

    def test_unauthorized_path_fails(self):
        write(self.repo / "stray/secrets.txt", "oops\n")
        self.commit("chore: stray file")
        result = self.run_gate("--check", "range")
        self.assertEqual(result.returncode, 1)
        verdict = self.verdict(result, "range")
        self.assertEqual(verdict["status"], "fail")
        self.assertIn("stray/secrets.txt", verdict["detail"])

    def test_nothing_outgoing_passes(self):
        result = self.run_gate("--check", "range")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("nothing outgoing", self.verdict(result, "range")["detail"])

    # --- surface ---------------------------------------------------------

    def test_wellformed_surface_passes(self):
        result = self.run_gate("--check", "surface")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(self.verdict(result, "surface")["status"], "pass")

    def test_malformed_frontmatter_fails(self):
        write(
            self.repo / ".claude/skills/sample-skill/SKILL.md",
            "---\nname: sample-skill\n---\n\n# no description\n",
        )
        self.commit("chore: break frontmatter")
        result = self.run_gate("--check", "surface")
        self.assertEqual(result.returncode, 1)
        verdict = self.verdict(result, "surface")
        self.assertEqual(verdict["status"], "fail")
        self.assertIn("description", verdict["detail"])

    def test_missing_skill_manifest_fails(self):
        (self.repo / ".claude/skills/sample-skill/SKILL.md").unlink()
        write(self.repo / ".claude/skills/sample-skill/notes.md", "orphan\n")
        self.commit("chore: drop SKILL.md")
        result = self.run_gate("--check", "surface")
        self.assertEqual(result.returncode, 1)
        self.assertIn("SKILL.md", self.verdict(result, "surface")["detail"])

    def test_broken_skills_link_fails(self):
        (self.repo / "skills").unlink()
        (self.repo / "skills").symlink_to(".claude/nonexistent")
        self.commit("chore: break the skills link")
        result = self.run_gate("--check", "surface")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.verdict(result, "surface")["status"], "fail")

    # --- new skills ------------------------------------------------------

    def test_unclassified_new_skill_fails(self):
        write(self.repo / ".claude/skills/client-work/SKILL.md", SKILL_MD)
        self.commit("feat: add client-work skill")
        result = self.run_gate("--check", "new-skills")
        self.assertEqual(result.returncode, 1)
        verdict = self.verdict(result, "new-skills")
        self.assertEqual(verdict["status"], "fail")
        self.assertIn("client-work", verdict["detail"])

    def test_new_skill_passes_with_frontmatter_classification(self):
        write(
            self.repo / ".claude/skills/client-work/SKILL.md",
            SKILL_MD.replace("---\nname:", "---\npublic_safe: true\nname:", 1),
        )
        self.commit("feat: add classified skill")
        result = self.run_gate("--check", "new-skills")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(self.verdict(result, "new-skills")["status"], "pass")

    def test_new_skill_passes_with_explicit_allow_flag(self):
        write(self.repo / ".claude/skills/client-work/SKILL.md", SKILL_MD)
        self.commit("feat: add client-work skill")
        result = self.run_gate("--check", "new-skills", "--allow-new-skill", "client-work")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_editing_an_existing_skill_is_not_a_new_skill(self):
        write(self.repo / ".claude/skills/sample-skill/CHANGELOG.md", "[2026-08-11] edit\n")
        self.commit("chore: touch existing skill")
        result = self.run_gate("--check", "new-skills")
        self.assertEqual(result.returncode, 0, result.stdout)

    # --- aggregate -------------------------------------------------------

    def test_one_failing_check_blocks_the_whole_gate(self):
        self.write_manifests(version="1.1.0", marketplace_version="1.0.0")
        self.commit("chore: drift the manifests")
        result = self.run_gate()
        self.assertEqual(result.returncode, 1)
        self.assertFalse(json.loads(result.stdout)["ok"])


if __name__ == "__main__":
    unittest.main()
