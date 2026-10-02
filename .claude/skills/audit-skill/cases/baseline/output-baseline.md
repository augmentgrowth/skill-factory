# Baseline output — no skill (captured 2026-10-02)

Claude with no audit skill, given `input.md`'s request in a copy of the fixture repo. Captured
verbatim from a fresh agent session told not to use any skill. Files modified: none.

Notable for judging the with-skill run: it never notices that `meta-ads-weekly`'s description
fails to parse as YAML (it calls the `Triggers on:` list fine), so the skill's biggest live defect
— it loads with no description — goes unreported. No per-rule verdicts, no file:line evidence
table, no numbered approval list.

---

# Skill audit: 2 skills in `.claude/skills/`

I checked both skills against Anthropic's skill-authoring guidance: the Agent Skills best-practices doc, the "Complete Guide to Building Skills for Claude", and the Claude Code "how we use skills" lessons. I haven't changed any files.

## Summary

| Skill | Overall | Biggest issue |
|---|---|---|
| `brand-voice` | In good shape | Only minor polish needed |
| `meta-ads-weekly` | Needs work | Unconfirmed side effects, a data gap that breaks step 3, padded instructions, and a fragile script |

---

## brand-voice — mostly good

**Already done well:**
- **Description** is in the third person. It says both what the skill does and when to use it, includes phrases people would actually say ("make this on-brand", "brand voice check"), and states what it is not for ("Not for internal docs").
- **Concise.** It skips general copywriting advice Claude already knows and only covers how Restore's voice differs from Claude's defaults.
- **A worked contrast** (generic vs. on-brand) shows the voice better than rules alone.
- **Has a `## Gotchas` section** built from a real result (the subject-line test).
- 26 lines, well under the 500-line limit.

**Minor suggestions:**
1. **Add more trigger words to the description.** "Customer-facing copy" is abstract. Add the words people actually type: "subject line", "ad copy", "SMS", "promo email", "rewrite this", "punch this up". Missed triggers are the most common reason a skill fails to load.
2. **Add 2–3 more example pairs.** One pair is thin. Cover a subject line, an SMS (short format), and a "claim we can't make" case. Those are the cases where Claude is most likely to slip back to its defaults.
3. **Explain the "no medical promises" rule.** Claude follows a rule more reliably when it knows the reason. Add one clause, e.g. "regulatory/legal exposure". Also give one example of a banned claim ("reduces inflammation", "heals").
4. **Check the `metadata.target-models` value.** It's harmless, since harnesses ignore extra keys, but nothing reads it. Make sure it says what you mean, or remove it.

---

## meta-ads-weekly — needs work

### High priority

**1. It takes real-world actions without asking first (steps 4 and 8).**
- Step 4 pauses live ad sets.
- Step 8 posts to Slack.

Both affect the outside world and are hard to undo. The guidance is to keep risky, hard-to-undo operations tightly scripted and to confirm before taking them. Right now a casual "how did ads do this week?" could pause campaigns.

There's also no stated way to do either step. "Using the Meta Ads Manager" is a web UI Claude can't use, and no Slack tool is named.

*Fix:*
- Change step 4 to: "List ad sets with CPA > $80 as **recommended pauses**; pause only after the user confirms, via `<named script/tool>`."
- Make step 8 "Draft the Slack post; post only on confirmation." Also name the tool that posts it.
- Consider adding `disable-model-invocation: true` to the frontmatter so the workflow only runs when someone asks for it explicitly.

**2. Step 3 can't be done with the data the skill pulls.**
- Step 1 pulls only `--days 7`.
- Step 3 compares against the *prior* week, which was never fetched.

Claude will either guess the numbers, re-run the script with arguments it makes up, or make up a comparison.

*Fix:* have the script fetch both weeks, either with explicit `time_range` dates or a `--compare` flag. Then step 3 works on data the skill actually has.

**3. "Conversion" and "revenue" are never defined.**
`actions` and `action_values` come back as lists covering many action types. CPA and ROAS depend completely on which type counts as a purchase (e.g. `purchase` vs `offsite_conversion.fb_pixel_purchase`). This is the kind of company-specific knowledge a skill exists to hold, and it's missing.

*Fix:* add one line naming the exact `action_type` to use. Better, have the script compute CPA and ROAS so the numbers are deterministic.

### Medium priority

**4. It explains things Claude already knows.**
- Line 8 sets a persona ("You are an expert performance marketer").
- Lines 8–10 define Meta Ads, ROAS and CPA.

None of this changes what Claude does. Remove it and spend those words on #3 instead.

