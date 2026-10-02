# With-skill output (captured 2026-10-02)

The same request as `input.md`, in a fresh copy of the fixture repo, by a fresh agent told only to
read this skill's SKILL.md and follow it. Captured verbatim at the stop-and-ask point. Files
modified before approval: none. Compare side by side with `output-baseline.md`.

---

```
Audit progress:
- [x] 1. Scope resolved, skills listed
- [x] 2. Lint run over the scope
- [x] 3. Every skill judged against the rubric
- [x] 4. Report delivered, changes ranked, builder asked which to apply  ← stop here
- [ ] 5. Approved changes applied, nothing else
- [ ] 6. Each changed skill verified (if anything regressed, go back to step 5 for that skill)
- [ ] 7. Each changed skill saved, summary given
```

I audited the 2 skills in this repo against the current rubric (refreshed today against Anthropic's skill-authoring guidance and prompting pages for current models). Both are your own skills, so both can be edited. **I haven't changed anything yet.**

**The short version:** brand-voice is in good shape. meta-ads-weekly has four serious problems:
- **It never loads properly.** Its description breaks the skill's header, so it currently loads without one.
- **It can pause ad sets with no approval step.**
- **It can post to Slack with no approval step.**
- **It asks for the model's full reasoning to be written out.** Current models may refuse that instruction.

### brand-voice  (.claude/skills/brand-voice)
| Rule | Verdict | Evidence | Exact change |
|---|---|---|---|
| 1 · C4 Contents list | n.a. | No reference files | — |
| 2 · D1 Strictness | pass | SKILL.md:16–18: loose copy guidance, each rule gives its reason; nothing consequential | — |
| 3 · G1–G5 Model calibration | pass | SKILL.md:8 names `claude-sonnet-5-5`; no all-caps; no "show your reasoning"; scope stated outright at :6 | — |
| 4 · C1–C3 Size and references | pass | SKILL.md is 26 lines; no references | — |
| 5 · E1 Checklist | n.a. | One-pass rewrite, no ordered steps | — |
| 6 · F1 Concrete check | fix | SKILL.md:16–18 has the three rules, but nothing tells Claude to check the draft against them. Sonnet follows instructions literally, so it won't check unless told | Insert after line 22: "Before returning copy, check every line against the three rules above and the Gotchas; rewrite any line that fails, then check it again." |
| 7 · H1 Install lines | n.a. | No scripts or libraries | — |
| K1 Saved example | fix | No `cases/` or `evals/` | Add `cases/subject-line/` (I draft it, you confirm). `input.md`: "make this on-brand: Unlock your best recovery ever! Book wellness week now!" `expected.md` checks: names the service and the felt benefit, second person, present tense, no "!", no medical promise, no "Wellness" in a subject line. Also one near-miss that should not trigger: an internal report request. |

Also pass: A1 A2 A3 A4 B1 B2 B3 B4 B5 B6 C5 C6 I1 J1 J2.
- B2: "guest" in the body and "customers" in the description is fine. One is the brand's word, the other is what people actually say.
- B3: "2025 tests" at :26 explains why, so it isn't a rule that expires.

n.a.: C2–C4 (no references), H2–H4 (no scripts), L1 (not built by the factory).

### meta-ads-weekly  (.claude/skills/meta-ads-weekly)
| Rule | Verdict | Evidence | Exact change |
|---|---|---|---|
| 1 · C4 Contents list | fix | references/format.md:1 is 114 lines with no Contents list | Insert after line 1: "## Contents", then one bullet per section: Headline, Spend and revenue, Campaign table, Winners, Losers, Creative notes, Audience notes, Budget moves, Tests running, Next week. Not needed if you take item 14, because the file shrinks to about 44 lines. |
| 2 · D1 Strictness (pausing) | fix | SKILL.md:17 "Pause any ad set whose CPA is above $80 using the Meta Ads Manager": stops live spend, in prose, with no approval point | Replace line 17 with: "4. List every ad set whose CPA is above $80 under Budget moves as a recommended pause. Do not pause anything yourself; the user pauses them in Meta Ads Manager after reading the report." |
| 2 · D1 Strictness (posting) | fix | SKILL.md:21 "Post the report to the #growth Slack channel": no approval, no stop if the post fails | Replace line 21 with: "8. Show the user the finished report and ask whether to post it to #growth. Post only on a clear yes, exactly once; if the post fails, stop and say so rather than retrying." |
| 3 · G1 Target model | fix | No `metadata` → `target-models` | Insert after line 3: `metadata:` then `  target-models: "claude-sonnet-5-5"`. I assumed the same model as brand-voice; tell me if you run this one on a different model. |
| 3 · G2 Shouting | fix | SKILL.md:12 has five all-caps words (IMPORTANT, MUST, ALWAYS, NEVER, CRITICAL) applied to every step, not to one dangerous step | Delete line 12 |
| 3 · G3 Over-prescription | fix | references/format.md:7–113: each of the 10 sections repeats the same line 8 times (80 near-identical lines) | Under each `##` heading, replace the eight "Guidance line N…" lines with one line: "Keep it short and lead with the number." |
| 3 · G4 Show reasoning | fix | SKILL.md:19 "Write out your full reasoning for every number". Current models can refuse this | Replace line 19 with: "6. Give the report without showing your working; add a one-line explanation under any number that looks surprising." |
| 3 · G5 Smaller model | pass | Steps are explicit; revisit once G1 names the model | — |
| 4 · C2 References one level deep | fix | SKILL.md is 23 lines, so C1 passes. But references/examples.md is reachable only through format.md:3 | Replace line 18 with: "5. Write the report in the format in [the format guide](references/format.md); match the length and tone of the [past reports](references/examples.md)." |
| 5 · E1 Checklist | fix | SKILL.md:14–21: the steps depend on order, but there is no checklist to copy and nothing says to stop when the data pull fails | Insert before line 14: "Copy steps 1–8 into your response as a checklist and tick each off." Insert after line 14: "   If the pull errors or returns no campaigns, stop and tell the user; never report on an empty pull." |
| 6 · F1 Concrete check | fix | SKILL.md:20 "Double-check your work." is generic | Replace line 20 with: "7. Check every campaign's spend and revenue in the report against the step 1 data. If any figure disagrees, go back to step 2, recompute, and check again." |
| 7 · H1 Install lines | fix | scripts/pull_insights.py:4 imports `requests`; SKILL.md:14 runs the script with no install line and no mention of the token it needs | Replace line 14 with: "1. Pull last week's data: run `pip install requests` once, then `python3 scripts/pull_insights.py --days 7` with a Meta access token (ads_read) in the `META_TOKEN` environment variable." |
| A1 Header loads | fix | SKILL.md:3: the unquoted "Triggers on: …" makes the header invalid, so the skill loads with no description and never triggers. Claude Code's own checker didn't flag it; reading the header directly confirms it | Replace line 3 with `description: >-`, then the same text unchanged on the next two lines, indented two spaces |
| A3 Description triggers | fix | SKILL.md:3 is a summary plus a keyword list, with no "Use when" and no boundary. "weekly ads" can pull in ad-copy requests that belong to brand-voice | Replace line 3 with (keeps all four of your phrases): `description: >-` / `  Builds the weekly Meta Ads (Facebook and Instagram) performance report: ROAS, CPA and CTR per` / `  campaign, week-over-week flags, and the post to #growth. Use when someone asks for the meta` / `  report, weekly ads, facebook ads performance, or a ROAS update. Not for writing ad copy` / `  (brand-voice) or one-off ad questions outside the weekly report.` |
| B1 Nothing Claude knows | fix | SKILL.md:8–10: a role line plus definitions of Meta Ads, ROAS and CPA | Delete lines 8–10 |
| B3 Time bomb | fix | SKILL.md:23 "Before March 2026 the API returned spend in cents…" | Handled by the J1 change below |
| B5 Default, not a menu | fix | SKILL.md:15 "You can use pandas, polars, a spreadsheet, or do it by hand." | Replace line 15 with: "2. Compute ROAS, CPA and CTR per campaign in Python over the JSON from step 1, using only the standard library so nothing extra needs installing." |
| H3 Script error handling | fix | pull_insights.py has four problems: (1) at :18, a missing token crashes with a raw error; (2) at :21, any API error crashes with a raw error; (3) only the first page of results comes back, and Meta splits results into pages (25 by default), so campaigns can silently go missing from the report; (4) at :15, `act_123` is unexplained | Replace the whole script with the version below |
| J1 Gotchas section | fix | There is no `## Gotchas` section | Replace line 23 with: "## Gotchas", a blank line, then "- Spend from the pull is already in dollars. Only exports saved before March 2026 are in cents; divide those by 100 if you ever compare against one." This also fixes B3. |
| K1 Saved example | fix | No `cases/` or `evals/` | Add `cases/weekly-report/`. `input.md`: a frozen copy of one week's pull, which you paste. `expected.md` checks: the 10 sections in order, every spend/ROAS figure matches the input, CPA rises over 20% are flagged, over-$80 ad sets are listed as recommendations only, nothing is posted without a yes. I draft it; you confirm. |

Also pass: A2 A4 B2 B4 B6 C1 C3 C5 C6 H2 I1. n.a.: H4 (no tool names used), J2 (no gotchas yet), L1 (not built by the factory).

**Script replacement for item 6** (scripts/pull_insights.py):
```python
import argparse
import json
import os
import sys

import requests

TOKEN_ENV = "META_TOKEN"
AD_ACCOUNT_ID = "act_123"  # the ad account this report covers


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    args = ap.parse_args()
    token = os.environ.get(TOKEN_ENV)
    if not token:
        sys.exit("No Meta access token is set. Set it up as SKILL.md step 1 describes, then re-run.")
    url = f"https://graph.facebook.com/v21.0/{AD_ACCOUNT_ID}/insights"
    params = {"date_preset": f"last_{args.days}d", "level": "campaign",
              "fields": "campaign_name,spend,actions,action_values,clicks,impressions",
              "access_token": token}
    rows = []
    while url:
        resp = requests.get(url, params=params, timeout=30)
        body = resp.json()
        if not resp.ok or "data" not in body:
            sys.exit("Meta API error: " + str(body.get("error", {}).get("message", resp.status_code)))
        rows.extend(body["data"])
        url, params = body.get("paging", {}).get("next"), None
    print(json.dumps(rows))


if __name__ == "__main__":
    main()
```

**One more problem, not on the rubric:** step 4 judges *ad sets*, but the script only pulls *campaign-level* data (pull_insights.py:16, `"level": "campaign"`). Ad-set CPA isn't in the data at all. Which level did you mean? I haven't put a change on the list for this; it's your call.

### Ranked changes
1. [P1] meta-ads-weekly · A1: the header is broken, so the skill loads with no description and never triggers. Smallest fix: wrap the description as a block, wording unchanged.
2. [P1] meta-ads-weekly · D1: pausing ad sets happens in prose with no approval. Make it recommend-only.
3. [P1] meta-ads-weekly · D1: the Slack post has no approval. Show the report first, post once on a yes, stop if the post fails.
4. [P1] meta-ads-weekly · G4: replace "write out your full reasoning" with a one-line note on surprising numbers.
5. [P2] meta-ads-weekly · A3: rewrite the description with "Use when…" and "Not for…", keeping all four trigger phrases. This includes item 1's fix.
6. [P2] meta-ads-weekly · H3: the script crashes on a missing token or an API error, and silently drops campaigns past the first page of results.
7. [P2] meta-ads-weekly · H1: add the `requests` install line and the token note to step 1.
8. [P2] meta-ads-weekly · G2: delete the all-caps "IMPORTANT… MUST ALWAYS… CRITICAL" line.
9. [P2] meta-ads-weekly · B1: cut the role line and the definitions of Meta Ads, ROAS and CPA.
10. [P2] meta-ads-weekly · B5: pick one way to compute the metrics instead of four.
11. [P2] meta-ads-weekly · F1: replace "Double-check your work" with a check against the pulled data.
12. [P2] meta-ads-weekly · E1: add a copyable checklist and a stop when the pull fails.
13. [P2] meta-ads-weekly · C2: link the past-reports example straight from the skill's main file.
14. [P2] meta-ads-weekly · G3: collapse the 80 repeated guidance lines in the format guide to one per section. If you take this, item 15 isn't needed.
15. [P2] meta-ads-weekly · C4: add a Contents list to the format guide.
16. [P2] meta-ads-weekly · B3 + J1: add a Gotchas section and restate the "before March 2026, spend was in cents" note as a gotcha.
17. [P2] brand-voice · F1: check each line of copy against the three rules and the gotcha before handing it back.
18. [P3] meta-ads-weekly · G1: record the target model (assumed claude-sonnet-5-5).
19. [P3] meta-ads-weekly · K1: capture one saved example so later changes can be proven safe.
20. [P3] brand-voice · K1: capture one saved example so later changes can be proven safe.

Neither skill has a saved example yet. Until items 19 and 20 are done, I can re-check any changes with the lint and a header check, but I can't replay the skill to prove it still produces good output.

Which numbers should I apply? For example "all P1", "1, 3, 6", or "none".