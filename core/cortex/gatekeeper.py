#!/usr/bin/env python3
"""
Milo Cognitive Core (Cortex) — Gatekeeper & Familiarity Engine
Evaluates incoming queries, tracks topic familiarity (the 6-encounter rule),
and gates between Online Web Exploration and Offline Local Mastery.
"""

import sys
import os
import re
import time
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict, Any, Set

# Ensure access to milo venv and milo-brain modules
if "/usr/lib/python3.14/site-packages" not in sys.path:
    sys.path.append("/usr/lib/python3.14/site-packages")
sys.path.insert(0, str(Path.home() / ".local/share/milo/brain"))
sys.path.insert(0, str(Path.home() / ".local/share/milo/cortex"))

import numpy as np
from engine import FastSemanticEncoder, NL_PREFIXES, STOP_WORDS
from db import get_db_connection

SIMILARITY_THRESHOLD = 0.20  # Hybrid score threshold for topic clustering
MASTERY_THRESHOLD = 6
RETRY_WINDOW_SECONDS = 90


@dataclass
class GatekeeperDecision:
    mode: str  # 'EXPLORER' (Web needed) or 'MASTERED' (Local only)
    topic_id: int
    topic_name: str
    encounter_count: int
    similarity: float
    is_mastered: bool
    is_retry: bool
    context_text: str  # Local atomic facts or notes if available


