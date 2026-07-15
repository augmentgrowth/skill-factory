# Describe-first path

The builder can explain the workflow. You interview to extract the expertise, then
run the shared spine (Steps 2–7 in `SKILL.md`). The interview is the whole edge here:
a skill drafted from a thin description is a generic skill.

## The interview — extract, don't accept the first answer

Ask these, and dig on each until you have something concrete enough to draft from:

- **What's the recurring task?** The exact repeating job, not the category. "Email
  marketing" is too broad; "the weekly paid-media report I send my client" is a skill.
- **Walk me through how you do it, step by step.** Get the real sequence — inputs,
  where you look, what you decide, what you produce. This is where tacit knowledge lives.
- **What does good output look like?** Ask for a concrete example of excellent past
  output. One real artifact teaches more than ten adjectives.
- **What does Claude get wrong by default?** The single most valuable answer. Their
  frustrations with generic AI output become the skill's anti-patterns. If they can't
  say, that's what Step 2's baseline will surface — capture it there and come back.
- **What decisions do you make that a stranger wouldn't?** The judgment calls, the "I
  always do X when Y" rules, the vocabulary insiders use. These become the principles.

If you can't state the problem and the default failure clearly after this, you're not
ready to draft — ask more, or route to reverse-engineer instead.

## Then run the spine

- **Step 2 (baseline):** Freeze one representative input from their examples. For a
  live-data workflow, paste a real sample export — never pull live, never touch
  credentials in the guided flow. Write `cases/baseline/input.md`, then produce and save
  Claude's genuine no-skill output as `cases/baseline/output-baseline.md`. Birth commit.
- **Step 3 (classify + split):** Type it per `templates/taxonomy.md`; apply the
  one-or-many rule before drafting.
- **Step 4 (draft):** Draft from `templates/TEMPLATE_Skill.md` against
  `quality-bar.md`. Turn each interview finding into a principle **with its WHY**, not a
  step. Name the anti-patterns they gave you explicitly. Scaffold Gotchas at birth.
- **Step 5 (self-critique):** Run `self-critique.md`; fix failures before showing the draft.
- **Step 6 (done gate):** Re-run the same frozen input WITH the skill by explicit
  invocation; render baseline vs with-skill side by side; the builder judges. Loses or
  ties → back to Step 4. The gate will not close without the side-by-side shown.
- **Step 7 (done):** One commit + `<skill>/known-good-1` tag + changelog line one, then
  offer the personal install.

## Watch for

- **A description so smooth it hides the hard parts.** The interesting content is the
  edge cases and corrections, not the happy path. Probe for where the workflow breaks.
- **Adjectives instead of examples.** "Make it punchy" is not a principle. Get the real
  artifact, extract what actually makes it good.
- **Comprehensive-itis.** More coverage is not better output — a focused skill beats a
  kitchen-sink one. Cut anything that doesn't change the output.
