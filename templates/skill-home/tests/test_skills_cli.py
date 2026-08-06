"""Tests for bin/skills — the hub's master-map / link-surgery CLI.

Every test runs the real `bin/skills` script as a subprocess against a throwaway
fixture tree. Harness roots (Claude, Codex, Hermes) and the Hermes config path are
redirected via environment variables so the suite never reads or writes the real
~/.claude, ~/.codex, or ~/.hermes directories.
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
SKILLS_BIN = REPO_ROOT / "bin" / "skills"


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


class CliTestCase(unittest.TestCase):
    """Builds a fake hub + fake harness roots in a temp dir."""

    def setUp(self):
        # resolve(): macOS hands out /var/... which is a symlink to /private/var,
        # and the CLI reports realpaths — compare like with like.
        self.tmp = Path(tempfile.mkdtemp(prefix="skills-cli-test-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)

        self.hub = self.tmp / "hub"
        self.claude_root = self.tmp / "home" / ".claude" / "skills"
        self.codex_root = self.tmp / "home" / ".codex" / "skills"
        self.hermes_root = self.tmp / "home" / ".hermes" / "skills"
        self.hermes_config = self.tmp / "home" / ".hermes" / "config.yaml"
        for d in (self.claude_root, self.codex_root, self.hermes_root):
            d.mkdir(parents=True, exist_ok=True)

        # --- personal tier ---
        write(
            self.hub / ".claude" / "skills" / "alpha" / "SKILL.md",
            "---\nname: alpha\ndescription: Alpha test skill.\n---\n\nBody.\n",
        )
        write(
            self.hub / ".claude" / "skills" / "beta" / "SKILL.md",
            "---\nname: beta\ndescription: Beta test skill.\n---\n\nBody.\n",
        )

        # --- an upstream source for the external tier ---
        self.upstream = self.tmp / "upstream" / "ext-one"
        write(
            self.upstream / "SKILL.md",
            "---\nname: ext-one\ndescription: External skill v1.\n---\n\nUpstream body v1.\n",
        )
        write(self.upstream / "reference.md", "upstream reference v1\n")

        # --- external tier (vendored copy of the above) ---
        self.vendored = self.hub / "vendor" / "skills" / "ext-one"
        write(
            self.vendored / "SKILL.md",
            "---\nname: ext-one\ndescription: External skill v1.\n"
            "static: true\ntier: external\nupstream: %s\n---\n\nUpstream body v1.\n"
            % self.upstream,
        )
        write(self.vendored / "reference.md", "upstream reference v1\n")

        # --- registry + hermes farm ---
        write(
            self.hub / "docs" / "topology" / "scopes.txt",
            "# scope registry\n",
        )
        (self.hub / "scopes" / "hermes").mkdir(parents=True, exist_ok=True)

        write(
            self.hermes_config,
            "agent:\n  name: hermes\nskills:\n  external_dirs: []\n"
            "  template_vars: true\ncurator:\n  enabled: true\n",
        )

    def env(self):
        e = dict(os.environ)
        e.update(
            {
                "SKILLS_HUB_ROOT": str(self.hub),
                "SKILLS_CLAUDE_ROOT": str(self.claude_root),
                "SKILLS_CODEX_ROOT": str(self.codex_root),
                "SKILLS_HERMES_ROOT": str(self.hermes_root),
                "SKILLS_HERMES_CONFIG": str(self.hermes_config),
                "SKILLS_VAULT_ROOT": str(self.tmp / "vault"),
            }
        )
        return e

    def run_cli(self, *args, expect_ok=True):
        proc = subprocess.run(
            [sys.executable, str(SKILLS_BIN)] + list(args),
            env=self.env(),
            capture_output=True,
            text=True,
        )
        if expect_ok and proc.returncode != 0:
            self.fail(
                "skills %s exited %d\nstdout:\n%s\nstderr:\n%s"
                % (" ".join(args), proc.returncode, proc.stdout, proc.stderr)
            )
        return proc

    def status_json(self):
        return json.loads(self.run_cli("status", "--json").stdout)


class TestStatus(CliTestCase):
    def test_status_lists_both_tiers(self):
        data = self.status_json()
        by_name = {s["name"]: s for s in data["skills"]}
        self.assertIn("alpha", by_name)
        self.assertIn("beta", by_name)
        self.assertIn("ext-one", by_name)
        self.assertEqual(by_name["alpha"]["tier"], "personal")
        self.assertEqual(by_name["ext-one"]["tier"], "external")
        self.assertEqual(
            Path(by_name["alpha"]["canonical"]).resolve(),
            (self.hub / ".claude" / "skills" / "alpha").resolve(),
        )

    def test_status_reports_link_locations(self):
        self.run_cli("link", "alpha", "--scope", "global")
        data = self.status_json()
        alpha = [s for s in data["skills"] if s["name"] == "alpha"][0]
        link_paths = {Path(l["path"]) for l in alpha["links"]}
        self.assertIn(self.claude_root / "alpha", link_paths)
        self.assertIn(self.codex_root / "alpha", link_paths)
        for link in alpha["links"]:
            self.assertEqual(link["status"], "valid")

    def test_status_text_output_mentions_skills(self):
        out = self.run_cli("status").stdout
        self.assertIn("alpha", out)
        self.assertIn("ext-one", out)

    def test_status_scans_hermes_external_dirs(self):
        extra = self.tmp / "hermes-external"
        extra.mkdir()
        write(
            self.hermes_config,
            "skills:\n  external_dirs:\n    - %s\n  template_vars: true\n" % extra,
        )
        os.symlink(self.hub / ".claude" / "skills" / "beta", extra / "beta")
        data = self.status_json()
        beta = [s for s in data["skills"] if s["name"] == "beta"][0]
        self.assertIn(extra / "beta", {Path(l["path"]) for l in beta["links"]})


class TestDoctor(CliTestCase):
    def test_doctor_clean_tree_exits_zero(self):
        proc = self.run_cli("doctor", expect_ok=False)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_doctor_fails_on_broken_link(self):
        os.symlink(self.hub / ".claude" / "skills" / "ghost", self.claude_root / "ghost")
        proc = self.run_cli("doctor", expect_ok=False)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("ghost", proc.stdout + proc.stderr)

    def test_doctor_warns_but_passes_on_undrained_case(self):
        write(
            self.hub / ".claude" / "skills" / "alpha" / "cases" / "2026-08-01-oops" / "input.md",
            "failing input\n",
        )
        proc = self.run_cli("doctor", expect_ok=False)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("2026-08-01-oops", proc.stdout)

    def test_doctor_ignores_baseline_and_annealed_cases(self):
        base = self.hub / ".claude" / "skills" / "alpha" / "cases"
        write(base / "baseline" / "input.md", "x\n")
        write(base / "experiments" / "input.md", "x\n")
        write(base / "2026-08-02-done" / "input.md", "x\n")
        write(base / "2026-08-02-done" / ".annealed", "")
        proc = self.run_cli("doctor", "--json", expect_ok=False)
        self.assertEqual(proc.returncode, 0)
        data = json.loads(proc.stdout)
        self.assertEqual(data["warnings"], [])

    def test_doctor_flags_vendor_drift(self):
        write(self.upstream / "reference.md", "upstream reference v2 CHANGED\n")
        proc = self.run_cli("doctor", expect_ok=False)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("ext-one", proc.stdout + proc.stderr)

    def test_doctor_warns_on_stale_lock(self):
        lock = self.hub / ".anneal" / "locks" / "alpha"
        write(lock, "pid: 999999\nstarted: 2000-01-01T00:00:00\n")
        proc = self.run_cli("doctor", "--json", expect_ok=False)
        self.assertEqual(proc.returncode, 0)
        data = json.loads(proc.stdout)
        self.assertTrue(any("alpha" in w for w in data["warnings"]), data["warnings"])


class TestLinkSurgery(CliTestCase):
    def test_link_unlink_roundtrip_updates_registry_and_fs(self):
        scope = self.tmp / "project"
        scope.mkdir()
        self.run_cli("link", "alpha", "--scope", str(scope))

        cc = scope / ".claude" / "skills" / "alpha"
        agents = scope / ".agents" / "skills" / "alpha"
        self.assertTrue(cc.is_symlink())
        self.assertTrue(agents.is_symlink())
        self.assertEqual(
            cc.resolve(), (self.hub / ".claude" / "skills" / "alpha").resolve()
        )

        registry = (self.hub / "docs" / "topology" / "scopes.txt").read_text()
        self.assertIn(str(scope), registry)

        # linking twice must not duplicate the registry line
        self.run_cli("link", "alpha", "--scope", str(scope))
        registry2 = (self.hub / "docs" / "topology" / "scopes.txt").read_text()
        self.assertEqual(
            registry2.count(str(scope)), registry.count(str(scope))
        )

        self.run_cli("unlink", "alpha", "--scope", str(scope))
        self.assertFalse(cc.exists() or cc.is_symlink())
        self.assertFalse(agents.exists() or agents.is_symlink())
        # registry lines are never removed — the registry bounds the scan
        self.assertIn(str(scope), (self.hub / "docs" / "topology" / "scopes.txt").read_text())

    def test_link_hermes_scope_uses_hub_farm(self):
        self.run_cli("link", "beta", "--scope", "hermes")
        farm = self.hub / "scopes" / "hermes" / "beta"
        self.assertTrue(farm.is_symlink())
        self.assertEqual(
            farm.resolve(), (self.hub / ".claude" / "skills" / "beta").resolve()
        )

    def test_link_resolves_external_tier_skill(self):
        self.run_cli("link", "ext-one", "--scope", "global")
        self.assertEqual(
            (self.claude_root / "ext-one").resolve(), self.vendored.resolve()
        )

    def test_link_unknown_skill_fails(self):
        proc = self.run_cli("link", "nope", "--scope", "global", expect_ok=False)
        self.assertNotEqual(proc.returncode, 0)

    def test_disable_removes_links_keeps_content(self):
        scope = self.tmp / "project"
        scope.mkdir()
        self.run_cli("link", "alpha", "--scope", "global")
        self.run_cli("link", "alpha", "--scope", str(scope))
        self.run_cli("disable", "alpha")

        self.assertFalse((self.claude_root / "alpha").is_symlink())
        self.assertFalse((self.codex_root / "alpha").is_symlink())
        self.assertFalse((scope / ".claude" / "skills" / "alpha").is_symlink())
        self.assertTrue(
            (self.hub / ".claude" / "skills" / "alpha" / "SKILL.md").exists()
        )

        data = self.status_json()
        alpha = [s for s in data["skills"] if s["name"] == "alpha"][0]
        self.assertEqual(alpha["links"], [])

    def test_enable_with_scope_relinks(self):
        self.run_cli("link", "alpha", "--scope", "global")
        self.run_cli("disable", "alpha")
        self.run_cli("enable", "alpha", "--scope", "global")
        self.assertTrue((self.claude_root / "alpha").is_symlink())

    def test_enable_without_scope_is_informational(self):
        proc = self.run_cli("enable", "alpha")
        self.assertIn("link", proc.stdout)


class TestVendorRefresh(CliTestCase):
    def test_refresh_propagates_upstream_edit_and_preserves_frontmatter(self):
        write(
            self.upstream / "SKILL.md",
            "---\nname: ext-one\ndescription: External skill v2.\n---\n\nUpstream body v2.\n",
        )
        write(self.upstream / "reference.md", "upstream reference v2\n")
        write(self.upstream / "new-file.md", "brand new\n")

        proc = self.run_cli("vendor", "--refresh", "ext-one")

        skill_md = (self.vendored / "SKILL.md").read_text()
        self.assertIn("Upstream body v2.", skill_md)
        self.assertIn("description: External skill v2.", skill_md)
        self.assertIn("static: true", skill_md)
        self.assertIn("tier: external", skill_md)
        self.assertIn("upstream: %s" % self.upstream, skill_md)
        self.assertEqual(
            (self.vendored / "reference.md").read_text(), "upstream reference v2\n"
        )
        self.assertTrue((self.vendored / "new-file.md").exists())
        self.assertIn("reference.md", proc.stdout)

    def test_refresh_then_doctor_is_clean(self):
        write(self.upstream / "reference.md", "upstream reference v2\n")
        self.run_cli("vendor", "--refresh", "ext-one")
        proc = self.run_cli("doctor", expect_ok=False)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
