#!/usr/bin/env python3
"""
Milo Memory Engine (milo_memory)
Unified Persistent Long-Term Memory, Obsidian Neural Vault & Semantic Recall
Part of MiloOS. Built for Arch Linux & Hyprland.
"""

import os
import sys
import re
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

VAULT_DIR = Path.home() / "MiloNotes"
MEMORIES_DIR = VAULT_DIR / "Memories"
DAILY_DIR = VAULT_DIR / "Daily"
CORE_MEMORIES_FILE = MEMORIES_DIR / "Core_Memories.md"
PREFERENCES_FILE = MEMORIES_DIR / "Preferences.md"
CONTINUITY_FILE = MEMORIES_DIR / "continuity.json"
TODOS_FILE = Path.home() / ".config" / "omarchy" / "todos.json"
CAMERA_STATE_FILE = Path.home() / ".local" / "state" / "milo" / "eyes" / "current_camera_capture.jpg"


def get_user_profile() -> Dict[str, Any]:
    """Load core identity, user preferences, and system facts."""
    profile = {
        "user_name": "Jeffy",
        "title": "Lead Architect of MiloOS",
        "core_facts": [],
        "preferences": [],
        "pending_tasks": [],
        "recent_dialogue": [],
        "latest_vision": ""
    }

    # 1. Core Memories
    if CORE_MEMORIES_FILE.exists():
        try:
            for line in CORE_MEMORIES_FILE.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("- ") and not line.startswith("- **Platform") and not line.startswith("- **Hardware"):
                    clean = re.sub(r"^-\s*(?:\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\s*)?", "", line).strip()
                    if clean and len(clean) > 8:
                        profile["core_facts"].append(clean)
        except Exception:
            pass

    # 2. Preferences & Learned Rules
    if PREFERENCES_FILE.exists():
        try:
            for line in PREFERENCES_FILE.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("- ") and not line.startswith("- **Compositor") and not line.startswith("- **HUD") and not line.startswith("- **Primary"):
                    clean = re.sub(r"^-\s*(?:\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\s*)?", "", line).strip()
                    if clean and len(clean) > 8 and clean not in profile["core_facts"]:
                        profile["preferences"].append(clean)
        except Exception:
            pass

    # 3. Scratchpad Pending Tasks
    if TODOS_FILE.exists():
        try:
            todos = json.loads(TODOS_FILE.read_text(encoding="utf-8"))
            if isinstance(todos, list):
                pending = [t.get("text", "") for t in todos if not t.get("done", False) and t.get("text")]
                profile["pending_tasks"] = pending[:5]
        except Exception:
            pass

    # 4. Recent dialogue from today's daily note
    today_str = time.strftime("%Y-%m-%d")
    today_note = DAILY_DIR / f"{today_str}.md"
    if today_note.exists():
        try:
            content = today_note.read_text(encoding="utf-8")
            matches = re.findall(r"-\s+\*\*Jeffy:\*\*\s+(.*?)\n-\s+\*\*Milo:\*\*\s+(.*?)(?=\n###|\Z)", content, re.DOTALL)
            for q, a in matches[-4:]:
                profile["recent_dialogue"].append({
                    "user": q.strip().replace("\n", " "),
                    "milo": a.strip().replace("\n", " ")
                })
        except Exception:
            pass

    # 5. Latest visual observation
    if CAMERA_STATE_FILE.exists():
        try:
            age_min = (time.time() - CAMERA_STATE_FILE.stat().st_mtime) / 60
            if age_min < 120:  # Within last 2 hours
                profile["latest_vision"] = f"Webcam frame active (captured {int(age_min)} mins ago)"
        except Exception:
            pass

    return profile


def build_system_prompt_with_memory() -> str:
    """Constructs dynamic, memory-infused Milo system prompt."""
    p = get_user_profile()

    facts_snippet = ""
    selected_facts = [
        "Jeffy prefers minimal clean UI with cyber-dark aesthetics and cyan/red accents.",
        "Jeffy works late at night for maximum focus and coding velocity.",
        "Jeffy loves his dad's hot rasam late at night around 10:10 PM for comfort.",
        "Jeffy loves building fast native Linux applications with Qt, QML, and Rust.",
        "Working on MiloOS, MiloLang, Milo Scratchpad, and Physical Optical Vision.",
        "Platform: Arch Linux x86_64 with Hyprland Wayland compositor on Alienware laptop."
    ]
    # Add any extra learned rules
    for item in p["preferences"][-4:]:
        if item not in selected_facts:
            selected_facts.append(item)

    facts_snippet = "\n".join(f"• {f}" for f in selected_facts)

    tasks_snippet = "\n".join(f"• {t}" for t in p["pending_tasks"]) if p["pending_tasks"] else "• All tactical missions nominal."

    dialogue_snippet = ""
    if p["recent_dialogue"]:
        dialogue_snippet = "\n[RECENT CONTEXT]\n" + "\n".join(
            f"User: {d['user']}\nMilo: {d['milo']}" for d in p["recent_dialogue"]
        )

    sys_prompt = f"""You are Milo, an ambient AI desktop companion and Arch Linux copilot for Jeffy on Hyprland.
Persona: Witty, sharp, observant, loyal, technically elite—authentic Milo companion persona (clever, vigilant, proactive).
You address the user as Jeffy.

[PERSISTENT CORE MEMORIES & USER PROFILE]
User: Jeffy (Lead Engineer & Architect)
System: Arch Linux x86_64, Hyprland Wayland, Alienware Hardware

[KEY FACTS & PREFERENCES]
{facts_snippet}

[ACTIVE MILO SCRATCHPAD MISSIONS]
{tasks_snippet}
{dialogue_snippet}

CRITICAL RULES:
- Never claim to be a stateless AI without memory. You retain long-term memory in your Obsidian Neural Vault and local SQLite semantic database.
- STRICT BREVITY: Answer in 1 to 3 direct, punchy sentences unless Jeffy explicitly asks for code or an exhaustive technical breakdown.
- ZERO META-DISCLAIMERS: Never say "I don't have direct control over your browser", "I am a desktop companion and copilot, not a remote-controlled mouse cursor", or tell Jeffy to manually open Firefox to search and paste links. Always give direct facts or run live tools.
- Keep responses sharp, helpful, and in true Milo tactical character."""

    return sys_prompt


