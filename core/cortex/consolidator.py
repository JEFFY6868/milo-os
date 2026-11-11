#!/usr/bin/env python3
"""
Milo Cognitive Core (Cortex) — 24-Hour Nocturnal Sleep Consolidator
Part of MiloOS. Built for Arch Linux & Hyprland.
Consolidates raw daily web logs into permanent atomic facts, writes human-readable
Markdown cards to ~/MiloNotes/Cortex/, and syncs into the Milo Brain index.
"""

import sys
import os
import re
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Ensure access to milo venv and milo-brain modules
if "/usr/lib/python3.14/site-packages" not in sys.path:
    sys.path.append("/usr/lib/python3.14/site-packages")
sys.path.insert(0, str(Path.home() / ".local/share/milo/brain"))
sys.path.insert(0, str(Path.home() / ".local/share/milo/cortex"))

from db import get_db_connection
from engine import MiloBrainEngine

CORTEX_NOTES_DIR = Path.home() / "MiloNotes" / "Cortex"


class CortexSleepConsolidator:
    def __init__(self):
        CORTEX_NOTES_DIR.mkdir(parents=True, exist_ok=True)
        self.brain = MiloBrainEngine()

    def _extract_fact_triples_heuristic(self, topic_name: str, snippets: List[str]) -> List[Tuple[str, str, str]]:
        """Fallback regex-based fact extraction."""
        triples = []
        clean_topic = topic_name.replace("_", " ")

        for text in snippets:
            lines = text.splitlines()
            for line in lines:
                line = line.strip()
                if not line or line.startswith("[") or line.startswith("http"):
                    continue

                m = re.match(r"^([A-Za-z0-9_-]+(?:\s+[A-Za-z0-9_-]+){0,3})[:=—\-]\s+(.+)$", line)
                if m:
                    attr = m.group(1).strip()
                    val = m.group(2).strip()
                    if len(val) > 4 and len(val) < 200:
                        triples.append((clean_topic, attr, val))
                        continue

                cmd_match = re.search(r"(`[^`]+`|\$[A-Za-z0-9_\s/-]+|sudo\s+[a-z0-9_\s/-]+)", line)
                if cmd_match:
                    triples.append((clean_topic, "command", cmd_match.group(1).strip("`")))

        unique_triples = []
        seen = set()
        for t in triples:
            key = (t[0].lower(), t[1].lower(), t[2].lower())
            if key not in seen:
                seen.add(key)
                unique_triples.append(t)

        return unique_triples[:10]

    def _extract_fact_triples(self, topic_name: str, snippets: List[str]) -> List[Tuple[str, str, str]]:
        """
        AI-powered distillation using local LLM with regex fallback.
        Extracts atomic fact triples: (Entity, Attribute, Value).
        """
        if not snippets:
            return []

        joined_snippets = "\n".join(snippets[:4])
        clean_topic = topic_name.replace("_", " ")
        prompt = f"""Topic: {clean_topic}
Web Findings:
{joined_snippets}

Extract 3 to 6 permanent, atomic factual triples in the exact format:
Entity | Attribute | Value
Example:
Btrfs | mount_option | compress=zstd:1,noatime
Only return the triples, one per line. No conversation."""

        try:
            from generator import CortexGenerator
            gen = CortexGenerator()
            raw_output = gen.synthesize(query="Extract facts", mode="MASTERED", context_facts=prompt)
            triples = []
            for line in raw_output.splitlines():
                parts = line.strip().split("|")
                if len(parts) == 3:
                    ent = parts[0].strip().strip("-*• ")
                    attr = parts[1].strip()
                    val = parts[2].strip()
                    if ent and attr and val:
                        triples.append((ent, attr, val))
            if triples:
                return triples[:8]
        except Exception:
            pass

        return self._extract_fact_triples_heuristic(topic_name, snippets)

    def consolidate_topic(self, cur, topic_id: int, topic_name: str) -> int:
        """Consolidate staged records for a specific topic."""
        cur.execute("""
            SELECT id, query, raw_snippet, source_url 
            FROM daily_staging 
            WHERE topic_id = ?
        """, (topic_id,))
        rows = cur.fetchall()
        if not rows:
            return 0

        snippets = [r["raw_snippet"] for r in rows]
        sources = list({r["source_url"] for r in rows if r["source_url"]})

        # 1. Distill into Atomic Fact Triples
        triples = self._extract_fact_triples(topic_name, snippets)
        for entity, attr, val in triples:
            cur.execute("""
                INSERT INTO atomic_facts (topic_id, entity, attribute, fact_value)
                VALUES (?, ?, ?, ?)
            """, (topic_id, entity, attr, val))

        # 2. Write / Update Human-Readable Markdown Card
        card_file = CORTEX_NOTES_DIR / f"{topic_name}.md"
        cur.execute("SELECT encounter_count, is_mastered FROM topics WHERE id = ?", (topic_id,))
        t_row = cur.fetchone()
        count = t_row["encounter_count"] if t_row else 1
        is_mastered = bool(t_row["is_mastered"]) if t_row else False

        status_badge = "Mastered (Offline Ready)" if is_mastered else f"Learning ({count}/6)"
        timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S")

        md_content = [
            f"# 🧠 Milo Cortex: {topic_name.replace('_', ' ')}\n",
            f"> **Status**: {status_badge} | **Last Consolidated**: {timestamp_str}\n\n",
            "## 📌 Consolidated Atomic Facts\n"
        ]

        if triples:
            for entity, attr, val in triples:
                md_content.append(f"- **{attr.title()}**: `{val}`\n")
        else:
            md_content.append("- *General knowledge verified during daily exploration.*\n")

        if sources:
            md_content.append("\n## 🌐 References & Sources\n")
            for s in sources:
                md_content.append(f"- <{s}>\n")

        card_file.write_text("".join(md_content), encoding="utf-8")

        # 3. Purge Processed Staging Rows
        cur.execute("DELETE FROM daily_staging WHERE topic_id = ?", (topic_id,))

        return len(triples)

    def run_daily_consolidation(self) -> Dict[str, Any]:
        """Runs the complete 24-hr consolidation and TTL decay cycle."""
        print(f"[milo-cortex] Starting 24-Hour Sleep Consolidation Cycle at {time.strftime('%Y-%m-%d %H:%M:%S')}...")
        conn = get_db_connection()
        cur = conn.cursor()

        # Find all topics with pending daily staging data
        cur.execute("SELECT DISTINCT topic_id FROM daily_staging")
        pending_topics = [r["topic_id"] for r in cur.fetchall()]

        total_facts = 0
        consolidated_topics = 0

        for tid in pending_topics:
            cur.execute("SELECT name FROM topics WHERE id = ?", (tid,))
            t_row = cur.fetchone()
            if not t_row:
                continue
            topic_name = t_row["name"]
            facts_count = self.consolidate_topic(cur, tid, topic_name)
            total_facts += facts_count
            consolidated_topics += 1
            print(f"  • Consolidated topic '{topic_name}' → {facts_count} atomic facts baked into memory.")

        # TTL Decay Pass: re-open curiosity on stale dynamic topics
        cur.execute("""
            UPDATE topics 
            SET encounter_count = MAX(1, encounter_count - 3), is_mastered = 0
            WHERE is_dynamic = 1 AND (julianday('now') - julianday(last_accessed)) > ttl_days
        """)
        decayed = cur.rowcount
        if decayed > 0:
            print(f"  • Decayed {decayed} stale dynamic topics to re-enable web curiosity.")

        conn.commit()
        conn.close()

        # Re-index Cortex Markdown files into Milo Brain
        print("[milo-cortex] Syncing consolidated notes into Milo Semantic Brain...")
        indexed_count = 0
        with self.brain.get_connection() as b_conn:
            for md_file in CORTEX_NOTES_DIR.glob("*.md"):
                indexed_count += self.brain.index_file(b_conn, md_file)
            b_conn.commit()
        print(f"[milo-cortex] Done. Indexed {indexed_count} chunks in Milo Brain.")

        return {
            "topics_consolidated": consolidated_topics,
            "facts_extracted": total_facts,
            "topics_decayed": decayed,
            "indexed_chunks": indexed_count
        }


if __name__ == "__main__":
    consolidator = CortexSleepConsolidator()
    stats = consolidator.run_daily_consolidation()
    print(f"\n[Consolidation Report] {stats}")
