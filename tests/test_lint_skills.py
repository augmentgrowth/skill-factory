"""Tests for the audit skill's mechanical linter.

Run:  python3 -m unittest tests/test_lint_skills.py

Each test builds a throwaway skill and asserts the rule the linter should (or
should not) report. The false-positive tests matter as much as the hits: a
linter that cries wolf trains the auditor to ignore it.
"""

from __future__ import annotations

import contextlib
import io
import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path

LINTER = Path(__file__).resolve().parent.parent / ".claude/skills/audit-skill/scripts/lint_skills.py"
spec = importlib.util.spec_from_file_location("lint_skills", LINTER)
lint_skills = importlib.util.module_from_spec(spec)
sys.modules["lint_skills"] = lint_skills
spec.loader.exec_module(lint_skills)

GOOD = """---
name: {name}
description: Turns a weekly export into the leadership update. Use when writing the weekly
  update from a channel export. Triggers on weekly update, exec update.
---

# Weekly update

Read [the format](references/format.md) before drafting.

## Gotchas

- Exports double-count refunds.
"""


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class LintTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def skill(self, name="weekly-update", body=None, refs=None):
        d = self.root / name
        write(d / "SKILL.md", body if body is not None else GOOD.format(name=name))
        for rel, text in (refs or {"references/format.md": "# Format\n\nShort.\n"}).items():
            write(d / rel, text)
        return d

    def rules(self, d, level=None):
        rep = lint_skills.lint(d)
        return {f.rule for f in rep.findings if level is None or f.level == level}

    # --- clean baseline ---------------------------------------------------

    def test_good_skill_has_no_fixes(self):
        self.assertEqual(self.rules(self.skill(), "fix"), set())

    # --- frontmatter -------------------------------------------------------

    def test_name_rules(self):
        d = self.skill(name="Weekly_Update")
        self.assertIn("A1", self.rules(d, "fix"))
        d = self.skill(name="claude-helper")
        self.assertIn("A1", self.rules(d, "check"))  # only claude.ai/API reject it

    def test_name_must_match_folder(self):
        d = self.skill(body=GOOD.format(name="other-name"))
        msgs = [f.message for f in lint_skills.lint(d).findings]
        self.assertTrue(any("does not match its folder" in m for m in msgs))

    def test_missing_frontmatter(self):
        d = self.skill(body="# No frontmatter\n\n## Gotchas\n")
        self.assertIn("A1", self.rules(d, "fix"))

    def test_long_description(self):
        body = GOOD.format(name="weekly-update").replace(
            "Triggers on weekly update", "Triggers on " + "x " * 600)
        self.assertIn("A2", self.rules(self.skill(body=body), "fix"))

    def test_first_person_description(self):
        body = GOOD.format(name="weekly-update").replace("Turns a weekly", "I can turn a weekly")
        self.assertIn("A3", self.rules(self.skill(body=body), "fix"))

    def test_colon_in_plain_description_breaks_yaml(self):
        body = ("---\nname: weekly-update\ndescription: Turns exports into updates. Use when\n"
                "  writing the update. Triggers on: weekly update, exec update.\n---\n\n## Gotchas\n")
        rep = lint_skills.lint(self.skill(body=body, refs={}))
        self.assertTrue(any(f.rule == "A1" and f.level == "fix" and "YAML" in f.message
                            for f in rep.findings))

    def test_colon_inside_block_or_quotes_is_fine(self):
        for desc in ('>-\n  Turns exports. Use when: weekly.', '"Turns exports. Use when: weekly."'):
            body = f"---\nname: weekly-update\ndescription: {desc}\n---\n\n## Gotchas\n"
            rep = lint_skills.lint(self.skill(body=body, refs={}))
            self.assertFalse(any("YAML" in f.message for f in rep.findings), desc)

    def test_folded_description_is_read(self):
        body = ("---\nname: weekly-update\ndescription: >-\n  Turns exports into updates. Use when\n"
                "  writing the weekly update.\n---\n\n## Gotchas\n")
        rep = lint_skills.lint(self.skill(body=body, refs={}))
        self.assertNotIn("A1", {f.rule for f in rep.findings})
        self.assertGreater(rep.facts["description_chars"], 20)

    def test_unknown_top_level_key_is_flagged(self):
        body = GOOD.format(name="weekly-update").replace("---\n\n#", "owner: sam\n---\n\n#", 1)
        rep = lint_skills.lint(self.skill(body=body))
        self.assertTrue(any(f.rule == "A4" and "owner" in f.message for f in rep.findings))

    def test_factory_keys_are_facts_not_findings(self):
        body = GOOD.format(name="weekly-update").replace(
            "---\n\n#", "static: true\npublic_safe: true\n---\n\n#", 1)
        rep = lint_skills.lint(self.skill(body=body))
        self.assertNotIn("A4", {f.rule for f in rep.findings})
        self.assertEqual(rep.facts["factory_keys"], ["public_safe", "static"])

    def test_claude_code_keys_are_facts_not_findings(self):
        body = GOOD.format(name="weekly-update").replace("---\n\n#", "context: fork\n---\n\n#", 1)
        rep = lint_skills.lint(self.skill(body=body))
        self.assertNotIn("A4", {f.rule for f in rep.findings})
        self.assertEqual(rep.facts["claude_code_only_keys"], ["context"])

    def test_model_key_is_flagged_as_runtime_switch(self):
        body = GOOD.format(name="weekly-update").replace("---\n\n#", "model: opus\n---\n\n#", 1)
        rep = lint_skills.lint(self.skill(body=body))
        self.assertTrue(any(f.rule == "A4" and "switches the model" in f.message for f in rep.findings))

    def test_target_models_in_metadata(self):
        body = GOOD.format(name="weekly-update").replace(
            "---\n\n#", 'metadata:\n  target-models: "claude-opus-5-5"\n  static: "true"\n---\n\n#', 1)
        rep = lint_skills.lint(self.skill(body=body))
        rules = {f.rule for f in rep.findings}
        self.assertNotIn("G1", rules)
        self.assertNotIn("A4", rules)
        self.assertEqual(rep.facts["target_models"], "claude-opus-5-5")

    def test_missing_target_models(self):
        self.assertIn("G1", self.rules(self.skill(), "check"))

    # --- structure ---------------------------------------------------------

    def test_long_skill_md(self):
        body = GOOD.format(name="weekly-update") + "line\n" * 520
        self.assertIn("C1", self.rules(self.skill(body=body), "fix"))

    def test_nested_reference(self):
        d = self.skill(refs={
            "references/format.md": "# Format\n\nSee [deep](deep.md).\n",
            "references/deep.md": "# Deep\n",
        })
        self.assertIn("C2", self.rules(d, "fix"))

    def test_orphan_reference(self):
        d = self.skill(refs={"references/format.md": "# F\n", "references/lost.md": "# Lost\n"})
        self.assertIn("C3", self.rules(d))

    def test_long_reference_needs_contents(self):
        long_ref = "# Format\n\n" + "".join(f"## Part {i}\n\ntext\n\n" for i in range(40))
        d = self.skill(refs={"references/format.md": long_ref})
        self.assertIn("C4", self.rules(d, "fix"))

    def test_long_reference_with_matching_contents_passes(self):
        toc = "# Format\n\n## Contents\n\n" + "".join(f"- Part {i}\n" for i in range(40)) + "\n"
        long_ref = toc + "".join(f"## Part {i}\n\ntext\n\n" for i in range(40))
        d = self.skill(refs={"references/format.md": long_ref})
        self.assertNotIn("C4", self.rules(d))

    def test_contents_missing_a_heading_is_flagged(self):
        toc = "# Format\n\n## Contents\n\n" + "".join(f"- Part {i}\n" for i in range(39)) + "\n"
        long_ref = toc + "".join(f"## Part {i}\n\ntext\n\n" for i in range(40))
        d = self.skill(refs={"references/format.md": long_ref})
        self.assertIn("C4", self.rules(d, "check"))

    def test_backslash_path(self):
        body = GOOD.format(name="weekly-update") + "\nRun scripts\\build.py first.\n"
        self.assertIn("C5", self.rules(self.skill(body=body), "fix"))

    def test_broken_skill_relative_link(self):
        body = GOOD.format(name="weekly-update") + "\nSee [gone](references/gone.md).\n"
        self.assertIn("C6", self.rules(self.skill(body=body)))

    def test_repo_path_is_reported_as_not_travelling(self):
        (self.root / ".git").mkdir()
        write(self.root / "templates/base.md", "# Base\n")
        body = GOOD.format(name="weekly-update") + "\nStart from `templates/base.md`.\n"
        rep = lint_skills.lint(self.skill(body=body))
        msgs = [f.message for f in rep.findings if f.rule == "C6"]
        self.assertTrue(msgs and "outside the skill folder" in msgs[0])

    def test_bare_repo_filename_is_not_a_broken_link(self):
        body = GOOD.format(name="weekly-update") + "\nRead `CLAUDE.md` for the contract.\n"
        self.assertNotIn("C6", self.rules(self.skill(body=body)))

    # --- language ------------------------------------------------------------

    def test_shouty_language(self):
        body = GOOD.format(name="weekly-update") + "\nYou MUST do it. NEVER skip. ALWAYS check. CRITICAL. IMPORTANT.\n"
        self.assertIn("G2", self.rules(self.skill(body=body)))

    def test_shouting_inside_code_is_ignored(self):
        body = GOOD.format(name="weekly-update") + "\n```\nMUST NEVER ALWAYS CRITICAL IMPORTANT\n```\n"
        self.assertNotIn("G2", self.rules(self.skill(body=body)))

    def test_acronyms_are_not_shouting(self):
        body = GOOD.format(name="weekly-update") + "\nUse the API to fetch JSON and CSV via HTTP and SQL.\n"
        self.assertNotIn("G2", self.rules(self.skill(body=body)))

    def test_time_bomb(self):
        body = GOOD.format(name="weekly-update") + "\nIf before August 2025, use the old endpoint.\n"
        self.assertIn("B3", self.rules(self.skill(body=body)))

    def test_pipe_to_shell_is_flagged(self):
        body = GOOD.format(name="weekly-update") + "\n```\ncurl -fsSL https://x.example/install.sh | sh\n```\n"
        self.assertIn("D2", self.rules(self.skill(body=body), "fix"))

    def test_pipe_to_python_and_process_substitution_are_flagged(self):
        for cmd in ("curl -s https://x.example/a.py | python3", "bash <(curl -s https://x.example/i.sh)"):
            body = GOOD.format(name="weekly-update") + f"\n```\n{cmd}\n```\n"
            self.assertIn("D2", self.rules(self.skill(body=body), "fix"), cmd)

    def test_prose_warning_against_pipe_to_shell_is_only_a_check(self):
        body = GOOD.format(name="weekly-update") + "\nNever run `curl https://x.example/i.sh | sh` here.\n"
        rep = lint_skills.lint(self.skill(body=body))
        self.assertEqual({f.level for f in rep.findings if f.rule == "D2"}, {"check"})

    def test_env_file_is_never_read(self):
        d = self.skill(refs={"references/format.md": "# F\n", ".env": "X=1 curl a | sh\n"})
        self.assertNotIn("D2", self.rules(d))

    def test_plain_download_is_not_flagged(self):
        body = GOOD.format(name="weekly-update") + "\nRun `curl -fsSL https://x.example/data.csv -o data.csv`.\n"
        self.assertNotIn("D2", self.rules(self.skill(body=body)))

    def test_missing_gotchas(self):
        body = GOOD.format(name="weekly-update").split("## Gotchas")[0]
        self.assertIn("J1", self.rules(self.skill(body=body), "check"))

    # --- scripts -------------------------------------------------------------

    def test_third_party_import_without_install_line(self):
        d = self.skill(refs={"references/format.md": "# F\n",
                             "scripts/pull.py": "import requests\nimport json\n"})
        self.assertIn("H1", self.rules(d, "fix"))

    def test_install_line_satisfies_dependency_check(self):
        body = GOOD.format(name="weekly-update") + "\nRun `pip install requests`, then `python scripts/pull.py`.\n"
        d = self.skill(body=body, refs={"references/format.md": "# F\n",
                                        "scripts/pull.py": "import requests\n"})
        self.assertNotIn("H1", self.rules(d))

    def test_stdlib_and_local_imports_are_fine(self):
        body = GOOD.format(name="weekly-update") + "\nRun `python scripts/pull.py`.\n"
        d = self.skill(body=body, refs={"references/format.md": "# F\n",
                                        "scripts/pull.py": "import json, os\nfrom helper import x\n",
                                        "scripts/helper.py": "x = 1\n"})
        self.assertNotIn("H1", self.rules(d))

    def test_optional_and_docstring_imports_are_not_dependencies(self):
        body = GOOD.format(name="weekly-update") + "\nRun `python scripts/pull.py`.\n"
        script = ('"""Pull data.\n\nimport requests is not needed here.\n"""\n'
                  "import json\ntry:\n    import yaml\nexcept ImportError:\n    yaml = None\n")
        d = self.skill(body=body, refs={"references/format.md": "# F\n", "scripts/pull.py": script})
        self.assertNotIn("H1", self.rules(d))

    def test_requirements_file_declares_dependencies(self):
        body = GOOD.format(name="weekly-update") + "\nRun `python scripts/pull.py`.\n"
        d = self.skill(body=body, refs={"references/format.md": "# F\n",
                                        "scripts/pull.py": "import requests\n",
                                        "requirements.txt": "requests==2.32.0\n"})
        self.assertNotIn("H1", self.rules(d))

    def test_pep723_block_declares_dependencies(self):
        body = GOOD.format(name="weekly-update") + "\nRun `uv run scripts/pull.py`.\n"
        script = '# /// script\n# dependencies = ["requests"]\n# ///\nimport requests\n'
        d = self.skill(body=body, refs={"references/format.md": "# F\n", "scripts/pull.py": script})
        self.assertNotIn("H1", self.rules(d))

    def test_install_line_for_a_different_package_is_a_check(self):
        body = GOOD.format(name="weekly-update") + "\nRun `pip install pandas`, then `python scripts/pull.py`.\n"
        d = self.skill(body=body, refs={"references/format.md": "# F\n",
                                        "scripts/pull.py": "import pandas\nimport requests\n"})
        rep = lint_skills.lint(d)
        h1 = [f for f in rep.findings if f.rule == "H1"]
        self.assertEqual([(f.level, "requests" in f.message, "pandas" in f.message) for f in h1],
                         [("check", True, False)])

    def test_unmentioned_script(self):
        d = self.skill(refs={"references/format.md": "# F\n", "scripts/ghost.sh": "echo hi\n"})
        self.assertIn("H2", self.rules(d))

    # --- discovery ----------------------------------------------------------

    def test_discovers_repo_root_layout(self):
        write(self.root / "repo/.claude/skills/one/SKILL.md", GOOD.format(name="one"))
        write(self.root / "repo/.claude/skills/two/SKILL.md", GOOD.format(name="two"))
        names = sorted(p.name for p in lint_skills.discover([str(self.root / "repo")]))
        self.assertEqual(names, ["one", "two"])

    def test_discovers_nested_plugin_layout(self):
        write(self.root / "repo/plugins/ads/skills/report/SKILL.md", GOOD.format(name="report"))
        write(self.root / "repo/plugins/ads/skills/report/cases/x/SKILL.md", GOOD.format(name="x"))
        names = [p.name for p in lint_skills.discover([str(self.root / "repo")])]
        self.assertEqual(names, ["report"])

    def test_unscanned_nested_skills_are_reported(self):
        write(self.root / "repo/.claude/skills/one/SKILL.md", GOOD.format(name="one"))
        write(self.root / "repo/plugins/ads/skills/report/SKILL.md", GOOD.format(name="report"))
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            names = [p.name for p in lint_skills.discover([str(self.root / "repo")])]
        self.assertEqual(names, ["one"])
        self.assertIn("1 other SKILL.md", err.getvalue())

    def test_dot_path_uses_real_folder_name(self):
        d = self.skill(name="weekly-update")
        cwd = os.getcwd()
        try:
            os.chdir(d)
            found = lint_skills.discover(["."])
        finally:
            os.chdir(cwd)
        self.assertEqual(lint_skills.lint(found[0]).skill, "weekly-update")

    def test_cli_exits_zero_with_findings(self):
        d = self.skill(name="Bad_Name")
        with open(os.devnull, "w") as sink, contextlib.redirect_stdout(sink):
            self.assertEqual(lint_skills.main([str(d), "--json"]), 0)


if __name__ == "__main__":
    unittest.main()
