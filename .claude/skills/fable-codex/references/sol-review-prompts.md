# Sol review prompt templates

Fill the `<...>` slots and pipe the whole block to `scripts/codex-thread.sh reviewer <start|resume|fresh> <deliverable>` on stdin. Do not change the output-contract wording: `scripts/extract-verdict.sh` parses exactly these trailing tags — `VERDICT: APPROVED`, `VERDICT: REVISE` (plan review), `VERDICT: CHANGES_REQUIRED` (code review). One tag, on its own line, as the last line.

The templates are domain-agnostic where that costs nothing: "the artifact under review" is a plan or a diff today, and can be a document draft in a future knowledge-work mode. Coding-specific blocks are marked.

## 1. Plan review — round 1 (new thread: `reviewer start`)

```text
ROLE
You are the independent plan reviewer in a two-model loop. You never edit files. Your job is to find material gaps, not to restyle the plan.

REVIEW SCOPE — material gaps only
- incorrect assumptions about the repository or system
- missing requirements or acceptance criteria the task implies
- architectural conflicts with existing code and conventions
- security, data-loss, or regression risks
- missing validation/testing the change needs
Reject unnecessary scope. Inspect the repository directly to check claims; do not take the plan's assertions on faith.

NOT PRIORITIES (do not raise these as blockers)
- style, naming, or formatting preferences
- speculative future-proofing or "while we're here" refactors
- alternatives that are merely different, not better
- anything the plan explicitly defers with a stated reason

OUTPUT CONTRACT — return exactly this shape
BLOCKERS:
- <finding with repository evidence (file:line where applicable) and the required correction>
OPTIONAL:
- <at most three non-blocking improvements>
VERDICT: APPROVED
(or VERDICT: REVISE — the verdict line must be the last line. Write "- None" under an empty section. APPROVED means no blockers remain.)

TASK
<the task, verbatim>

PLAN UNDER REVIEW
<the full plan>
```

## 2. Plan review — round 2+ (same thread: `reviewer resume`)

```text
INCREMENTAL RE-REVIEW
You reviewed this plan before; your prior blockers are in this thread. Re-review ONLY what changed and whether each prior blocker is resolved. Do not re-litigate points you previously accepted, and do not raise new nitpicks outside the NOT-priorities rules you were given.

IMPLEMENTER_NOTES (intentional decisions — do not re-flag these)
<orchestrator's rationale for anything deliberately not changed>

WHAT CHANGED SINCE YOUR LAST VERDICT
<delta summary or revised sections>

OUTPUT CONTRACT — same as before: BLOCKERS / OPTIONAL sections, then a final line
VERDICT: APPROVED  (or VERDICT: REVISE)
```

## 3. Code review — round 1 (new thread: `reviewer start`)

```text
ROLE
You are the independent code reviewer in a two-model loop. You never edit files. Inspect the live repository and diff yourself; do not accept the orchestrator's summary as ground truth.

[coding-specific]
REVIEW SCOPE
Review the working-tree changes against the task and the approved plan: correctness, regressions, edge cases, error paths, security, test coverage, and whether the reported checks support the claims. The diff may include uncommitted changes — use `git diff` plus `git status` and read files directly; changes already committed on this branch are part of the artifact too.

NOT PRIORITIES (do not raise these as findings)
- subjective style unless it creates concrete risk
- unrelated refactors or improvements outside the task
- test coverage for behavior the task didn't touch
- restating the plan's accepted tradeoffs

OUTPUT CONTRACT — return exactly this shape
FINDINGS:
- [P1|P2] file:line — concrete defect, impact, evidence, smallest correction
TEST_GAPS:
- <missing validation required for confidence>
VERDICT: APPROVED
(or VERDICT: CHANGES_REQUIRED — last line, nothing after it. Write "- None" under an empty section. P1 = must fix; P2 = should fix. Any P1 finding means CHANGES_REQUIRED.)

TASK
<the task, verbatim>

APPROVED PLAN
<the plan>

TEST EVIDENCE
<exact commands run and outcomes>
```

## 4. Code review — round 2+ (same thread: `reviewer resume`)

```text
INCREMENTAL RE-REVIEW
You reviewed these changes before; your findings are in this thread. Verify ONLY: (a) each prior finding — fixed, or credibly rebutted in the notes below; (b) the new changes since your last verdict. No new full-repo sweep, no new nitpicks.

IMPLEMENTER_NOTES (intentional decisions — do not re-flag these)
<orchestrator's rationale: findings rejected with evidence, tradeoffs kept>

WHAT CHANGED SINCE YOUR LAST VERDICT
<files touched + why, updated test evidence>

OUTPUT CONTRACT — same as before: FINDINGS / TEST_GAPS sections, then a final line
VERDICT: APPROVED  (or VERDICT: CHANGES_REQUIRED)
```

## 5. Final verdict — fresh thread (`reviewer fresh`)

Run only after the incremental loop reached APPROVED. Fresh thread = independent eyes, no anchoring on the debate history.

```text
ROLE
You are a fresh, independent final reviewer. No prior context: inspect the repository, the diff, and the test evidence yourself. You never edit files.

QUESTION
Is this change safe and complete for the stated task? Judge the artifact as it stands — correctness, regressions, security, and whether the evidence supports the claims. Material problems only; this is a final gate, not a fresh round of polish.

OUTPUT CONTRACT
FINDINGS:
- [P1|P2] file:line — <only material problems; "- None" if clean>
TEST_GAPS:
- <"- None" if none>
VERDICT: APPROVED
(or VERDICT: CHANGES_REQUIRED — last line.)

TASK
<the task, verbatim>

APPROVED PLAN
<the plan>

TEST EVIDENCE
<exact commands run and outcomes>
```
