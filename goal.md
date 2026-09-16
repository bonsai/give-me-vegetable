# Goal — Give Me Vegetable Research DB

## Objective

Build a source-first historical database of **ギブミーベジタブル / Give Me Vegetable** events across Japan.

The database should grow from a SEED-driven Agent Workflow (AW), while preserving the evidence needed to verify every event.

## Priority

**Source URL > flyer/image > event fields.**

An event should not become verified data unless a source URL is retained.

A flyer is treated as valuable evidence: collect the original flyer URL, PDF, OGP image, or page image whenever available.

## Target record

```json
{
  "subject": "ギブミーベジタブル",
  "pref": "",
  "place": "",
  "date": "YYYY-MM-DD",
  "local_implementer": "",
  "url": "",
  "img_url": ""
}
```

## Research loop

```text
SEED
  ↓
discover source URLs
  ↓
fetch pages / PDFs / archives
  ↓
extract event facts + flyer URLs
  ↓
verify against source
  ↓
normalize
  ↓
dedupe
  ↓
append JSONL
  ↓
use place / implementer / source as new seeds
  ↺
```

## Rules

- Preserve the original source URL.
- Prefer official event, organizer, venue, municipality, tourism association, and archival sources.
- Collect flyer/poster images whenever discoverable.
- Keep unknown fields empty rather than guessing.
- Exclude future events unless evidence establishes them as historical/current records according to the research cutoff.
- Deduplicate by date + place, while retaining useful source evidence.
- Never replace a source URL with a search-result URL.
- Treat SNS URLs, PDFs, archived pages, and flyers as evidence, not as disposable discovery artifacts.
- Newly discovered places, prefectures, organizers, venues, and source URLs become research seeds.

## Success condition

The project is successful when the DB can answer:

1. Where and when was each event held?
2. Who implemented it locally?
3. What is the strongest surviving source?
4. Is there a flyer/image documenting the event?
5. Can another researcher reproduce the record from the stored URLs?

The research output is not merely a list of events. It is an **auditable event history with provenance**.
