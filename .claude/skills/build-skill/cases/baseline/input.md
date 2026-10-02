# Baseline case — build a skill from a described workflow

## Invocation context

A builder in a fresh git repo of their own (plugin install; no release gate) says:

> I want a skill for my Monday paid-social update. Every week I export last week's Meta campaign
> numbers, figure out blended CPA against our $65 target, and write leadership five bullets: what
> moved, what we're doing about it. They hate tables and hate hedging. Here's last week's export.

Pasted sample export (the frozen fixture):

```
campaign,spend,purchases,revenue,clicks,impressions
Prospecting - Broad,18420,262,51310,9120,1204000
Prospecting - LAL 1%,9310,121,23980,4410,612000
Retargeting - 7d,6120,118,27140,3020,198000
Retargeting - 30d,2210,19,4120,880,141000
```

The builder answers interview questions briefly and consistently with the above; they judge the
side-by-side honestly (with-skill wins only if it is visibly better).