class CortexGatekeeper:
    def __init__(self):
        self.encoder = FastSemanticEncoder(dim=256)

    def clean_query(self, query: str) -> Tuple[str, List[str]]:
        raw = query.strip()
        cleaned = raw
        for pattern in NL_PREFIXES:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"[?!.,;]+$", "", cleaned).strip()

        words = re.findall(r"[a-zA-Z0-9_]+|[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)+", cleaned)
        keywords = [w.lower() for w in words if w.lower() not in STOP_WORDS]
        if not keywords:
            keywords = [w.lower() for w in words]
        return (cleaned if cleaned else raw), keywords

    def _pack_vector(self, vec: np.ndarray) -> bytes:
        return vec.astype(np.float32).tobytes()

    def _unpack_vector(self, blob: bytes) -> np.ndarray:
        return np.frombuffer(blob, dtype=np.float32)

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a < 1e-9 or norm_b < 1e-9:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    def _keyword_jaccard(self, kw1: List[str], kw2_str: str) -> float:
        s1 = set(kw1)
        s2 = set(re.findall(r"[a-z0-9]+", kw2_str.lower()))
        if not s1 or not s2:
            return 0.0
        inter = len(s1 & s2)
        # Szymkiewicz-Simpson overlap coefficient emphasizes shared core technical nouns
        return float(inter / min(len(s1), len(s2)))

    def _is_recent_retry(self, cur, query: str) -> bool:
        """Check if user asked a very similar query in the last 90s (indicates retry/dissatisfaction)."""
        cur.execute("""
            SELECT query, strftime('%s', 'now') - strftime('%s', timestamp) as diff
            FROM query_history
            WHERE diff <= ?
            ORDER BY id DESC LIMIT 1
        """, (RETRY_WINDOW_SECONDS,))
        row = cur.fetchone()
        if not row:
            return False

        last_query = row["query"]
        if query.strip().lower() == last_query.strip().lower():
            return True

        vec1 = self.encoder.encode(query)
        vec2 = self.encoder.encode(last_query)
        return self._cosine_similarity(vec1, vec2) > 0.82

    def _get_local_atomic_facts(self, cur, topic_id: int) -> str:
        """Retrieve compiled atomic facts and summary notes for this topic."""
        cur.execute("""
            SELECT entity, attribute, fact_value 
            FROM atomic_facts 
            WHERE topic_id = ?
            ORDER BY id DESC LIMIT 20
        """, (topic_id,))
        rows = cur.fetchall()
        if not rows:
            return ""

        lines = ["[Consolidated Local Memory]"]
        for r in rows:
            lines.append(f"• {r['entity']}: {r['attribute']} → {r['fact_value']}")
        return "\n".join(lines)

    def evaluate(self, query: str) -> GatekeeperDecision:
        cleaned_text, query_keywords = self.clean_query(query)
        q_vec = self.encoder.encode(cleaned_text)

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT id, name, embedding, encounter_count, is_mastered, ttl_days, last_accessed FROM topics")
        topics = cur.fetchall()

        best_topic = None
        best_score = -1.0

        for t in topics:
            t_vec = self._unpack_vector(t["embedding"])
            vec_sim = self._cosine_similarity(q_vec, t_vec)
            kw_sim = self._keyword_jaccard(query_keywords, t["name"])

            # Hybrid score: 60% semantic vector + 40% keyword overlap
            hybrid_score = (0.6 * vec_sim) + (0.4 * kw_sim)
            if hybrid_score > best_score:
                best_score = hybrid_score
                best_topic = t

        is_retry = self._is_recent_retry(cur, query)

        # 1. Existing Topic Match
        if best_topic is not None and best_score >= SIMILARITY_THRESHOLD:
            topic_id = best_topic["id"]
            topic_name = best_topic["name"]
            count = best_topic["encounter_count"]
            is_mastered = bool(best_topic["is_mastered"])

            # If not an immediate retry, increment encounter count
            if not is_retry:
                count += 1
                if count >= MASTERY_THRESHOLD:
                    is_mastered = True

                # Update centroid with rolling average
                old_vec = self._unpack_vector(best_topic["embedding"])
                alpha = 0.15
                new_vec = (1 - alpha) * old_vec + alpha * q_vec
                new_norm = np.linalg.norm(new_vec)
                if new_norm > 1e-9:
                    new_vec = new_vec / new_norm

                cur.execute("""
                    UPDATE topics 
                    SET encounter_count = ?, is_mastered = ?, embedding = ?, last_accessed = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (count, int(is_mastered), self._pack_vector(new_vec), topic_id))
                conn.commit()

            mode = "MASTERED" if is_mastered else "EXPLORER"
            local_context = self._get_local_atomic_facts(cur, topic_id)

            cur.execute("""
                INSERT INTO query_history (query, topic_id, mode, user_satisfied)
                VALUES (?, ?, ?, ?)
            """, (query, topic_id, mode.lower(), not is_retry))
            conn.commit()
            conn.close()

            return GatekeeperDecision(
                mode=mode,
                topic_id=topic_id,
                topic_name=topic_name,
                encounter_count=count,
                similarity=round(best_score, 3),
                is_mastered=is_mastered,
                is_retry=is_retry,
                context_text=local_context
            )

        # 2. Brand New Topic
        # Extract meaningful technical keywords for canonical topic name
        clean_kw = [k for k in query_keywords if len(k) > 2][:3]
        topic_name = "_".join(clean_kw).title() if clean_kw else f"Topic_{int(time.time())}"

        cur.execute("SELECT id FROM topics WHERE name = ?", (topic_name,))
        if cur.fetchone():
            topic_name = f"{topic_name}_{int(time.time()) % 1000}"

        cur.execute("""
            INSERT INTO topics (name, embedding, encounter_count, is_mastered)
            VALUES (?, ?, 1, 0)
        """, (topic_name, self._pack_vector(q_vec)))
        new_topic_id = cur.lastrowid

        cur.execute("""
            INSERT INTO query_history (query, topic_id, mode, user_satisfied)
            VALUES (?, ?, 'explorer', 1)
        """, (query, new_topic_id))

        conn.commit()
        conn.close()

        return GatekeeperDecision(
            mode="EXPLORER",
            topic_id=new_topic_id,
            topic_name=topic_name,
            encounter_count=1,
            similarity=round(best_score, 3) if best_score > 0 else 0.0,
            is_mastered=False,
            is_retry=False,
            context_text=""
        )


if __name__ == "__main__":
    gk = CortexGatekeeper()
    test_queries = [
        "How do I set up Btrfs subvolumes on Arch Linux?",
        "What are the best mount options for Btrfs SSD?",
        "Btrfs snapshot commands with snapper",
        "How to do Btrfs filesystem defragmentation?",
        "Btrfs send and receive backup tutorial",
        "How to check Btrfs disk space and allocate metadata?",
        "What are the best mount options for Btrfs SSD?"
    ]

    print("--- Testing Milo Cortex Gatekeeper (Hybrid Clustering) ---")
    for q in test_queries:
        dec = gk.evaluate(q)
        print(f"Q: '{q}'")
        print(f"  → Mode: {dec.mode} | Topic: {dec.topic_name} (ID: {dec.topic_id})")
        print(f"  → Count: {dec.encounter_count}/6 | Score: {dec.similarity} | Mastered: {dec.is_mastered}")
        print()
