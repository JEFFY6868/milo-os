#!/usr/bin/env python3
"""
Milo Cognitive Core (Cortex) — Interactive HUD Engine with Power Tools
Features:
  1. Real-time streaming with Warm Resident Daemon + Awareness Mode + Local Knowledge
  2. Auto command & code block extraction
  3. 1-Key Quick Action Runner:
     [c] Copy command/snippet to Wayland clipboard (wl-copy) + notify-send
     [x] Execute command live in shell with confirmation
     [s] Save solution directly as Markdown card in ~/MiloNotes/Cortex/ & index into Milo Brain
     [y/n] Immediate cognitive feedback loop (graduates topic familiarity in cortex.db)
"""

import sys
import os
import re
import tty
import termios
import select
import subprocess
import time
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

# Ensure access to cortex and brain
sys.path.insert(0, str(Path.home() / ".local/share/milo/cortex"))
sys.path.insert(0, str(Path.home() / ".local/share/milo/brain"))

from db import get_db_connection
from gatekeeper import CortexGatekeeper
from web_searcher import CortexWebSearcher
from generator import CortexGenerator
from context_inspector import capture_desktop_context, should_trigger_awareness
from local_knowledge import LocalKnowledgeEngine

CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def extract_command(text: str) -> Optional[str]:
    """Extract the primary executable bash command from answer text."""
    prose_words = {"is", "are", "used", "to", "can", "will", "should", "the", "this", "that", "means", "when", "does"}

    # 1. Look for markdown code blocks (```bash ... ``` or ``` ... ```)
    code_blocks = re.findall(r"```(?:bash|sh)?\s*\n(.*?)\n```", text, re.DOTALL)
    if code_blocks:
        candidate = code_blocks[0].strip()
        lines = [l for l in candidate.splitlines() if l.strip() and not l.strip().startswith("#")]
        if lines:
            return lines[0].strip().lstrip("$ ")

    # 2. Look for inline backticks with shell commands (`btrfs ...`, `pacman ...`)
    backticks = re.findall(r"`([^`\n]+)`", text)
    for b in backticks:
        b = b.strip().lstrip("$ ")
        words = b.split()
        first_w = words[0] if words else ""
        if first_w in {
            "btrfs", "pacman", "hyprctl", "systemctl", "ffmpeg", "journalctl",
            "git", "ip", "nmcli", "tar", "find", "grep", "sed", "awk", "curl",
            "chmod", "chown", "ss", "lsof", "foot", "kdenlive", "mpv", "grim",
            "slurp", "wl-copy", "wl-paste", "udisksctl", "mount", "umount", "lsblk",
            "sudo", "cat", "ls", "cd", "mkdir", "rm", "mv", "cp"
        }:
            # Don't match if it contains obvious English prose
            w_set = set(w.lower() for w in words)
            if not w_set.intersection(prose_words):
                return b

    # 3. Look for command words or sudo anywhere in a line
    for line in text.splitlines():
        line_clean = line.strip()
        if line_clean.startswith("$ "):
            cmd_part = line_clean[2:].strip()
            if cmd_part:
                return cmd_part

        # Check if line contains sudo ...
        sudo_m = re.search(r"\b(sudo\s+[a-zA-Z0-9_\-\.\/@ ]+)", line_clean)
        if sudo_m:
            raw_cmd = sudo_m.group(1).rstrip(". ")
            clean_cmd = re.split(r"\s+(?:to|for|and|then|in|which|because|is)\s+", raw_cmd, flags=re.IGNORECASE)[0]
            words = set(clean_cmd.lower().split())
            if not words.intersection(prose_words):
                return clean_cmd.strip()

        # Check if line starts with known command with flags or subcommands
        parts = line_clean.split()
        if parts:
            first_w = parts[0].lstrip("$")
            if first_w in {
                "sudo", "btrfs", "pacman", "hyprctl", "systemctl", "ffmpeg",
                "git", "ip", "nmcli", "curl", "udisksctl", "mount", "umount"
            }:
                words = set(w.lower() for w in parts[1:])
                has_flags = any(w.startswith("-") for w in parts)
                if has_flags or (len(parts) <= 6 and not words.intersection(prose_words)):
                    return line_clean.rstrip(". ")

    return None


def get_single_keypress() -> str:
    """Read a single keypress from standard input without requiring Enter."""
    if not sys.stdin.isatty():
        return 'enter'

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        # Handle Enter / Ctrl+C
        if ch in ('\r', '\n'):
            return 'enter'
        if ch == '\x03':  # Ctrl+C
            return 'ctrl_c'
        return ch.lower()
    except Exception:
        return 'enter'
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def notify(title: str, message: str, icon: str = "dialog-information"):
    """Send desktop notification via notify-send."""
    try:
        subprocess.run(["notify-send", "-a", "Milo Cortex", "-i", icon, title, message], check=False)
    except Exception:
        pass


