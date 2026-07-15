# Script efficiency review

Run this checklist **inline** against every script in a script-backed skill at graduation. It is not
a standing sub-agent — you read it and apply it in the current session. Mindset: assume every API
call costs money and every unhandled error will happen at real scale.

Read each script end to end, then walk the six dimensions below. Emit one finding per issue, each
severity-ranked. A finding is only useful if it names all four parts:

- **Location** — file + the line(s) or function.
- **Issue** — what the code does now.
- **Why it matters** — the concrete cost at real scale (money, latency, quota, a silent-truncation bug).
- **Fix** — the specific change to make, not "consider improving".

## Severity rubric

| Severity | Criteria | Effect on graduation |
|---|---|---|
| **CRITICAL** | Will break at real scale or burn money/quota fast — N+1 over a large list, no backoff against a rate-limited API, unbounded fetch that silently truncates. | **BLOCKS graduation** until fixed. |
| **HIGH** | Material waste that works today but degrades under load or volume. | Report prominently; fix before heavy use. Does not block. |
| **MEDIUM / LOW** | Suboptimal-but-safe patterns, small optimizations, style. | Improvement notes. Builder decides. |

Only CRITICAL findings block. Everything else is reported; the builder chooses whether to act.

## The six dimensions

### 1. Batching
- **Look for:** per-item API calls a batch endpoint could collapse — the classic `for id in ids: get(id)`.
- **Why it matters:** N items = N calls vs 1. Batching is the proven ~90% cost/latency win.
- **Example finding (CRITICAL):** `report.py:44` loops `api.get_ad(ad_id)` over every ad — 800 ads = 800 calls. Fix: replace with one `api.get_ads(ad_ids)` batch call.

### 2. N+1 patterns
- **Look for:** fetch a list, then fetch each item in the list separately.
- **Why it matters:** one list call plus N detail calls where a single call with the fields embedded would do; cost and latency scale with the list.
- **Example finding (CRITICAL):** `sync.py:60` lists campaigns then fetches each campaign's stats in a loop. Fix: request stats in the list call's field set, or batch the detail fetch.

### 3. Over-fetching
- **Look for:** pulling full objects, all fields, or all rows when a filter or projection exists.
- **Why it matters:** larger payloads, slower parses, and on metered APIs a bigger bill for data you drop.
- **Example finding (HIGH):** `pull.py:22` selects `*` then uses two columns. Fix: request only the two fields (projection / `fields=` param) and filter server-side.

### 4. Pagination
- **Look for:** unbounded fetches, missing cursor/next-page handling, or fetching all pages when one suffices.
- **Why it matters:** assuming everything fits in one response silently truncates data; blindly paging to the end burns quota when the caller needs only the first page.
- **Example finding (CRITICAL):** `list.py:15` reads `response["items"]` with no cursor loop — silently drops everything past page one. Fix: follow the `next_cursor` until exhausted, or bound to the pages actually needed.

### 5. Rate limiting & backoff
- **Look for:** no retry strategy, tight loops firing at an API, missing exponential backoff and jitter.
- **Why it matters:** rapid-fire calls trip 429s and can earn a temporary ban; no backoff turns a transient blip into a hard failure.
- **Example finding (CRITICAL):** `fetch.py:30` calls in a loop with no delay and no retry. Fix: wrap calls in bounded exponential backoff with jitter on 429/5xx (e.g. `sleep(base * 2**attempt + random)`, max N attempts).

### 6. Cost / quota awareness
- **Look for:** an expensive model or endpoint where a cheap one suffices; no caching of stable results; no ceiling on bulk operations.
- **Why it matters:** paying premium rates for commodity work, or recomputing results that never change, compounds every run.
- **Example finding (HIGH):** `classify.py:12` calls the top-tier model to label fixed categories. Fix: drop to the cheap model for this task and cache the label for inputs that repeat.

## Reporting

Group findings by severity, CRITICAL first. If any CRITICAL exists, state plainly that graduation is
blocked and list the exact fixes required to unblock. If none, note the skill passes the efficiency
gate and list any HIGH/MEDIUM/LOW notes for the builder to weigh. Procedure-only skills never reach
this file — see the SKILL's skip rule.
