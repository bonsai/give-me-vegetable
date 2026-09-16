#!/usr/bin/env python3
"""SEED-driven, source-first research loop.

Discovery produces URLs; source inspection records page metadata and flyer
candidates. Facts are never fabricated: event rows require a source URL.
"""
from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

SEED = Path("research/seed.yaml")
EVENTS = Path("data/events.jsonl")
OUT = Path("research/runs/latest.json")


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images: list[str] = []
        self.og_image = ""
        self.title = ""
        self._title = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "img" and a.get("src"):
            self.images.append(a["src"])
        if tag == "meta" and a.get("property") == "og:image":
            self.og_image = a.get("content", "")
        if tag == "title":
            self._title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._title = False

    def handle_data(self, data):
        if self._title:
            self.title += data.strip()


def yaml_queries(text: str) -> list[str]:
    out, active = [], False
    for line in text.splitlines():
        if line.strip() == "queries:":
            active = True
            continue
        if active:
            m = re.match(r"\s+-\s+['\"]?(.*?)['\"]?$", line)
            if m:
                out.append(m.group(1).strip("'\""))
            elif line and not line.startswith(" "):
                active = False
    return out


def load_events() -> list[dict]:
    if not EVENTS.exists():
        return []
    rows = []
    for line in EVENTS.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return rows


def search_urls(query: str) -> list[str]:
    endpoint = os.environ.get("SEARCH_ENDPOINT")
    if not endpoint:
        return []
    url = endpoint + ("&" if "?" in endpoint else "?") + urllib.parse.urlencode({"q": query})
    req = urllib.request.Request(url, headers={"User-Agent": "give-me-vegetable-research/2"})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read().decode("utf-8"))
    return [u for u in data.get("urls", []) if isinstance(u, str) and u.startswith("http")]


def inspect_source(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "give-me-vegetable-research/2"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            final_url = r.geturl()
            content_type = r.headers.get("Content-Type", "")
            body = r.read(2_000_000)
        result = {"url": final_url, "content_type": content_type, "flyer_urls": [], "title": ""}
        if "html" in content_type or not content_type:
            parser = PageParser()
            parser.feed(body.decode("utf-8", errors="ignore"))
            base = final_url
            candidates = ([parser.og_image] if parser.og_image else []) + parser.images
            result["flyer_urls"] = list(dict.fromkeys(urllib.parse.urljoin(base, u) for u in candidates))
            result["title"] = parser.title
        elif "pdf" in content_type or final_url.lower().endswith(".pdf"):
            result["flyer_urls"] = [final_url]
        return result
    except Exception as exc:
        return {"url": url, "error": str(exc), "flyer_urls": []}


def main() -> None:
    seed_text = SEED.read_text(encoding="utf-8")
    base_queries = yaml_queries(seed_text)
    events = load_events()
    entities = sorted({str(row[k]) for row in events for k in ("place", "local_implementer", "pref") if row.get(k)})
    queries = list(dict.fromkeys(base_queries + [f'"ギブミーベジタブル" {e}' for e in entities]))

    urls: list[str] = []
    for query in queries:
        try:
            urls.extend(search_urls(query))
        except Exception as exc:
            print(f"search failed: {query}: {exc}")
    urls = list(dict.fromkeys(urls))

    sources = [inspect_source(url) for url in urls]
    flyer_urls = list(dict.fromkeys(u for source in sources for u in source.get("flyer_urls", []) if u))
    result = {
        "date": date.today().isoformat(),
        "seed": str(SEED),
        "queries": queries,
        "source_urls": urls,
        "flyer_urls": flyer_urls,
        "sources": sources,
        "existing_events": len(events),
        "status": "source_inspection",
        "next": ["extract", "verify", "normalize", "dedupe", "append", "recurse"],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"queries": len(queries), "sources": len(urls), "flyers": len(flyer_urls)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
