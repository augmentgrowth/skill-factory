# Failing case: rollback leaves failed-attempt residue behind

## How the skill was invoked

`improve-skill` running its normal anneal transaction against a skill whose fix
does not converge — three red replays, so Step 7 fires.

## The exact scenario

A skill `weekly-report` is annealing. During the three fix attempts the agent
creates files the skill did not previously have:

- `weekly-report/scripts/fetch.py` — attempt 1's new helper
- `weekly-report/references/api-notes.md` — attempt 2's extracted notes
- `weekly-report/scratch-output.txt` — attempt 3's debug dump

None of these exist in the skill's last good commit. All three attempts fail
their replay, so Step 7 runs:

```
git -C <repo> checkout <last-good-ref> -- .claude/skills/weekly-report
```

Then Step 7 step 3 commits "the restore plus the marker," path-scoped to the
skill folder.

## What to check

Inspect the skill folder after the Step 7 commit lands. Compare it against the
folder's contents at `<last-good-ref>`.
