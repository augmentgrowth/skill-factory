# Expected vs observed

## Observed (the bug)

All three attempt-created files are still present after the Step 7 commit:

- `weekly-report/scripts/fetch.py`
- `weekly-report/references/api-notes.md`
- `weekly-report/scratch-output.txt`

The skill folder is **not** back at its last good state. It is the last good
state *plus* the wreckage of three failed attempts — and that hybrid is now
committed, and under the autonomous-push policy, pushed.

`scripts/fetch.py` is the worst of the three: a skill that acquires a `scripts/`
folder becomes "script-backed," which changes how `graduate-skill` treats it
(the efficiency review becomes mandatory). A failed attempt silently
reclassifies the skill.

## Why it happens

`git checkout <ref> -- <folder>` and `git restore --source=<ref> -- <folder>`
both write only the paths that exist in `<ref>`. Neither deletes paths that
exist now but did not exist then. Step 7 relied on that behavior to protect the
case directory — correctly — but drew the wrong general conclusion from it.

The current text says:

> a path-scoped restore rewrites only files the old state knew about, so the
> case directory survives in place

True, and the case directory does survive. But the same mechanic is what leaves
every failed attempt's new file in place. The instruction observed the
beneficial half of the behavior and never accounted for the harmful half.

## Expected

After Step 7, the skill folder is byte-identical to `<last-good-ref>` **except**
for the active case directory, which survives with `input.md`, `expected.md`,
and its `.annealed` terminal marker intact.

Specifically:

1. Tracked files that changed are restored from the ref.
2. Files created during the attempts are removed — including untracked ones,
   which no restore form touches.
3. The active case directory is explicitly excluded from that removal. It was
   created during this transaction and would otherwise look exactly like
   attempt residue.
4. Before committing, `input.md`, `expected.md`, and `.annealed` are asserted
   present. The Gotchas section calls the case commit sacred; nothing currently
   checks it.
5. Repo HEAD never moves and the Step 3 case commit is never restaged.

## Judging a replay

Green when a Step 7 run leaves no attempt-created file behind, leaves the case
directory complete, and states in the commit body which residue it removed.
Red if any attempt file survives, or if the case directory loses a file.