**5. Too much emphatic wording.**
Line 12 ("IMPORTANT… MUST ALWAYS… EXACTLY… NEVER… CRITICAL") is the kind of capitalised emphasis Anthropic now advises against. Current models already follow instructions closely, and shouting makes them apply rules too rigidly. It also hides which steps actually matter: the risky ones (4 and 8) look no more important than "double-check your work".

*Fix:* use calm instructions and explain *why* the fragile steps are fragile.

**6. Vague or counterproductive steps.**
- Step 2 offers a menu ("pandas, polars, a spreadsheet, or by hand"). The guidance is to give one default rather than options, and ideally to do the calculation in the script.
- Step 6 ("full reasoning for every number before the report") fills the output and buries the report.
- Step 7 ("Double-check your work") gives no way to check anything.

*Fix:* replace steps 6 and 7 with one concrete check, e.g. "campaign spend sums to the account total; if not, say so". If you want the reasoning, ask for a short "how these were computed" note *after* the report.

**7. A time-sensitive note is left loose.**
Line 23 (spend was reported in cents before March 2026) is useful but sits on its own, and it will eventually go out of date. Move it into a `## Gotchas` section. Even better, have the script detect old data and convert it.

**8. No `## Gotchas` section.**
Recommended practice is to start every skill with one and grow it from real failures. Good first entries:
- the cents conversion,
- which conversion action counts,
- the Graph API paging limit (#10).

### Low priority: reference files

**9. `references/format.md` is 114 lines of repeated filler.**
All 80 bullets say the same thing: "Guidance line N for the X section: keep it short and lead with the number." That loads ~1.5k tokens of filler every time the skill runs and gives Claude nothing per section. It is also over 100 lines with no table of contents.

*Fix:* replace it with a ~15-line template: the 10 section headings, one sentence each on what goes there, and one filled-in example report.

**10. The links go two levels deep.**
`SKILL.md` links to `format.md`, which links to `examples.md`. Guidance is to keep references one level deep from SKILL.md, because Claude may only partly read a file that is linked from another reference file.

*Fix:* link `examples.md` directly from SKILL.md, or fold its one example into the format template.

**11. `references/examples.md` has a single one-line example.**
That isn't enough to show the format. Add 2–3 real past reports, especially one where nothing needed pausing.

### Script: `scripts/pull_insights.py`

**12. It can silently drop data (no paging).**
The Graph API returns results in pages. The script prints only `data` from the first page and ignores `paging.next`. With enough campaigns, the report covers only some of them and nothing says so.

*Fix:* follow `paging.next` until it runs out.

**13. Some `--days` values just fail.**
`date_preset=f"last_{days}d"` only works for values Meta supports (7, 14, 28, 30, 90…). `--days 10` fails.

*Fix:* use `time_range` with `since`/`until` dates (this also enables #2).

**14. No error handling.**
- `resp.json()["data"]` throws an unclear `KeyError` on any API error, such as an expired token or a rate limit.
- A missing `META_TOKEN` raises an unhelpful `KeyError`.

Scripts should handle errors themselves rather than leaving Claude to make sense of a traceback.

*Fix:*
- Call `resp.raise_for_status()`.
- Check for an `error` key in the response.
- Print a plain-language message, without echoing the token.

**15. Setup problems:**
- **Hard-coded account.** The account ID (`act_123`) is hard-coded. Make it a variable.
- **Script path depends on where it's run from.** `python scripts/pull_insights.py` assumes the working folder is the skill folder. Reference it relative to the skill directory instead.
- **Setup isn't documented.** Neither `META_TOKEN` nor the `requests` dependency is mentioned anywhere. Add a short "Setup" line or a `.env.example`.
- **Untidy imports.** `import os` sits inside the function.

**16. The description could be stronger.**
"Triggers on:" with a keyword list works, but the description doesn't say what the skill *produces* or that it can pause ad sets. Suggested:

> "Builds the weekly Meta (Facebook/Instagram) ads performance report — ROAS, CPA, CTR per campaign, week-over-week, flagged CPA spikes and recommended pauses. Use for 'meta report', 'weekly ads report', 'how did Facebook ads do', 'ROAS update'."

---

## Suggested order of work
1. Make pauses and Slack posts happen only after confirmation (#1).
2. Fetch the prior week and define the conversion action (#2, #3).
3. Add paging and error handling to the script (#12–14).
4. Trim the SKILL.md wording and add `## Gotchas` (#4–8).
5. Replace `format.md` with a short template and flatten the links (#9–11).
6. Polish the `brand-voice` triggers and examples.

I can apply any or all of these. The `meta-ads-weekly` rewrite (items 1–8 plus the script fixes) is the one most worth doing.

---ACTIONS---
none