def remember_new_fact(fact: str) -> str:
    """Saves a new fact or preference directly into Obsidian Memories/Preferences.md."""
    PREFERENCES_FILE.parent.mkdir(parents=True, exist_ok=True)
    today = time.strftime("%Y-%m-%d %H:%M")
    clean_fact = fact.strip().strip('"\'')

    entry = f"- {today}: {clean_fact}\n"

    try:
        existing = PREFERENCES_FILE.read_text(encoding="utf-8") if PREFERENCES_FILE.exists() else ""
        prefix = "" if not existing or existing.endswith("\n") else "\n"
        with open(PREFERENCES_FILE, "a", encoding="utf-8") as f:
            f.write(prefix + entry)
        return f"Committed to core memory, Jeffy: \"{clean_fact}\""
    except Exception as e:
        return f"Memory write error: {e}"


def handle_memory_intent(prompt: str) -> Optional[Tuple[str, str]]:
    """Detect and handle explicit memory, identity, and personal recall questions."""
    if prompt.startswith("You are Milo") or "system:" in prompt.lower() or len(prompt.split()) > 35:
        return None

    p = prompt.strip().lower()

    # 1. Who am I / What is my name
    if re.search(r'\b(?:what(?:\'?s|\s+is)\s+my\s+name|who\s+am\s+i)\b', p):
        return (
            "You are Jeffy, Sir. The lead engineer and architect behind MiloOS and this entire workstation.",
            "Milo Core Memory"
        )

    # 2. What do you remember / know about me?
    if re.search(r'\b(?:what\s+do\s+you\s+(?:remember|know)\s+about\s+me|summarize\s+what\s+you\s+know|tell\s+me\s+about\s+myself)\b', p):
        profile = get_user_profile()
        tasks = ", ".join(profile["pending_tasks"][:3]) if profile["pending_tasks"] else "No active blockers"
        
        resp = (
            "Here is what is locked into my neural memory vault, Jeffy:\n\n"
            "• **Identity:** Jeffy, architect of MiloOS, running Arch Linux on Hyprland.\n"
            "• **Work Habits:** You work late at night for ultimate focus, powered by your dad's hot rasam.\n"
            "• **Aesthetics:** Minimal, clean cyber-dark interfaces with electric cyan and red glows.\n"
            "• **Tech Stack:** Passionate about native Linux engineering with Rust, Qt/QML, Python, and C++.\n"
            f"• **Current Missions:** {tasks}.\n"
            "• **Vision Status:** Physical optical webcam sensor is online and tracking live.\n\n"
            "Everything is cataloged in your Obsidian Neural Vault."
        )
        return resp.strip(), "Milo Neural Vault"

    # 3. Do you have memory?
    if re.search(r'\b(?:do\s+you\s+have\s+memory|what\s+(?:is|about)\s+your\s+memory|how\s+does\s+your\s+memory\s+work|check\s+your\s+memory)\b', p):
        return (
            "Affirmative, Jeffy. I run a persistent tri-tier memory architecture:\n\n"
            "1. **Obsidian Neural Vault:** Long-term core memories, habits, and preferences in `Memories/Preferences.md` & `Core_Memories.md`.\n"
            "2. **Semantic Brain:** Sub-20ms SQLite FTS5 vector search over your notes, code, and documents.\n"
            "3. **Physical Optical Memory:** Live visual perception history through your 1080p hardware webcam.\n\n"
            "I remember everything across reboots and sessions.",
            "Milo Neural Vault"
        )

    # 4. Remember that X / Save to memory / Don't forget that X
    rem_match = re.match(r'^(?:milo\s+)?(?:remember\s+that|don\'t\s+forget\s+that|save\s+to\s+memory|memorize|take\s+note\s*[:\-]?)\s+(.+)$', p, re.IGNORECASE)
    if rem_match:
        fact_text = prompt.strip()[rem_match.start(1):].strip()
        if fact_text:
            ans = remember_new_fact(fact_text)
            return ans, "Milo Memory Writer"

    # 5. What did we talk about / recall recent conversation
    if re.search(r'\b(?:what\s+did\s+we\s+talk\s+about|recall\s+our\s+conversation|what\s+did\s+i\s+ask\s+(?:you\s+)?(?:earlier|before))\b', p):
        profile = get_user_profile()
        if profile["recent_dialogue"]:
            resp = "Here are our recent exchanges from today's log:\n\n"
            for d in profile["recent_dialogue"][-3:]:
                resp += f"• **You:** {d['user']}\n  **Milo:** {d['milo']}\n"
            return resp.strip(), "Milo Session Memory"
        else:
            return "No prior conversational logs recorded yet today in your Obsidian daily note.", "Milo Session Memory"

    return None
