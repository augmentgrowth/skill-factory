# Self-critique — build-skill

Backfill run on 2026-10-06 for a skill built before the self-critique record existed. The six
checks ran against SKILL.md and its references as they stand; there was no draft-stage audit to
precede.

| Check | Verdict | Evidence (from the skill) | Fixed |
|---|---|---|---|
| Voice | pass | SKILL.md:20–22 "By default Claude free-hands 'make me a skill' into a generic SKILL.md with no baseline, no test, no Gotchas. This flow refuses to close until the skill provably wins side by side." | — |
| Principles | pass | Rules carry their reason: SKILL.md:78 baseline first "so the final side-by-side is literal"; :99 "because the type decides what the skill emphasizes"; :129–130 a fixture-quoting skill "wins the side-by-side by recall"; :157 "you are the worst judge of it" | — |
| Anti-Pattern | pass | SKILL.md:126 "Don't teach to the test"; :83 never inside a plugin's managed cache; :87 "never a live API pull"; Gotchas :218–235; references/describe-first.md:46–53 and reverse-engineer.md:53–58 "Watch for" lists | — |
| Example | fix | SKILL.md:114–116 before/after for strictness (prose "post the summary" → `scripts/post.py --dry-run`, shown, then run); :122–124 before/after for current-model wording | SKILL.md taught strictness and current-model wording only in the abstract; added one before/after line to each |
| Model Calibration | pass | One all-caps NEVER, on the secret-copy line (SKILL.md:211); :120 names MUST/NEVER only to forbid them; Step 6 "back to Step 4" is a loop on a concrete check, not a generic "double-check"; no request to write out reasoning | — |
| Focus | fix | Gotchas (SKILL.md:218–235) now hold only real-failure entries | Removed the birth placeholder "[Grow this from real failures…]", stale once three real gotchas existed (the template says to replace it with the first real one) |
