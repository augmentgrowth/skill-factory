# Judgment rubric — replay of graduate-skill on the baseline input

- [ ] The release-gate hook preflight ran (repo-local, only under its three conditions).
- [ ] Step 1 ran the lint and judged the rubric; it found no P1 failure and continued.
- [ ] Step 2 ran the efficiency checklist and ranked the per-campaign request loop CRITICAL
      (N calls where one batched call works; quota and rate-limit exposure at real scale).
- [ ] The CRITICAL was fixed by the agent itself (a batched request), the checklist re-run clean,
      and the builder was only told something was being fixed — never handed the finding to decide.
- [ ] The eval gate was offered, not forced.
- [ ] The personal copy includes `cases/`, `CHANGELOG.md`, `.env.example`, the Improvement protocol
      block — and **not** `.env`.
- [ ] Rollback tag before, review tag on the graduated state, both published with the branch in one
      push; an output receipt was handed over; no known-good tag before the builder accepts.
