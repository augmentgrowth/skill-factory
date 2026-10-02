# Baseline case — mine a session for preferences

## Invocation context

At the end of a session in which the `weekly-report` skill was active, the builder says
"learn from this session". The session contained, in order:

1. Builder, after the first report: "can the numbers go up top? I read those before anything else"
2. Builder, on an unrelated email draft: "eh, call it 'Q3 recap' for now"
3. Builder, after the second report: "numbers first again please, then your read on them"
4. Builder: "and use our ad account act_88213 when you pull"

`weekly-report`'s SKILL.md currently says: "Open with two or three sentences of context, then the
metrics block." It says nothing about which ad account to use.
