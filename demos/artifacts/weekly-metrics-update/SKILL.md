---
name: weekly-metrics-update
description: Turn a weekly channel/marketing metrics export into the leadership
  update in our house format — verdict first, five bullets, every bullet ending in
  an action. Use when writing the weekly update, the Monday update, the leadership
  or exec update from a channel export, spend report, or performance CSV. Triggers
  on: weekly update, weekly channel update, leadership update, exec update, Monday
  update, write the update from this export, turn this export into an update.
---

# Weekly Metrics Update

Claude writes an excellent analyst's memo by default: every channel covered, every
caveat surfaced, a tidy "what moved / what held up" structure. That memo is the wrong
artifact. Leadership does not read dashboards and will not read two pages — and worse,
a memo that reports movement without judging it against our target makes a good week
read like a crisis. This skill spends nothing on teaching analysis. It carries the two
things Claude cannot know: **what our numbers are supposed to be, and how we talk to
this audience.**

## Instructions

### Lead with the verdict, not the delta

Open with one sentence answering the only question leadership is actually asking:
**are we winning this week?** Judge blended CPA against the **$65 target**, then say so
plainly — "We're at $56 blended against a $65 target" — before any movement is
described.

Why this rule exists: a percentage change is meaningless without the anchor. "Blended
CPA up 11%" reads as alarming; "blended CPA up 11% and still $9 under target" reads as
a controlled test working. Same numbers, opposite decision. Claude has the arithmetic
and none of the anchor, so it defaults to reporting the change as though the change is
the news. The change is never the news. The **position against target** is the news,
and the change explains it.

If the week is genuinely bad — over target, or under target but trending at a rate that
crosses it within ~2 weeks — say that in the same first sentence. Do not soften it and
do not bury it at the bottom under "suggested next steps."

### Deliberate tests are not problems

Before diagnosing any line, check it against what we chose to do:

| Currently deliberate | Treat as |
|---|---|
| Google Search - Nonbrand scale-up | Expected CPA rise. Report cost-of-test vs. volume bought. Do **not** recommend pulling back unless it breaches the target. |

A planned test that behaves exactly as planned is a *status line*, not a finding. The
failure mode here is real and expensive: Claude sees Nonbrand CPA +24% and writes a
diagnostic recommending we "decide explicitly whether we're scaling for volume or
optimizing for efficiency." That decision was already made. Telling leadership to
re-make a settled decision makes the update look like the team isn't running the plan.

Report a deliberate test as: what we bought, what it cost, and whether the price is
still worth paying. That is the only open question on a test.

### Five bullets. The limit is the point.

Maximum five bullets after the verdict. Not a soft target — the constraint is what
forces the ranking, and the ranking is the value you add over a dashboard.

Rank by **dollars at stake × how much it moved**, not by how interesting it is. A 3x
CPA swing on a $900 line is interesting and irrelevant. A 24% CPA rise on our largest
line is boring and the whole week.

If something doesn't make the top five, it did not matter this week. Do not append it
as an honorable mention, do not add a "what held up" section, do not add a table of the
rest. The channels that held steady are why we have a dashboard.

### Every bullet ends in an action with a name on it

Shape each bullet: **what changed → what it means → what happens next.** If you cannot
name the next action and who owns it, the bullet is an observation, and observations
belong in the dashboard.

"Meta Prospecting CPA up 18% on flat spend — looks like creative fatigue, checking
frequency and CTR trend this week" is a bullet. "Meta Prospecting CPA rose 18%" is a
row in a spreadsheet.

### Don't read noise as signal

Two filters, applied before anything reaches the bullets:

- **Small base:** under ~20 conversions, percentage swings are not signal. LinkedIn at 9
  conversions can double or halve on nothing. Never report a % change on a small base;
  report the absolute number if it matters at all.
