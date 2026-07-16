# Frozen sample input — weekly-metrics-update

## Invocation context

A growth/marketing lead exports channel performance from their ad platforms every Monday
and has to turn it into a short written update for the leadership team. Leadership does not
read dashboards. They want to know what changed, what it means, and what is being done.

The export below is the frozen sample. It is representative, not live: real Monday data
differs every week, so this captured sample is the stable fixture the skill is tested against.

## The request as the builder would type it

> Here's this week's channel export. Write the weekly update for the leadership team.

## The export (pasted CSV)

```csv
channel,spend_this_week,spend_last_week,conversions_this_week,conversions_last_week,cpa_this_week,cpa_last_week,impressions_this_week,impressions_last_week
Google Search - Brand,4120,4050,198,201,20.81,20.15,142000,139500
Google Search - Nonbrand,18400,14200,214,205,85.98,69.27,880000,690000
Google Performance Max,9600,9450,131,128,73.28,73.83,1240000,1210000
Meta - Prospecting,12750,12900,142,169,89.79,76.33,2100000,2180000
Meta - Retargeting,3300,3250,118,121,27.97,26.86,410000,405000
LinkedIn - Sponsored,2100,2050,9,7,233.33,292.86,88000,86000
TikTok - Prospecting,1850,1900,21,19,88.10,100.00,620000,640000
Email - Promotional,0,0,86,79,0.00,0.00,0,0
Affiliate,2400,2350,64,71,37.50,33.10,0,0
Display - Remarketing,900,880,4,12,225.00,73.33,320000,315000
```

## Notes the builder would have in their head (not in the CSV)

- Total spend is roughly $55K/week; the team's target blended CPA is $65.
- Nonbrand search budget was deliberately increased this week as a growth test.
- Display - Remarketing is a small, long-tail line item nobody actively manages.
