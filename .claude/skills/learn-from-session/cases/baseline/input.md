# Baseline case — mine a session for preferences

## Invocation context

At the end of a session in which the `weekly-report` skill was active, the builder says
"learn from this session". The session contained, in order:

1. Builder, after the first report: "put the summary table first"
2. Builder, on an unrelated email draft: "eh, call it 'Q3 recap' for now"
3. Builder, after the second report: "again — table first, then commentary"
4. Builder: "and use our ad account act_88213 when you pull"

`weekly-report`'s SKILL.md currently says: "Lead with the narrative commentary, then the summary
table." It says nothing about which ad account to use.
