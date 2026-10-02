# Baseline case — audit a two-skill repo

## Invocation context

A builder opens a repo of their own skills (not the factory) and says:

> Audit my skills against Anthropic's updated skill best practices.

To replay, write the files below into a fresh git repo at the paths shown, commit them, and run
the audit there. One skill (`meta-ads-weekly`) carries most of the defects the rubric targets; the
other (`brand-voice`) is close to clean and checks that the audit does not invent fixes.

Planted defects in `meta-ads-weekly`, for judging: unparseable description (`Triggers on:` in a
plain value); over-explaining Meta/ROAS basics; shouty caps line; a menu of tools in step 2;
pausing ad sets (spends money) and posting to Slack (sends) as loose prose; no checklist or
loop-back for an ordered job; "write out your full reasoning"; generic "double-check your work";
date-conditional instruction; `requests` used with no install line; 114-line reference with no
Contents; `examples.md` reachable only through `format.md`; no Gotchas; no target model.

## Files

### `.claude/skills/brand-voice/SKILL.md`

````
---
name: brand-voice
description: >-
  Applies the Restore brand voice to customer-facing copy — emails, ads, landing pages, SMS.
  Use when writing or editing copy that customers will read, or when someone says "make this
  on-brand" or "brand voice check". Not for internal docs or reports.
metadata:
  target-models: "claude-sonnet-5-5"
---

# Brand voice

Default Claude copy is upbeat and generic ("Unlock your best self!"). Restore's voice is calm,
specific, and clinical-adjacent: it names the service and the felt benefit, never hype.

- Lead with the specific service and what the guest will feel, in that order.
- Second person, present tense. No exclamation marks — they read as hype in this category.
- Claims stay within what a front-desk associate could say out loud; no medical promises.

| Generic | On-brand |
|---|---|
| Unlock your best recovery ever! | Cryotherapy, three minutes, and your legs feel lighter for the drive home. |

## Gotchas

- "Wellness" is banned in subject lines — it tanked open rates in the 2025 tests.
````

### `.claude/skills/meta-ads-weekly/SKILL.md`

````
---
name: meta-ads-weekly
description: Weekly Meta Ads performance report. Triggers on: meta report, weekly ads, facebook ads performance, ROAS update.
---

# Meta Ads Weekly Report

You are an expert performance marketer. Meta Ads (formerly Facebook Ads) is an advertising
platform where businesses pay to show ads to users on Facebook and Instagram. ROAS means return
on ad spend and is calculated as revenue divided by spend. CPA means cost per acquisition.

IMPORTANT: You MUST ALWAYS follow these steps EXACTLY. NEVER skip a step. This is CRITICAL.

1. Pull last week's data by running `python scripts/pull_insights.py --days 7`.
2. Compute ROAS, CPA and CTR per campaign. You can use pandas, polars, a spreadsheet, or do it by hand.
3. Compare to the prior week and flag any campaign whose CPA rose more than 20%.
4. Pause any ad set whose CPA is above $80 using the Meta Ads Manager.
5. Write the report in the format in [the format guide](references/format.md).
6. Write out your full reasoning for every number before giving the report.
7. Double-check your work.
8. Post the report to the #growth Slack channel.

Before March 2026 the API returned spend in cents, so divide by 100 for older exports.
````

### `.claude/skills/meta-ads-weekly/references/examples.md`

````
# Past reports

**Week of 2026-09-21** — ROAS 3.1 (+0.4). Prospecting carried it; retargeting CPA up 22%, paused two ad sets.
````

### `.claude/skills/meta-ads-weekly/references/format.md`

````
# Report format

The weekly report follows this structure. See [examples](examples.md) for past reports.

## Headline

- Guidance line 1 for the Headline section: keep it short and lead with the number.
- Guidance line 2 for the Headline section: keep it short and lead with the number.
- Guidance line 3 for the Headline section: keep it short and lead with the number.
- Guidance line 4 for the Headline section: keep it short and lead with the number.
- Guidance line 5 for the Headline section: keep it short and lead with the number.
- Guidance line 6 for the Headline section: keep it short and lead with the number.
- Guidance line 7 for the Headline section: keep it short and lead with the number.
- Guidance line 8 for the Headline section: keep it short and lead with the number.

## Spend and revenue

- Guidance line 1 for the Spend and revenue section: keep it short and lead with the number.
- Guidance line 2 for the Spend and revenue section: keep it short and lead with the number.
- Guidance line 3 for the Spend and revenue section: keep it short and lead with the number.
- Guidance line 4 for the Spend and revenue section: keep it short and lead with the number.
- Guidance line 5 for the Spend and revenue section: keep it short and lead with the number.
- Guidance line 6 for the Spend and revenue section: keep it short and lead with the number.
- Guidance line 7 for the Spend and revenue section: keep it short and lead with the number.
- Guidance line 8 for the Spend and revenue section: keep it short and lead with the number.

## Campaign table

