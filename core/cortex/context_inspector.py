#!/usr/bin/env python3
"""
Milo Cognitive Core (Cortex) — Desktop Context Inspector
Captures Wayland/Hyprland focused window context, active primary mouse selection,
and clipboard state to enable seamless zero-copy AI queries ("fix this", "explain this").
"""

import sys
import os
import json
import subprocess
import re
from pathlib import Path
from typing import Dict, Any, Optional

AWARENESS_TRIGGERS = {
    "fix", "fix this", "debug", "error", "traceback", "explain this",
    "what is this", "why", "how to fix", "what does this mean", "issue",
    "selected", "here", "help", "log", "exception"
}


def get_hyprland_signature() -> Optional[str]:
    """Find active Hyprland instance signature from env or socket directory."""
    sig = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")
    if sig:
        return sig
    uid = os.getuid()
    hypr_dir = Path(f"/run/user/{uid}/hypr")
    if hypr_dir.exists():
        dirs = [d.name for d in hypr_dir.iterdir() if d.is_dir()]
        if dirs:
            return sorted(dirs)[-1]
    return None


def get_active_window() -> Dict[str, str]:
    """
    Returns active window details from Hyprland.
    If the current window is the Cortex HUD, retrieves the previously focused window (focusHistoryID: 1).
    """
    sig = get_hyprland_signature()
    env = os.environ.copy()
    if sig:
        env["HYPRLAND_INSTANCE_SIGNATURE"] = sig

    try:
        proc = subprocess.run(
            ["hyprctl", "clients", "-j"],
            capture_output=True,
            text=True,
            timeout=1.0,
            env=env
        )
        if proc.returncode != 0 or not proc.stdout.strip():
            return {}

        clients = json.loads(proc.stdout)
        if not clients:
            return {}

        # Sort by focusHistoryID (0 = current, 1 = previous)
        clients.sort(key=lambda c: c.get("focusHistoryID", 999))

        # If current is Cortex HUD or terminal running HUD, pick the work window (focusHistoryID 1)
        target = clients[0]
        curr_class = target.get("class", "").lower()
        curr_title = target.get("title", "").lower()

        if "cortex" in curr_class or "cortex" in curr_title:
            if len(clients) > 1:
                target = clients[1]

        return {
            "class": target.get("class", "Unknown"),
            "title": target.get("title", ""),
            "workspace": str(target.get("workspace", {}).get("name", "")),
            "pid": str(target.get("pid", ""))
        }
    except Exception:
        return {}


def get_selection_or_clipboard() -> Dict[str, Any]:
    """
    Reads active mouse selection (wl-paste -p) or standard clipboard (wl-paste).
    Caps output at 600 characters for optimal LLM context size.
    """
    text = ""
    source = "none"

    # 1. Try Primary Mouse Selection (highest priority for highlighted code/errors)
    try:
        proc = subprocess.run(
            ["wl-paste", "-p", "--no-newline"],
            capture_output=True,
            text=True,
            timeout=0.4
        )
        if proc.returncode == 0 and proc.stdout.strip():
            text = proc.stdout.strip()
            source = "selection"
    except Exception:
        pass

    # 2. Try Standard Clipboard if no primary selection
    if not text:
        try:
            proc = subprocess.run(
                ["wl-paste", "--no-newline"],
                capture_output=True,
                text=True,
                timeout=0.4
            )
            if proc.returncode == 0 and proc.stdout.strip():
                text = proc.stdout.strip()
                source = "clipboard"
        except Exception:
            pass

    if not text:
        return {"text": "", "source": "none", "is_error": False}

    # Detect if selection resembles an error / traceback / command
    is_error = bool(re.search(
        r"(Traceback|Error|Exception|failed|denied|invalid|syntax|No such|command not found|FATAL|SIG)",
        text,
        re.IGNORECASE
    ))

    # Cap text length for micro-model context
    if len(text) > 600:
        text = text[:597] + "..."

    return {
        "text": text,
        "source": source,
        "is_error": is_error,
        "length": len(text)
    }


def capture_desktop_context() -> Dict[str, Any]:
    """Full snapshot of active desktop state for AI context injection."""
    win = get_active_window()
    sel = get_selection_or_clipboard()

    parts = []
    if win.get("class"):
        parts.append(f"Application: {win['class']} (Window: '{win['title']}')")

    if sel.get("text"):
        label = "Highlighted Selection" if sel["source"] == "selection" else "Clipboard Text"
        parts.append(f"[{label}]:\n{sel['text']}")

    context_str = "\n".join(parts) if parts else ""

    return {
        "window": win,
        "selection": sel,
        "formatted_context": context_str,
        "has_context": bool(context_str.strip())
    }


def should_trigger_awareness(query: str, force_flag: bool = False) -> bool:
    """Detect if query warrants desktop context inspection."""
    if force_flag:
        return True
    q_clean = query.lower().strip()
    words = set(re.findall(r"[a-z0-9]+", q_clean))
    return bool(words & AWARENESS_TRIGGERS) or q_clean in AWARENESS_TRIGGERS


if __name__ == "__main__":
    ctx = capture_desktop_context()
    print("Desktop Context Captured:")
    print(json.dumps(ctx, indent=2))
