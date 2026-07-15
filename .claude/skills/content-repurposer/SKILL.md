---
name: content-repurposer
description: Repurpose a webinar, podcast, talk, or transcript into a tweet thread, LinkedIn post, and newsletter draft. Use when converting a recording into social content. Triggers on: repurpose this webinar/podcast/talk/transcript into posts, turn this transcript into a tweet thread / LinkedIn post / newsletter, make social content from this recording.
---

# Content Repurposer — Transcript to Multi-Platform Content

## Goal
Take a transcript (podcast, talk, video, meeting) and produce three pieces of content:
1. **Tweet thread** (5-10 tweets)
2. **LinkedIn post** (single post, 150-300 words)
3. **Newsletter draft** (500-800 words)

Each format has its own voice, structure, and constraints. They share the same source material but are NOT copy-pasted versions of each other. The default failure to correct: Claude flattens all three into the same paragraphs with hashtags and "Thread: 1/" scaffolding.

## Inputs
- **Transcript**: A file path or pasted text. Any format — raw transcript, SRT, VTT, or plain text.
- **Author name** (optional): Ask the user, or infer from the transcript/context. Never assume a default person.
- **Topic focus** (optional): If the transcript covers multiple topics, specify which to focus on.

## Process

### Step 1: Read and Extract
Read the transcript. Identify:
- **Core thesis** — the single biggest idea (1 sentence)
- **3-5 key insights** — supporting points, stats, quotes, or stories worth highlighting
- **Best quotes** — punchy, shareable lines (exact words from transcript)
- **Narrative arc** — the logical flow from setup to payoff

Do NOT summarize the transcript. Extract the raw material that makes each format work.

### Step 2: Generate All Three Formats
Produce the three formats **sequentially** — this is the portable default and needs no special tooling. For each, use the format-specific template in [templates.md](templates.md) and the worked example in [examples/podcast_example.md](examples/podcast_example.md). (A harness with parallel sub-agents MAY fan the three out concurrently as an accelerant, but do not depend on it.)

Feed each format the same Step 1 material — core thesis, key insights, best quotes, narrative arc — then write to that format's template and rules.

### Step 3: Present Output
Show all three pieces in-chat with clear headers. Then offer to save them to files the user names (default `repurposed_content/{date}_{format}.md` relative to the working directory) — do not write files unprompted.

## Voice & Tone
- **Register**: Smart-casual. Like explaining something interesting to a friend who's also sharp.
- **No corporate speak**: No "leveraging synergies", no "thought leadership", no "in today's fast-paced world".
- **No exclamation marks** in tweets or LinkedIn. One max in newsletter (if genuinely exciting).
- **Contractions are fine**: "don't", "isn't", "we're" — write like you talk.
- **Specific > generic**: "We cut onboarding from 3 weeks to 4 days" beats "We improved onboarding significantly".

## Format-Specific Rules

See [templates.md](templates.md) for detailed templates and [examples/podcast_example.md](examples/podcast_example.md) for a worked example. Summary:

### Tweet Thread
- 5-10 tweets, each standalone-readable
- Tweet 1 is the hook — bold claim or surprising stat, no preamble
- Last tweet is a summary + soft CTA
- No hashtags. No "1/" numbering. No "Thread:" label.
- Each tweet under 280 chars

### LinkedIn Post
- Single post, 150-300 words
- Hook line (first line visible before "see more") must be arresting
- Short paragraphs (1-2 sentences each)
- End with a question to drive comments
- No hashtags in body. 3-5 hashtags only at the very end, separated by a line break.

### Newsletter Draft
- 500-800 words
- Subject line + preview text included
- Starts with a story or scenario, not "In this issue..."
- Sections with headers
- Ends with a single clear takeaway or action item
- Conversational but slightly more polished than tweets

## Edge Cases
- **Transcript too short (< 500 words)**: Produce tweet thread + LinkedIn only. Skip newsletter, note why.
- **Multiple distinct topics**: Ask user which to focus on, or pick the most compelling one.
- **Transcript is an interview**: Attribute quotes properly. Use "According to [Guest]..." in newsletter.
- **No clear thesis**: Flag this to the user. Still produce content but note it may need a stronger angle.
- **Non-English transcript**: Produce content in the same language as the transcript.

## Gotchas
- **Transcripts under ~500 words can't support a newsletter.** There isn't enough raw material for 500-800 words without padding. Produce the thread + LinkedIn only and say why — don't inflate.
- **SRT/VTT timestamps and cue numbers are noise.** Strip the `00:00:12,400 --> 00:00:15,900` lines and index numbers before extraction, or they leak into quotes and derail the thesis pass.
- **Don't reuse the same sentences across all three formats.** If a line appears verbatim in the thread and the LinkedIn post, one of them is wrong — each format earns its own phrasing.

## Improvement protocol
When this skill fails during a run:
1. Fix the immediate problem so the current run succeeds.
2. Re-run the exact failing case; confirm it now passes before continuing.
3. Add a `## Gotchas` line capturing the trap so it can't recur.
4. Append one line to `CHANGELOG.md`: `[YYYY-MM-DD] What changed and why`.
5. Commit once — one anneal, one commit — touching only this skill's folder.

Skip this loop for one-off environmental failures (network timeout, rate limit, disk full) — those aren't skill bugs. Escalate to the user when the fix is uncertain, or when it would reach outside this skill's own folder.

## Changelog
Changes live in `CHANGELOG.md` in this folder — one line per change: `[YYYY-MM-DD] What changed and why`.

## Cases
This skill owns a `cases/` directory. At birth it holds one baseline pair: `cases/baseline/input.md` (the frozen sample input) and `cases/baseline/output-baseline.md` (Claude's no-skill output on that input). The with-skill test re-runs the same `input.md` and is judged against the baseline. Annealing adds a `cases/<name>/` for each failure it fixes.
