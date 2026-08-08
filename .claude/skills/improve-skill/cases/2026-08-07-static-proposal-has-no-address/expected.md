# Observed vs expected

## Why this matters despite AE3 passing

AE3 asserts a **safety** property — don't touch the vendor tree — and that property held, verifiably
and by construction. This case is about the **liveness** property sitting next to it: the proposal
has to actually reach the builder.

Right now the protocol guarantees the first and leaves the second to chance. A proposal written to
an agent-chosen path, uncommitted, in a busy repo, is one `git clean` or one branch switch from
gone — and unlike a case directory, nothing in the queue will ever notice it is missing. The
vendored branch explicitly says these skills "never enter the anneal queue," so the proposal file
*is* the entire record. Losing it loses the whole finding.

The asymmetry is the tell: the personal-tier bullet immediately below specifies both an action and
an exact commit message. The vendored bullet specifies neither. Same step, same paragraph, two very
different levels of precision.

## Expected

1. **A named location.** The protocol states where a static/vendored proposal goes — a specific
   directory, or an explicit rule for deriving one — so two agents running this a week apart put it
   in the same place. It need not be the same directory this repo happens to use for agent-config
   diffs; a dedicated proposals path is likely cleaner.
2. **An explicit durability instruction.** Commit the proposal (path-scoped, with a stated message
   shape), or state deliberately that it stays uncommitted and say why. Silence is the defect, not
   either answer.
3. **A tier test that keys on `tier:`, not on upstream tracking.** A skill with `tier: external` and
   no `upstream:` must still take the vendored branch. The current "tracks an upstream copy" phrasing
   invites a wrong read on exactly the skills most likely to be misfiled.

## Judgment rubric for the replay

Re-read Step 1's static/vendored branch after the fix:

- [ ] A vendored proposal has exactly one correct destination, derivable without guessing.
- [ ] Whether to commit it is stated, not implied — and if committed, the staging is path-scoped and
      the message shape is given, matching the precision of the personal-tier bullet beside it.
- [ ] The vendored-tier test keys on frontmatter (`tier: external`, or the `vendor/` path), so a
      missing `upstream:` cannot route a vendored skill into the anneal loop.
- [ ] The safety property is untouched: still "write NOTHING into the skill's folder", still checked
      at Step 1 before preflight and before any lock.
- [ ] Two agents given the same static failure would produce the proposal at the same path with the
      same durability outcome.

Pass = all five. Judgment read of the instructions, not a byte-diff.

## Scope note

Same as the lock-pid case: this is the factory's own loop shipping in the public plugin, so the fix
warrants a version bump and Malachi's review, not a quiet local commit. It is also **lower severity
than the lock defect** — that one silently disabled mutual exclusion; this one risks a lost
proposal. Worth batching into the next factory release rather than shipping a 0.3.2 on its own.