def execute_action_runner(topic_id: int, topic_name: str, query: str, answer_text: str):
    """Interactive post-answer action toolbar."""
    cmd = extract_command(answer_text)

    print(f"\n{CYAN}┌────────────────────────────────────────────────────────────────────────┐{RESET}")
    if cmd:
        print(f"{CYAN}│{RESET} {BOLD}⚡ ACTION BAR:{RESET} [{GREEN}c{RESET}] Copy Command  [{YELLOW}x{RESET}] Run Command  [{BLUE}s{RESET}] Save Note  [{MAGENTA}y{RESET}/{MAGENTA}n{RESET}] Feedback {CYAN}│{RESET}")
        print(f"{CYAN}│{RESET}   {DIM}Target:{RESET} {BOLD}{cmd[:60]}{RESET}{CYAN}{' ' * max(0, 62 - len(cmd[:60]))}│{RESET}")
    else:
        print(f"{CYAN}│{RESET} {BOLD}⚡ ACTION BAR:{RESET} [{GREEN}c{RESET}] Copy Answer   [{BLUE}s{RESET}] Save Note    [{MAGENTA}y{RESET}/{MAGENTA}n{RESET}] Feedback   [Enter] Next {CYAN}│{RESET}")
    print(f"{CYAN}└────────────────────────────────────────────────────────────────────────┘{RESET}")
    print(f"{DIM}Select an action (or press Enter to continue):{RESET} ", end="", flush=True)

    key = get_single_keypress()
    print(key if key != 'enter' else "")

    if key == 'ctrl_c':
        print()
        return

    # [c] Copy
    if key == 'c':
        payload = cmd if cmd else answer_text
        try:
            p = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE)
            p.communicate(input=payload.encode("utf-8"))
            print(f"\n{GREEN}✔ Copied to Wayland clipboard!{RESET}")
            notify("📋 Copied to Clipboard", payload[:50] + "..." if len(payload) > 50 else payload, "edit-copy")
        except Exception as e:
            print(f"\n{YELLOW}Could not copy to clipboard: {e}{RESET}")

    # [x] Execute
    elif key == 'x' and cmd:
        print(f"\n{YELLOW}{BOLD}Execute in shell:{RESET} {BOLD}{cmd}{RESET}")
        confirm = input(f"{DIM}Confirm run? [Y/n]: {RESET}").strip().lower()
        if confirm in ('', 'y', 'yes'):
            print(f"{DIM}Running...{RESET}\n")
            try:
                subprocess.run(cmd, shell=True)
                notify("⚡ Command Executed", cmd[:50], "utilities-terminal")
            except Exception as e:
                print(f"{YELLOW}Execution error: {e}{RESET}")
        else:
            print(f"{DIM}Execution cancelled.{RESET}")

    # [s] Save Note
    elif key == 's':
        cortex_notes_dir = Path.home() / "MiloNotes" / "Cortex"
        cortex_notes_dir.mkdir(parents=True, exist_ok=True)
        note_name = f"{topic_name}.md"
        note_path = cortex_notes_dir / note_name

        note_content = f"""---
title: "{topic_name.replace('_', ' ')}"
type: cortex_solution
created: "{time.strftime('%Y-%m-%d %H:%M:%S')}"
tags: [cortex, solution, linux]
---

# {topic_name.replace('_', ' ')}

**Query:** `{query}`

## Verified Solution
{answer_text}

"""
        if cmd:
            note_content += f"""### Extracted Command
```bash
{cmd}
```
"""

        try:
            note_path.write_text(note_content, encoding="utf-8")
            # Index into Milo Semantic Brain
            try:
                from engine import MiloBrainEngine
                eng = MiloBrainEngine()
                conn = eng.get_connection()
                eng.index_file(conn, note_path)
                conn.close()
            except Exception:
                pass

            print(f"\n{GREEN}✔ Saved to {note_path} and indexed in Milo Brain!{RESET}")
            notify("💾 Saved Note", f"Saved to ~/MiloNotes/Cortex/{note_name}", "document-save")
        except Exception as e:
            print(f"\n{YELLOW}Error saving note: {e}{RESET}")

    # [y] Positive Feedback
    elif key == 'y':
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("UPDATE topics SET encounter_count = encounter_count + 2 WHERE id = ?", (topic_id,))
            # Check if graduated
            cur.execute("SELECT encounter_count FROM topics WHERE id = ?", (topic_id,))
            new_count = cur.fetchone()[0]
            if new_count >= 6:
                cur.execute("UPDATE topics SET is_mastered = TRUE WHERE id = ?", (topic_id,))
            conn.commit()
            conn.close()
            status_msg = "Graduated to MASTERED! 🎓" if new_count >= 6 else f"Encounter count is now {new_count}/6"
            print(f"\n{GREEN}✔ Marked as helpful! {status_msg}{RESET}")
            notify("⭐ Cognitive Memory Updated", f"Topic '{topic_name.replace('_', ' ')}': {status_msg}", "starred")
        except Exception as e:
            print(f"\n{YELLOW}Error recording feedback: {e}{RESET}")

    # [n] Negative Feedback
    elif key == 'n':
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("UPDATE topics SET encounter_count = MAX(1, encounter_count - 1), is_mastered = FALSE WHERE id = ?", (topic_id,))
            conn.commit()
            conn.close()
            print(f"\n{YELLOW}✖ Feedback noted. Will seek alternate sources on next inquiry.{RESET}")
        except Exception as e:
            print(f"\n{YELLOW}Error recording feedback: {e}{RESET}")


