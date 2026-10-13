# Input and invocation

Invoked audit-skill for the user-approved personal skills audit, through its SKILL.md.

Exact relevant frontmatter input (synthetic name; offending lines unchanged):

```yaml
---
name: flow-sequence-probe
description: Test valid YAML flow sequences.
writes_to: []
tools: [get_page, query, graph, backlinks]
---
```

Invocation: `python3 .claude/skills/audit-skill/scripts/lint_skills.py /path/to/flow-sequence-probe --json`

Observed in a real skill audit: both flow-sequence fields received A1 fix findings saying YAML reads them as syntax and recommending scalar quoting.
