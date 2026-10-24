import os
import re
import json
import subprocess
from datetime import datetime
from pathlib import Path
from google import genai

VAULT_DIR = Path.home() / "Documents/Obsidian/Milo"
DAILY_DIR = VAULT_DIR / "Daily"
CONFIG_ENV = Path.home() / ".config/milo/browser.env"

MODELS_TO_TRY = [
    "gemini-3.5-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-3.5-flash",
    "gemini-flash-latest"
]

def get_gemini_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key and CONFIG_ENV.exists():
        for line in CONFIG_ENV.read_text(encoding="utf-8").splitlines():
            if line.startswith("GEMINI_API_KEY="):
                api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
    if not api_key:
        raise ValueError("GEMINI_API_KEY not configured. Set it in ~/.config/milo/browser.env")
    return genai.Client(api_key=api_key)

def get_desktop_state():
    """Gathers real-time Hyprland desktop state, workspaces, and running windows."""
    try:
        clients_proc = subprocess.run(["hyprctl", "clients", "-j"], capture_output=True, text=True, timeout=3)
        clients = json.loads(clients_proc.stdout) if clients_proc.returncode == 0 else []
        
        ws_map = {}
        for c in clients:
            ws_id = c.get("workspace", {}).get("name", str(c.get("workspace", {}).get("id", "")))
            clazz = c.get("class", "app")
            title = c.get("title", "")
            ws_map.setdefault(ws_id, []).append(f"{clazz} (title: {title[:60]})")

        ws_proc = subprocess.run(["hyprctl", "activeworkspace", "-j"], capture_output=True, text=True, timeout=3)
        active_ws = json.loads(ws_proc.stdout).get("name", "1") if ws_proc.returncode == 0 else "1"

        lines = [f"Currently Active Workspace: Workspace {active_ws}"]
        for ws_name in sorted(ws_map.keys(), key=lambda x: (len(x), x)):
            apps = "; ".join(ws_map[ws_name])
            lines.append(f"Workspace {ws_name}: {apps}")

        if not ws_map:
            lines.append("No active graphical client windows open.")

        return "\n".join(lines)
    except Exception as e:
        return f"Desktop state check unavailable: {e}"

def get_obsidian_context():
    """Retrieves Jeffy's profile, core memories, and preferences from Obsidian Neural Vault."""
    try:
        facts = ""
        memories_file = VAULT_DIR / "Memories/Core_Memories.md"
        if memories_file.exists():
            lines = [l for l in memories_file.read_text(encoding="utf-8").splitlines() if l.strip().startswith("- ")]
            facts = "\n".join(lines[-6:])

        prefs = ""
        prefs_file = VAULT_DIR / "Memories/Preferences.md"
        if prefs_file.exists():
            lines = [l for l in prefs_file.read_text(encoding="utf-8").splitlines() if l.strip().startswith("- ")]
            prefs = "\n".join(lines[-6:])

        bio = ""
        bio_file = VAULT_DIR / "Profile/Jeffy.md"
        if bio_file.exists():
            lines = [l for l in bio_file.read_text(encoding="utf-8").splitlines() if l.strip().startswith("- ")]
            bio = "\n".join(lines[:6])

        return f"Jeffy Profile:\n{bio}\n\nCore Memories:\n{facts}\n\nUser Preferences:\n{prefs}"
    except Exception as e:
        return ""

def log_to_daily_note(query, reply):
    """Appends voice conversation to today's Obsidian daily note."""
    try:
        DAILY_DIR.mkdir(parents=True, exist_ok=True)
        today = datetime.now().strftime("%Y-%m-%d")
        daily_file = DAILY_DIR / f"{today}.md"
        now_time = datetime.now().strftime("%H:%M")

        if not daily_file.exists():
            daily_file.write_text(f"# 📅 Daily Note: {today}\n\n## 💬 Voice & Interaction Log\n\n", encoding="utf-8")

        entry = f"### {now_time} - Milo Voice Call\n- **Jeffy:** {query}\n- **Milo:** {reply}\n\n"
        with open(daily_file, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception:
        pass

def ask_milo(query: str, voice: str = "") -> dict:
    """
    Core Milo AI Companion Reasoning Engine.
    Uses Gemini 2.5 Flash Lite + Live Hyprland Desktop State + Obsidian Vault Context.
    """
    try:
        desktop_state = get_desktop_state()
        obsidian_ctx = get_obsidian_context()
        client = get_gemini_client()

        # Check for direct Hyprland desktop actions
        q_lower = query.lower()
        action_performed = None
        if "switch to workspace" in q_lower or "go to workspace" in q_lower:
            m = re.search(r"workspace\s+(\d+)", q_lower)
            if m:
                target_ws = m.group(1)
                subprocess.run(["hyprctl", "dispatch", "workspace", target_ws], check=False)
                action_performed = f"Switched to workspace {target_ws}."

        system_instruction = (
            "You are Milo, Jeffy's personal ambient AI desktop companion on Arch Linux running the Hyprland compositor.\n"
            "You are having a direct, spoken, real-time voice call with Jeffy.\n"
            "CRITICAL VOICE INSTRUCTIONS:\n"
            "1. Keep answers SHORT, CRISP, and CONVERSATIONAL (1 to 2 sentences max).\n"
            "2. Never use markdown symbols, asterisks (*), hashtags (#), or bullet points, because your response is spoken aloud via Text-To-Speech.\n"
            "3. If Jeffy speaks to you in Tamil or Tanglish, reply in warm, natural Tanglish or Tamil matching his friendly buddy vibe.\n"
            "4. If Jeffy speaks in English, reply in casual, intelligent English.\n"
            "5. You have LIVE visibility into his Arch Linux desktop, running windows, and workspaces. Always answer desktop questions with 100% accuracy based on the Live Desktop State provided below.\n\n"
            f"[Live Arch Linux Desktop State]:\n{desktop_state}\n\n"
            f"[Obsidian Memory Context]:\n{obsidian_ctx}\n"
        )

        prompt = f"Jeffy asked: {query}"
        if action_performed:
            prompt += f"\n(System notice: you just successfully performed action: '{action_performed}')"

        resp = None
        last_err = None
        for model_name in MODELS_TO_TRY:
            try:
                resp = client.models.generate_content(
                    model=model_name,
                    contents=[system_instruction, prompt]
                )
                if resp and resp.text:
                    break
            except Exception as e:
                last_err = e
                continue

        if not resp or not resp.text:
            raise Exception(f"All models failed: {last_err}")

        reply = (resp.text or "").strip()
        # Clean speech
        clean_speech = re.sub(r"[#*_`>\[\]\(\)]", " ", reply)
        clean_speech = re.sub(r"\s+", " ", clean_speech).strip()

        # Log to Obsidian
        log_to_daily_note(query, reply)

        return {
            "reply": reply,
            "clean_speech": clean_speech
        }
    except Exception as e:
        err_msg = f"Sorry Jeffy, I ran into an error checking that: {e}"
        return {
            "reply": err_msg,
            "clean_speech": err_msg
        }