def run_hud_query(query: str):
    """Execute query with streaming output, awareness detection, and power tools."""
    start_t = time.perf_counter()
    gk = CortexGatekeeper()
    searcher = CortexWebSearcher()
    generator = CortexGenerator()
    local_eng = LocalKnowledgeEngine()

    # 0. Desktop Context Awareness
    desktop_context = ""
    if should_trigger_awareness(query):
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
    print(f"  {DIM}Topic:{RESET} {MAGENTA}{topic_display}{RESET}  {DIM}| Familiarity:{RESET} {CYAN}{decision.similarity:.2f}{RESET}  {DIM}| Routing:{RESET} {eval_ms:.1f}ms\n")

    answer_chunks = []

    # 1. Mastered Mode
    if decision.mode == "MASTERED":
        combined_facts = decision.context_text
        if desktop_context:
            combined_facts = f"{combined_facts}\n\n[Active Desktop Context]:\n{desktop_context}" if combined_facts else desktop_context

        if combined_facts:
            print(f"{BOLD}Answer:{RESET}\n")
            for token in generator.stream_synthesize(query=query, mode="MASTERED", context_facts=combined_facts):
                sys.stdout.write(token)
                sys.stdout.flush()
                answer_chunks.append(token)
            print("\n")
        else:
            msg = "Topic is mastered, but no atomic facts recorded yet."
            print(f"  {DIM}{msg}{RESET}")
            answer_chunks.append(msg)

    # 2. Explorer Mode
    else:
        local_match = None
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

            print(f"{BOLD}Answer ({lat:.0f}ms):{RESET}\n")
            for token in generator.stream_synthesize(query=query, mode="EXPLORER", context_facts=combined_context):
                sys.stdout.write(token)
                sys.stdout.flush()
                answer_chunks.append(token)
            print("\n")
            print(f"{DIM}Reference:{RESET} {CYAN}{local_match['path']}{RESET}")
        else:
            web_text = ""
            results = []
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
                answer_chunks.append(token)
            print("\n")

    full_answer = "".join(answer_chunks).strip()
    total_ms = (time.perf_counter() - start_t) * 1000
    print(f"{DIM}Total latency: {total_ms:.1f}ms{RESET}")

    # Launch Interactive Post-Answer Action Runner
    if full_answer:
        execute_action_runner(decision.topic_id, decision.topic_name, query, full_answer)


def run_repl():
    """Interactive loop for the Foot floating HUD."""
    os.system("clear")
    print(f"{CYAN}{BOLD}╔══════════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{CYAN}{BOLD}║   🧠 MILO COGNITIVE CORTEX — INTERACTIVE HUD & COPILOT               ║{RESET}")
    print(f"{CYAN}{BOLD}║   Sub-40ms Resident LLM • Awareness Mode • 1-Key Power Tools         ║{RESET}")
    print(f"{CYAN}{BOLD}╚══════════════════════════════════════════════════════════════════════╝{RESET}\n")

    # Initial Desktop Context Snapshot
    try:
        ctx = capture_desktop_context()
        if ctx.get("has_context"):
            w = ctx["window"].get("class", "Desktop")
            t = ctx["window"].get("title", "")[:35]
            s = ctx["selection"].get("source", "none")
            l = ctx["selection"].get("length", 0)
            print(f"{BLUE}👁️  Active Context:{RESET} {BOLD}{w}{RESET} {BLUE}({DIM}{t}{RESET}{BLUE}) | {YELLOW}{s} ({l} chars){RESET}")
            print(f"{DIM}   (Tip: Type 'fix this' or 'explain' to inspect your selection){RESET}\n")
    except Exception:
        pass

    while True:
        try:
            query = input(f"{BOLD}Cortex › {RESET}").strip()
            if not query:
                continue
            if query.lower() in ("exit", "quit", "q"):
                print(f"\n{CYAN}Milo Cortex closed.{RESET}\n")
                break
            run_hud_query(query)
            print(f"\n{DIM}{'─' * 70}{RESET}\n")
        except (KeyboardInterrupt, EOFError):
            print(f"\n\n{CYAN}Milo Cortex closed.{RESET}\n")
            break


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_hud_query(" ".join(sys.argv[1:]))
    else:
        run_repl()
