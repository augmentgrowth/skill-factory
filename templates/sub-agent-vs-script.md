# Script vs. Prose vs. Sub-agent

Where should a piece of a skill live? This is the degrees-of-freedom question
in another form: match the mechanism to how much the agent should adapt.

## The one question

> "Could a competent person do this the same way every time from written
> steps, or does it need judgment in the moment?"

- **Same way every time** → **script.** Deterministic and fragile work wants
  code: exact commands, API calls, calculations, format transforms, anything
  with auth/retries/pagination. Scripts don't drift between runs, and an LLM
  doing 50 micro-steps compounds small errors into inconsistent output.
- **Needs judgment** → **prose.** Interpretation, adapting to context, writing
  the deliverable, triaging an error, deciding what to call next. State the
  principle and let Claude think.

## The factory's bias

**Scripts for the deterministic and fragile. Prose for judgment. Sub-agents
rarely.**

Push fragile operations down into `scripts/` — a wrong flag or an unhandled
rate limit fails quietly, and prose can't guarantee the literal string. Keep
the reasoning in prose so the skill stays adaptable.

## Sub-agents: the exception, not the toolkit

A sub-agent buys you one thing: an isolated context. That's worth it when a
step would otherwise flood the main conversation — a large-dataset pass, a deep
research fan-out, a review that reads far more than it reports.

It is **not** a place to park capabilities. A standing zoo of named sub-agents
(a "reviewer," a "documenter," a "validator" kept around permanently) is an
anti-pattern: it fragments logic, hides it from the skill's own files, and
rots silently. Reach for a sub-agent when context isolation is the actual need,
and let it end when the task ends. Default to script or prose first.

## Quick reference

| Work | Mechanism | Why |
|------|-----------|-----|
| API call with auth + retry | Script | Deterministic, fragile, must not drift |
| Metric calculation, ranking | Script | Pure logic; LLM adds variance |
| Format transform (JSON → Markdown) | Script | Exact and repeatable |
| Choosing what to do with the result | Prose | Needs judgment |
| Writing the summary / recommendation | Prose | Needs voice and interpretation |
| Deep research or large-context read | Sub-agent | Isolate context, return findings |
