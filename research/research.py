#!/usr/bin/env python3
"""SEED-driven research loop.

The script is intentionally source-first: it discovers search candidates from
SEED and existing event entities, fetches pages, extracts event-like records,
and writes only records supported by a source URL. It does not require an LLM.
"""
from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

SEED = Path("research/seed.yaml")
EVENTS = Path("data/events.jsonl")
OUT = Path("research/runs/latest.json")


def yaml_queries(text: str) -> list[str]:
    out = []
    in_queries = False
    for line in text.splitlines():
        if line.strip() == "queries:":
            in_queries = True
            continue
        if in_queries:
            m = re.match(r"\s+-\s+['\"]?(.*?)['\"]?$", line)
            if m:
                out.append(m.group(1).strip("'\""))
            elif line and not line.startswith(" "):
                in_queries = False
    return out


def load_events() -> list[dict]:
    if not EVENTS.exists():
        return []
    rows = []
    for line in EVENTS.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def search_urls(query: str) -> list[str]:
    """Use an optional search endpoint supplied by the AW runtime.

    In GitHub Actions, SEARCH_ENDPOINT can point to a small search service that
    returns JSON: {"urls": ["https://..."]}. Without it, the loop still emits
    deterministic query seeds for the next agent run.
    """
    endpoint = os.environ.get("SEARCH_ENDPOINT")
    if not endpoint:
        return []
    url = endpoint + ("&" if "?" in endpoint else "?") + urllib.parse.urlencode({"q": query})
    req = urllib.request.Request(url, headers={"User-Agent": "give-me-vegetable-research/1"})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read().decode("utf-8"))
    return [u for u in data.get("urls", []) if isinstance(u, str) and u.startswith("http")]


def main() -> None:
    seed_text = SEED.read_text(encoding="utf-8")
    base_queries = yaml_queries(seed_text)
    events = load_events()
    entities = set()
    for row in events:
        for key in ("place", "local_implementer", "pref"):
            value = row.get(key)
            if value:
                entities.add(str(value))

    queries = list(dict.fromkeys(base_queries + [f'"ギブミーベジタブル" {e}' for e in sorted(entities)]))
    urls: list[str] = []
    for q in queries:
        try:
            urls.extend(search_urls(q))
        except Exception as exc:
            print(f"search failed: {q}: {exc}")

    result = {
        "date": date.today().isoformat(),
        "seed": str(SEED),
        "queries": queries,
        "source_urls": list(dict.fromkeys(urls)),
        "existing_events": len(events),
        "status": "discover",
        "next": ["expand", "verify", "normalize", "dedupe", "append", "recurse"],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
