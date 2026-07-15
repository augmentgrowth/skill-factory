# Reverse-engineer path

The builder can't fully articulate the workflow — or would rather show than tell. So
you do the work **live together first**, and the successful session becomes the source
material for the skill. This path asks the least articulation up front, which is why a
builder who can't describe their workflow defaults here.

## Do the work live

1. Get one real instance of the task with its real (or pasted-sample) input, and just
   do it — with the builder in the loop, correcting you as you go.
2. **Capture as you go**, because the session is the raw material:
   - **Decisions you made** — the choices that shaped good output. These become principles.
   - **Corrections the builder gave** — every "no, do it this way" and "that's wrong
     because…". These become the **principles and anti-patterns** — they are the highest-
     signal content in the skill, the exact places Claude's default was wrong.
   - **The final process** — the sequence that actually produced the accepted output.
3. Iterate live until the builder judges the output genuinely good. Only then extract.

## Extract the skill from the session

Turn the captured material into a draft: the corrections become explicit anti-patterns
(with the WHY the builder gave), the decisions become principles that transfer to new
instances, and the accepted sequence becomes the process — prose where judgment is
needed, exact text where it's fragile.

## Baseline is still Claude-default — capture it fresh

Do **not** reuse the good session output as the baseline. The baseline must be Claude's
**no-skill** output on the frozen input, captured fresh:

- **Step 2:** Freeze the same instance's input as `cases/baseline/input.md` (paste a
  representative sample for live-data workflows; no credentials in the flow). Then produce
  Claude's genuine no-skill output on it and save as `cases/baseline/output-baseline.md`.
  Birth commit. The bar the extracted skill must clear is **session-quality output** —
  the with-skill run should reproduce the quality you reached together live.

## Then run the rest of the spine

- **Step 3:** Classify per `templates/taxonomy.md` + one-or-many split.
- **Step 4:** Draft the extracted skill from `templates/TEMPLATE_Skill.md`
  against `quality-bar.md`; scaffold Gotchas at birth. Credentials lazy (`.env.example`
  only if actually needed; never echo a value).
- **Step 5:** Self-critique per `self-critique.md`; fix failures before showing the draft.
- **Step 6 (done gate):** Re-run the frozen input WITH the skill by explicit invocation;
  render baseline vs with-skill side by side. The builder judges — and should see the
  with-skill output matching the session quality. Loses or ties → back to Step 4. The
  gate will not close without the side-by-side shown.
- **Step 7:** One commit + `<skill>/known-good-1` tag + changelog line one, then offer
  the personal install.

## Watch for

- **Losing the corrections.** The moments the builder corrected you are the whole point —
  if you didn't capture them, the extracted skill is just your default with extra steps.
- **Baseline contamination.** If the baseline looks as good as the session output, you
  reused the session — recapture a true no-skill output, or the side-by-side proves nothing.
