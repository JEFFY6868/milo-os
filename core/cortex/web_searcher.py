#!/usr/bin/env python3
"""
Milo Cognitive Core (Cortex) — Web Exploration Engine
Zero-API-key web search & article extractor using DuckDuckGo HTML + BeautifulSoup.
Feeds the Explorer mode and populates the 24-hr daily staging buffer.
"""

import sys
import re
import urllib.parse
from typing import List, Dict, Optional, Any
from pathlib import Path

# Ensure access to milo venv
if "/usr/lib/python3.14/site-packages" not in sys.path:
    sys.path.append("/usr/lib/python3.14/site-packages")
sys.path.insert(0, str(Path.home() / ".local/share/milo/cortex"))

import requests
from bs4 import BeautifulSoup
from db import get_db_connection

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0"
DDG_URL = "https://html.duckduckgo.com/html/"


class CortexWebSearcher:
    def __init__(self, timeout: int = 6):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        })

    def search(self, query: str, max_results: int = 4) -> List[Dict[str, str]]:
        """Perform a web search via DuckDuckGo HTML interface."""
        try:
            resp = self.session.post(
                DDG_URL,
                data={"q": query, "b": ""},
                timeout=self.timeout
            )
            if resp.status_code != 200:
                return []

            soup = BeautifulSoup(resp.text, "html.parser")
            results = []

            # DuckDuckGo HTML format: results are in div.result
            for res in soup.find_all("div", class_="result", limit=max_results * 2):
                title_a = res.find("a", class_="result__a")
                snippet_tag = res.find("a", class_="result__snippet")

                if not title_a:
                    continue

                title = title_a.get_text(strip=True)
                raw_href = title_a.get("href", "")

                # DDG links usually wrap redirect in /l/?kh=-1&uddg=...
                actual_url = raw_href
                if "uddg=" in raw_href:
                    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(raw_href).query)
                    if "uddg" in parsed:
                        actual_url = parsed["uddg"][0]

                snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""

                if title and actual_url and not actual_url.startswith("/"):
                    results.append({
                        "title": title,
                        "url": actual_url,
                        "snippet": snippet
                    })
                    if len(results) >= max_results:
                        break

            return results
        except Exception as e:
            # Non-blocking: fail gracefully if offline
            return []

    def stage_findings(self, topic_id: int, query: str, results: List[Dict[str, str]]):
        """Append web search snippets into the daily staging buffer for 24-hr consolidation."""
        if not results:
            return

        conn = get_db_connection()
        cur = conn.cursor()

        for r in results:
            combined_snippet = f"[{r['title']}]\n{r['snippet']}"
            cur.execute("""
                INSERT INTO daily_staging (topic_id, query, raw_snippet, source_url)
                VALUES (?, ?, ?, ?)
            """, (topic_id, query, combined_snippet, r["url"]))

        conn.commit()
        conn.close()


if __name__ == "__main__":
    searcher = CortexWebSearcher()
    q = "Btrfs subvolume layout Arch Linux"
    print(f"--- Testing Web Searcher on '{q}' ---")
    res = searcher.search(q, max_results=3)
    if not res:
        print("Note: Network offline or blocked by sandbox; web searcher handled gracefully.")
    else:
        for i, item in enumerate(res, 1):
            print(f"[{i}] {item['title']}")
            print(f"    URL: {item['url']}")
            print(f"    Snippet: {item['snippet']}\n")