- **Unmanaged long tail:** lines under ~$1K/week that nobody actively runs (currently
  **Display - Remarketing**) get zero bullets. The one exception: a swing that smells
  like *tracking* rather than performance is worth exactly one clause, because broken
  tracking on a small line is often broken tracking everywhere. "Display remarketing
  conversions fell 12→4 — tag check, not a demand signal" is the whole treatment.

### The one caveat that changes a decision

Claude's instinct is a Caveats section listing every epistemics disclaimer — last-touch
attribution, one-week windows, no LTV data. All true, all known here, none of it new to
this audience, and a wall of hedging reads as no conviction.

Keep **one** caveat, and only if it would change what someone does this week. Fold it
into the bullet it qualifies rather than giving it its own section.

### Voice

Plain sentences. No headers beyond the verdict and the bullets. No tables — this gets
read on a phone. Never write "it is worth noting that." Our vocabulary: *blended CPA*,
*nonbrand*, *prospecting* vs. *retargeting*, *the target*, *cost of test*. Say "we,"
not "the team."

## What good looks like

**Bad** (Claude's default — accurate, and unusable):

> ## Headline
> Spend rose ~7% week-over-week (~$55.4K vs ~$51.0K) while conversions were roughly flat
> (987 vs 1,012, down 2.5%). Blended CPA moved from $50.42 to $56.15 (+11%).
>
> ## What Moved
> **Google Search — Nonbrand (the story of the week)** Spend up $4.2K (+30%) for 9 more
> conversions (+4%). CPA went from $69.27 to $85.98 (+24%)...
>
> ## What Held Up
> - **Email — Promotional:** 86 conversions (+9%) at zero media cost...
> [six more sections]

Every number is right. It buries the verdict, treats a planned test as a mystery, spends
a section on a $900 line, and ends with four things for leadership to decide.

**Good:**

> **We're at $56 blended against our $65 target — a good week with one thing to watch.**
>
> • The nonbrand scale-up is working as designed: +$4.2K bought 9 more conversions at $86
>   CPA. That's the price of the test and it's still inside target. Holding the budget.
> • Meta prospecting is the one real dip — CPA $76→$90 on flat spend, conversions -16%.
>   Reads like creative fatigue. Pulling frequency and CTR trend this week.
> • Email delivered 86 conversions at no media cost, our best incremental return again.
> • Display remarketing conversions fell 12→4 — tag check, not a demand signal.
> • Next week's update will carry revenue by channel; CPA alone can't tell us if nonbrand
>   is buying worse customers or just pricier ones.

Verdict first. Five bullets. The test is reported as a test. The $900 line gets one
clause. The one caveat that changes a decision is the one that survives.

## Gotchas

- **A "0" in a spend column is not missing data.** Email and Affiliate run at zero media
  cost — they are real lines with real conversions, not broken rows. Do not drop them and
  do not compute a CPA of $0.00 for them; report conversions only.
- [Grow this from real failures.]

## Improvement protocol

When this skill fails during a run:
1. Fix the immediate problem so the current run succeeds.
2. Re-run the exact failing case; confirm it now passes before continuing.
3. Add a `## Gotchas` line capturing the trap so it can't recur.
4. Append one line to `CHANGELOG.md`: `[YYYY-MM-DD] What changed and why`.
5. Commit once — one anneal, one commit — touching only this skill's folder.

Skip this loop for one-off environmental failures (network timeout, rate limit, disk
full) — those aren't skill bugs. Escalate when the fix is uncertain, or when it would
reach outside this skill's own folder.

## Changelog

Changes live in `CHANGELOG.md` in this folder — one line per change:
`[YYYY-MM-DD] What changed and why`.

## Cases

This skill owns a `cases/` directory. At birth it holds one baseline pair:
`cases/baseline/input.md` (the frozen export and its invocation context) and
`cases/baseline/output-baseline.md` (Claude's no-skill output on that input). The
with-skill test re-runs the same `input.md` and is judged against the baseline.
