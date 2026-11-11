#!/usr/bin/env python3
"""
Milo Cognitive Core (Cortex) — Main User CLI & Assistant Engine
Part of MiloOS. Built for Arch Linux & Hyprland.
Integrates Familiarity Gatekeeping, Web Exploration, Real-Time Token Streaming,
and Topic Lifecycle Management.
"""

import sys
import os
import time
import argparse
from pathlib import Path

# Ensure access to milo venv and local modules
if "/usr/lib/python3.14/site-packages" not in sys.path:
    sys.path.append("/usr/lib/python3.14/site-packages")
CORTEX_DIR = Path.home() / ".local" / "share" / "milo" / "cortex"
sys.path.insert(0, str(CORTEX_DIR))
sys.path.insert(0, str(Path.home() / ".local/share/milo/brain"))

from db import get_db_connection
from gatekeeper import CortexGatekeeper
from web_searcher import CortexWebSearcher
from consolidator import CortexSleepConsolidator
from generator import CortexGenerator
from engine import MiloBrainEngine

CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def ask_question(query: str, force_aware: bool = False):
    start_t = time.perf_counter()
    gk = CortexGatekeeper()
    searcher = CortexWebSearcher()
    generator = CortexGenerator()

    # 0. Desktop Context Awareness Inspection
    from context_inspector import capture_desktop_context, should_trigger_awareness
    desktop_context = ""
    if should_trigger_awareness(query, force_aware):
        ctx = capture_desktop_context()
        if ctx.get("has_context"):
            win_info = ctx["window"].get("class", "Desktop")
            sel_src = ctx["selection"]["source"]
            sel_len = ctx["selection"].get("length", 0)
            sel_info = f"{sel_src} ({sel_len} chars)" if sel_len else "window context"
            print(f"\n{BLUE}{BOLD}👁️  AWARENESS MODE{RESET}  ›  Active: {CYAN}{win_info}{RESET}  |  Captured: {YELLOW}{sel_info}{RESET}")
            desktop_context = ctx["formatted_context"]

    decision = gk.evaluate(query)
    eval_ms = (time.perf_counter() - start_t) * 1000

    print()
    if decision.mode == "MASTERED":
        status_tag = f"{GREEN}{BOLD}⚡ LOCAL MEMORY (Mastered {decision.encounter_count}/6){RESET}"
        network_tag = f"{DIM}[Offline Recall]{RESET}"
    else:
        status_tag = f"{YELLOW}{BOLD}🌐 WEB EXPLORER (Learning {decision.encounter_count}/6){RESET}"
        network_tag = f"{DIM}[Web Crawl Staged]{RESET}"

    topic_display = decision.topic_name.replace("_", " ")
    print(f"{CYAN}{BOLD}🧠 MILO CORTEX{RESET}  ›  {status_tag} {network_tag}")
    print(f"  {DIM}Topic:{RESET} {MAGENTA}{topic_display}{RESET}  {DIM}| Familiarity Score:{RESET} {CYAN}{decision.similarity:.2f}{RESET}  {DIM}| Routing:{RESET} {eval_ms:.1f}ms\n")

    # 1. Mastered Mode: 100% Offline Local Recall
    if decision.mode == "MASTERED":
        combined_facts = decision.context_text
        if desktop_context:
            combined_facts = f"{combined_facts}\n\n[Active Desktop Context]:\n{desktop_context}" if combined_facts else desktop_context

        if combined_facts:
            print(f"{BOLD}Answer:{RESET}\n")
            for token in generator.stream_synthesize(query=query, mode="MASTERED", context_facts=combined_facts):
                sys.stdout.write(token)
                sys.stdout.flush()
            print("\n")

            if decision.context_text:
                print(f"{DIM}Ground-truth memory facts:{RESET}")
                for line in decision.context_text.splitlines():
                    if line.startswith("•"):
                        parts = line[1:].strip().split("→")
                        if len(parts) == 2:
                            print(f"  • {CYAN}{parts[0].strip()}{RESET} → {BOLD}{parts[1].strip()}{RESET}")
                        else:
                            print(f"  {line}")
        else:
            print(f"  {DIM}Topic is mastered, but no atomic facts recorded yet.{RESET}")

        card_path = Path.home() / "MiloNotes" / "Cortex" / f"{decision.topic_name}.md"
        if card_path.exists():
            print(f"\n  {DIM}Vault Card:{RESET} {CYAN}{card_path}{RESET}")

    # 2. Explorer Mode: Local Knowledge First & Web Fallback
    else:
        from local_knowledge import LocalKnowledgeEngine
        local_eng = LocalKnowledgeEngine()

        web_text = ""
        results = []
        local_match = None

        # 2a. Try Local Knowledge First (Vault, CLI --help, Manpages)
        if not desktop_context:
            local_match = local_eng.resolve(query)

        if local_match:
            src = local_match["source"]
            title = local_match["title"]
            lat = local_match["latency_ms"]
            print(f"{GREEN}{BOLD}📚 LOCAL KNOWLEDGE{RESET}  ›  Source: {CYAN}{src}{RESET} ({title}) {DIM}[{lat:.1f}ms]{RESET}\n")

            combined_context = f"[Local System Knowledge ({src}: {title})]:\n{local_match['content']}"
            if desktop_context:
                combined_context = f"{desktop_context}\n\n{combined_context}"

            # Stage finding into DB as an atomic snippet so night consolidator remembers it!
            try:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO daily_staging (topic_id, source_url, snippet)
                    VALUES (?, ?, ?)
                """, (decision.topic_id, f"local://{src}/{title}", local_match["content"]))
                conn.commit()
                conn.close()
            except Exception:
                pass

            print(f"{BOLD}Answer ({lat:.0f}ms):{RESET}\n")
            for token in generator.stream_synthesize(query=query, mode="EXPLORER", context_facts=combined_context):
                sys.stdout.write(token)
                sys.stdout.flush()
            print("\n")
            print(f"{DIM}Reference:{RESET} {CYAN}{local_match['path']}{RESET}")
            print(f"\n{DIM}✔ Staged into daily buffer for 3:00 AM consolidation.{RESET}")

        # 2b. Web Fallback (if no local match or if desktop context only)
        else:
            if not desktop_context:
                print(f"{DIM}Gathering web context for unfamiliar topic...{RESET}")
                web_start = time.perf_counter()
                results = searcher.search(query, max_results=3)
                web_ms = (time.perf_counter() - web_start) * 1000
                if results:
                    searcher.stage_findings(decision.topic_id, query, results)
                    web_text = "\n".join([f"[{r['title']}]: {r['snippet']}" for r in results])
                    print(f"{BOLD}Answer ({web_ms:.0f}ms):{RESET}\n")
                else:
                    print(f"{BOLD}Answer:{RESET}\n")
            else:
                print(f"{BOLD}Answer:{RESET}\n")

            for token in generator.stream_synthesize(query=query, mode="EXPLORER", context_facts=desktop_context, web_snippets=web_text):
                sys.stdout.write(token)
                sys.stdout.flush()
            print("\n")

            if results:
                print(f"{DIM}Web Sources:{RESET}")
                for idx, r in enumerate(results, 1):
                    print(f"  {CYAN}[{idx}] {r['title']}{RESET}  {DIM}({r['url']}){RESET}")
                print(f"\n{DIM}✔ Staged into daily buffer for 3:00 AM consolidation.{RESET}")

    total_ms = (time.perf_counter() - start_t) * 1000
    print(f"\n{DIM}Total time: {total_ms:.1f}ms{RESET}\n")


def show_status():
    conn = get_db_connection()
    cur = conn.cursor()

    print(f"\n{CYAN}{BOLD}🧠 MILO COGNITIVE CORE (CORTEX) — SYSTEM STATUS{RESET}\n")

    cur.execute("SELECT COUNT(*) as total, SUM(is_mastered) as mastered FROM topics")
    row = cur.fetchone()
    total = row["total"] or 0
    mastered = row["mastered"] or 0
    learning = total - mastered

    cur.execute("SELECT COUNT(*) as staging_count FROM daily_staging")
    staging_count = cur.fetchone()["staging_count"]

    cur.execute("SELECT COUNT(*) as facts_count FROM atomic_facts")
    facts_count = cur.fetchone()["facts_count"]

    print(f"  • Total Topics Tracked:      {BOLD}{total}{RESET} ({GREEN}{mastered} Mastered{RESET}, {YELLOW}{learning} Learning{RESET})")
    print(f"  • Permanent Atomic Facts:    {BOLD}{facts_count}{RESET} baked in memory")
    print(f"  • Daily Staged Web Snippets: {BOLD}{staging_count}{RESET} awaiting nightly consolidation\n")

    cur.execute("""
        SELECT name, encounter_count, is_mastered, last_accessed 
        FROM topics 
        ORDER BY last_accessed DESC LIMIT 10
    """)
    recent = cur.fetchall()
    if recent:
        print(f"{BOLD}Active Topics:{RESET}")
        for r in recent:
            badge = f"{GREEN}[Mastered 6/6]{RESET}" if r["is_mastered"] else f"{YELLOW}[Learning {r['encounter_count']}/6]{RESET}"
            print(f"  • {badge} {CYAN}{r['name'].replace('_', ' ')}{RESET} {DIM}(Last: {r['last_accessed']}){RESET}")
    print()
    conn.close()


def list_topics():
    conn = get_db_connection()
    cur = conn.cursor()

    print(f"\n{CYAN}{BOLD}🧠 MILO CORTEX — ALL KNOWLEDGE TOPICS{RESET}\n")

    cur.execute("""
        SELECT id, name, encounter_count, is_mastered, is_dynamic, ttl_days, last_accessed 
        FROM topics 
        ORDER BY is_mastered DESC, encounter_count DESC
    """)
    topics = cur.fetchall()
    if not topics:
        print("  No topics recorded yet. Ask a question with `milo-ask <query>` to begin!")
        conn.close()
        return

    for t in topics:
        status = f"{GREEN}Mastered (Offline){RESET}" if t["is_mastered"] else f"{YELLOW}Learning ({t['encounter_count']}/6){RESET}"
        ttl_label = f"Dynamic ({t['ttl_days']}d TTL)" if t["is_dynamic"] else "Static (180d TTL)"

        print(f"  {BOLD}ID {t['id']}:{RESET} {CYAN}{t['name'].replace('_', ' ')}{RESET}  [{status}]  {DIM}{ttl_label}{RESET}")

        cur.execute("SELECT attribute, fact_value FROM atomic_facts WHERE topic_id = ? LIMIT 2", (t["id"],))
        facts = cur.fetchall()
        for f in facts:
            print(f"      {DIM}• {f['attribute']}:{RESET} {f['fact_value']}")
        print()

    conn.close()


def forget_topic(target: str):
    conn = get_db_connection()
    cur = conn.cursor()

    # Match by ID or Name
    if target.isdigit():
        cur.execute("SELECT id, name FROM topics WHERE id = ?", (int(target),))
    else:
        cur.execute("SELECT id, name FROM topics WHERE name LIKE ? OR name LIKE ?", (f"%{target}%", f"%{target.replace(' ', '_')}%"))

    row = cur.fetchone()
    if not row:
        print(f"\n{YELLOW}No topic matching '{target}' found.{RESET}\n")
        conn.close()
        return

    topic_id = row["id"]
    topic_name = row["name"]

    cur.execute("DELETE FROM daily_staging WHERE topic_id = ?", (topic_id,))
    cur.execute("DELETE FROM atomic_facts WHERE topic_id = ?", (topic_id,))
    cur.execute("DELETE FROM query_history WHERE topic_id = ?", (topic_id,))
    cur.execute("DELETE FROM topics WHERE id = ?", (topic_id,))
    conn.commit()
    conn.close()

    card_path = Path.home() / "MiloNotes" / "Cortex" / f"{topic_name}.md"
    if card_path.exists():
        card_path.unlink()

    print(f"\n{GREEN}✔ Topic '{topic_name.replace('_', ' ')}' (ID: {topic_id}) has been forgotten.{RESET}")
    print(f"  {DIM}Milo will re-explore and learn this topic from scratch next time.{RESET}\n")


def set_dynamic_topic(target: str):
    conn = get_db_connection()
    cur = conn.cursor()

    if target.isdigit():
        cur.execute("SELECT id, name, is_dynamic FROM topics WHERE id = ?", (int(target),))
    else:
        cur.execute("SELECT id, name, is_dynamic FROM topics WHERE name LIKE ?", (f"%{target}%",))

    row = cur.fetchone()
    if not row:
        print(f"\n{YELLOW}No topic matching '{target}' found.{RESET}\n")
        conn.close()
        return

    topic_id = row["id"]
    topic_name = row["name"]
    new_dynamic = 1 - int(row["is_dynamic"])
    new_ttl = 14 if new_dynamic else 180

    cur.execute("UPDATE topics SET is_dynamic = ?, ttl_days = ? WHERE id = ?", (new_dynamic, new_ttl, topic_id))
    conn.commit()
    conn.close()

    state_str = "Dynamic (14-day auto-refresh TTL)" if new_dynamic else "Static (180-day permanent memory)"
    print(f"\n{GREEN}✔ Topic '{topic_name.replace('_', ' ')}' is now set to {state_str}.{RESET}\n")


def run_consolidation():
    consolidator = CortexSleepConsolidator()
    report = consolidator.run_daily_consolidation()
    print(f"\n{GREEN}✔ Sleep Consolidation Completed Successfully!{RESET}")
    print(f"  • Topics Consolidated: {report['topics_consolidated']}")
    print(f"  • Atomic Facts Baked:  {report['facts_extracted']}")
    print(f"  • Vault Chunks Synced: {report['indexed_chunks']}\n")


def main():
    parser = argparse.ArgumentParser(description="Milo Cognitive Core (Cortex) CLI")
    subparsers = parser.add_subparsers(dest="command")

    ask_p = subparsers.add_parser("ask", help="Ask a question")
    ask_p.add_argument("-a", "--aware", action="store_true", help="Force desktop context awareness capture")
    ask_p.add_argument("query", nargs="+", help="Query string")

    subparsers.add_parser("status", help="Show cortex cognitive memory status")
    subparsers.add_parser("topics", help="List all topics and their memory states")
    subparsers.add_parser("consolidate", help="Trigger manual 24-hr sleep consolidation")

    daemon_p = subparsers.add_parser("daemon", help="Manage resident LLM daemon (status, start, stop, restart, ping)")
    daemon_p.add_argument("action", nargs="?", default="status", choices=["start", "stop", "restart", "enable", "disable", "status", "ping", "logs"])

    forget_p = subparsers.add_parser("forget", help="Erase a topic from memory to re-learn it")
    forget_p.add_argument("topic", help="Topic ID or name to erase")

    dynamic_p = subparsers.add_parser("dynamic", help="Toggle dynamic short TTL for a topic")
    dynamic_p.add_argument("topic", help="Topic ID or name to toggle")

    mode_p = subparsers.add_parser("mode", help="Manage hybrid intelligence mode (auto, online, offline)")
    mode_p.add_argument("action", nargs="?", default="status", choices=["status", "get", "set", "toggle"])
    mode_p.add_argument("value", nargs="?", default="auto", choices=["auto", "online", "offline"])

    if len(sys.argv) == 1:
        parser.print_help()
        return

    # If first argument is not a subcommand, treat it as a query directly
    if sys.argv[1] not in ["ask", "status", "topics", "consolidate", "forget", "dynamic", "daemon", "mode", "-h", "--help"]:
        force_aware = False
        remaining = sys.argv[1:]
        if remaining and remaining[0] in ["-a", "--aware"]:
            force_aware = True
            remaining = remaining[1:]
        query = " ".join(remaining)
        ask_question(query, force_aware=force_aware)
        return

    args = parser.parse_args()
    if args.command == "ask":
        ask_question(" ".join(args.query), force_aware=args.aware)
    elif args.command == "status":
        show_status()
    elif args.command == "topics":
        list_topics()
    elif args.command == "consolidate":
        run_consolidation()
    elif args.command == "daemon":
        import subprocess
        subprocess.run([str(Path.home() / ".local/bin/milo-cortex-daemon"), args.action])
    elif args.command == "forget":
        forget_topic(args.topic)
    elif args.command == "dynamic":
        set_dynamic_topic(args.topic)
    elif args.command == "mode":
        from intelligence_router import get_status, set_mode, toggle_mode, get_mode
        if args.action == "status":
            import json
            print(json.dumps(get_status(), indent=2))
        elif args.action == "get":
            print(get_mode())
        elif args.action == "set":
            m = set_mode(args.value)
            print(f"{GREEN}✔ Intelligence mode set to: {BOLD}{m}{RESET}")
        elif args.action == "toggle":
            m = toggle_mode()
            print(f"{GREEN}✔ Toggled intelligence mode to: {BOLD}{m}{RESET}")


if __name__ == "__main__":
    main()
