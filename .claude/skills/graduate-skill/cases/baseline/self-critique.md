# Self-critique — graduate-skill

Backfill run on 2026-10-06 for a skill built before the self-critique record existed. The six
checks ran against SKILL.md and references/script-efficiency-review.md as they stand; there was
no draft-stage audit to precede. One check is not a pass and was left unfixed; its row says
`weak` and it is listed under "Still weak".

| Check | Verdict | Evidence (from the skill) | Fixed |
|---|---|---|---|
| Voice | pass | SKILL.md:66–72 argues its own exception: output review "cannot observe quota exhaustion, a rate-limit ban, or a fetch that silently truncates", so the stop stays machine-to-machine; :134–137 "the one place the builder actually uses it" | — |
| Principles | pass | SKILL.md:66–72 explains why a CRITICAL finding blocks; :78–79 why skill-creator is handed off rather than driven ("its own instructions forbid external test runners wrapping it"); :134–137 why a rejected graduation needs two undos | — |
| Anti-Pattern | pass | SKILL.md:61–64 "never hand them the finding as a decision"; :78 "do NOT wrap, re-implement, or drive its runners"; :141–142 "Do not invent its mechanics"; :118 the copy never includes `.env` | — |
| Example | pass | SKILL.md:64–65 "a seeded N+1 loop calling the API once per item is CRITICAL — fix it to one batched call, re-run, proceed"; :86–88 the exact skip message; :103 the exact install command | — |
| Model Calibration | pass | The CRITICALs the lint counts (SKILL.md:59–72, and :23 in the checklist) are the severity label defined in references/script-efficiency-review.md, not emphasis; the other three (:61 BLOCKS, :78 NOT, :118 NEVER) each sit on a hard stop whose reason is in the same paragraph; no request to write out reasoning | — |
| Focus | weak | Gotchas SKILL.md:146–150: three of the four entries restate the body (:146 ≈ :124–126 frozen copy; :148 ≈ :113–116 static block; :150 ≈ :118–120 `.env`) | — (see Still weak) |

## Still weak

- **Focus — Gotchas restate the steps.** Proposed fix: cut the three restating entries (frozen
  copy, static block, `.env`) and keep the shared-config entry, so the section holds only
  real-failure knowledge; grow it from the next real graduation failure. Leaving it out of this
  backfill because removing gotchas is the builder's call.