- Guidance line 1 for the Campaign table section: keep it short and lead with the number.
- Guidance line 2 for the Campaign table section: keep it short and lead with the number.
- Guidance line 3 for the Campaign table section: keep it short and lead with the number.
- Guidance line 4 for the Campaign table section: keep it short and lead with the number.
- Guidance line 5 for the Campaign table section: keep it short and lead with the number.
- Guidance line 6 for the Campaign table section: keep it short and lead with the number.
- Guidance line 7 for the Campaign table section: keep it short and lead with the number.
- Guidance line 8 for the Campaign table section: keep it short and lead with the number.

## Winners

- Guidance line 1 for the Winners section: keep it short and lead with the number.
- Guidance line 2 for the Winners section: keep it short and lead with the number.
- Guidance line 3 for the Winners section: keep it short and lead with the number.
- Guidance line 4 for the Winners section: keep it short and lead with the number.
- Guidance line 5 for the Winners section: keep it short and lead with the number.
- Guidance line 6 for the Winners section: keep it short and lead with the number.
- Guidance line 7 for the Winners section: keep it short and lead with the number.
- Guidance line 8 for the Winners section: keep it short and lead with the number.

## Losers

- Guidance line 1 for the Losers section: keep it short and lead with the number.
- Guidance line 2 for the Losers section: keep it short and lead with the number.
- Guidance line 3 for the Losers section: keep it short and lead with the number.
- Guidance line 4 for the Losers section: keep it short and lead with the number.
- Guidance line 5 for the Losers section: keep it short and lead with the number.
- Guidance line 6 for the Losers section: keep it short and lead with the number.
- Guidance line 7 for the Losers section: keep it short and lead with the number.
- Guidance line 8 for the Losers section: keep it short and lead with the number.

## Creative notes

- Guidance line 1 for the Creative notes section: keep it short and lead with the number.
- Guidance line 2 for the Creative notes section: keep it short and lead with the number.
- Guidance line 3 for the Creative notes section: keep it short and lead with the number.
- Guidance line 4 for the Creative notes section: keep it short and lead with the number.
- Guidance line 5 for the Creative notes section: keep it short and lead with the number.
- Guidance line 6 for the Creative notes section: keep it short and lead with the number.
- Guidance line 7 for the Creative notes section: keep it short and lead with the number.
- Guidance line 8 for the Creative notes section: keep it short and lead with the number.

## Audience notes

- Guidance line 1 for the Audience notes section: keep it short and lead with the number.
- Guidance line 2 for the Audience notes section: keep it short and lead with the number.
- Guidance line 3 for the Audience notes section: keep it short and lead with the number.
- Guidance line 4 for the Audience notes section: keep it short and lead with the number.
- Guidance line 5 for the Audience notes section: keep it short and lead with the number.
- Guidance line 6 for the Audience notes section: keep it short and lead with the number.
- Guidance line 7 for the Audience notes section: keep it short and lead with the number.
- Guidance line 8 for the Audience notes section: keep it short and lead with the number.

## Budget moves

- Guidance line 1 for the Budget moves section: keep it short and lead with the number.
- Guidance line 2 for the Budget moves section: keep it short and lead with the number.
- Guidance line 3 for the Budget moves section: keep it short and lead with the number.
- Guidance line 4 for the Budget moves section: keep it short and lead with the number.
- Guidance line 5 for the Budget moves section: keep it short and lead with the number.
- Guidance line 6 for the Budget moves section: keep it short and lead with the number.
- Guidance line 7 for the Budget moves section: keep it short and lead with the number.
- Guidance line 8 for the Budget moves section: keep it short and lead with the number.

## Tests running

- Guidance line 1 for the Tests running section: keep it short and lead with the number.
- Guidance line 2 for the Tests running section: keep it short and lead with the number.
- Guidance line 3 for the Tests running section: keep it short and lead with the number.
- Guidance line 4 for the Tests running section: keep it short and lead with the number.
- Guidance line 5 for the Tests running section: keep it short and lead with the number.
- Guidance line 6 for the Tests running section: keep it short and lead with the number.
- Guidance line 7 for the Tests running section: keep it short and lead with the number.
- Guidance line 8 for the Tests running section: keep it short and lead with the number.

## Next week

- Guidance line 1 for the Next week section: keep it short and lead with the number.
- Guidance line 2 for the Next week section: keep it short and lead with the number.
- Guidance line 3 for the Next week section: keep it short and lead with the number.
- Guidance line 4 for the Next week section: keep it short and lead with the number.
- Guidance line 5 for the Next week section: keep it short and lead with the number.
- Guidance line 6 for the Next week section: keep it short and lead with the number.
- Guidance line 7 for the Next week section: keep it short and lead with the number.
- Guidance line 8 for the Next week section: keep it short and lead with the number.

````

### `.claude/skills/meta-ads-weekly/scripts/pull_insights.py`

````
import argparse
import json

import requests

TOKEN_ENV = "META_TOKEN"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    args = ap.parse_args()
    import os
    resp = requests.get(
        "https://graph.facebook.com/v21.0/act_123/insights",
        params={"date_preset": f"last_{args.days}d", "level": "campaign",
                "fields": "campaign_name,spend,actions,action_values,clicks,impressions",
                "access_token": os.environ[TOKEN_ENV]},
        timeout=30,
    )
    print(json.dumps(resp.json()["data"]))


if __name__ == "__main__":
    main()
````
