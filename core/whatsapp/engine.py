#!/usr/bin/env python3
"""
Milo WhatsApp Engine & Synchronizer
Connects OpenWA (Baileys) to MiloOS CLI, HUD, and Cortex Intelligence Router.
"""

import os
import sys
import re
import json
import time
import sqlite3
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Paths
OPENWA_DIR = Path.home() / ".local" / "share" / "milo" / "openwa"
DATA_DIR = Path.home() / ".local" / "share" / "milo" / "whatsapp"
INBOX_JSON = DATA_DIR / "inbox.json"
TRIGGER_PATH = Path("/tmp/milo-whatsapp-trigger")

SQLITE_PATH = OPENWA_DIR / "data" / "openwa.sqlite"
API_KEY_FILE = OPENWA_DIR / "data" / ".api-key"
OPENWA_URL = "http://127.0.0.1:2785"
KEYS_ENV = Path.home() / ".config" / "milo" / "keys.env"

# Cyberpunk Terminal Styling
CYAN = "\033[1;36m"
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
RED = "\033[1;31m"
MAGENTA = "\033[1;35m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


def get_api_key() -> str:
    if API_KEY_FILE.exists():
        try:
            return API_KEY_FILE.read_text(encoding="utf-8").strip()
        except Exception:
            pass
    return ""


def get_session_info() -> Dict[str, Any]:
    """Retrieve details about the active WhatsApp session from OpenWA (API or SQLite cache)."""
    key = get_api_key()
    try:
        req = urllib.request.Request(f"{OPENWA_URL}/api/sessions", headers={"X-API-Key": key})
        with urllib.request.urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read().decode())
            if isinstance(data, list) and len(data) > 0:
                s = data[0]
                return {
                    "id": s.get("id", "default"),
                    "name": s.get("name", "milo"),
                    "status": s.get("status", "offline"),
                    "phone": s.get("phone", ""),
                    "pushName": s.get("pushName", ""),
                    "connectedAt": s.get("connectedAt", "")
                }
    except Exception:
        pass

    # Fallback to local SQLite session record if HTTP API is not directly reachable
    if SQLITE_PATH.exists():
        try:
            conn = sqlite3.connect(f"file:{SQLITE_PATH}?mode=ro", uri=True)
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, status, phone, pushName, connectedAt FROM sessions ORDER BY updatedAt DESC LIMIT 1")
            row = cursor.fetchone()
            conn.close()
            if row:
                return {
                    "id": row[0] or "default",
                    "name": row[1] or "milo",
                    "status": row[2] or "ready",
                    "phone": row[3] or "",
                    "pushName": row[4] or "",
                    "connectedAt": row[5] or ""
                }
        except Exception:
            pass

    return {
        "id": "default",
        "name": "milo",
        "status": "offline",
        "phone": "",
        "pushName": "",
        "connectedAt": ""
    }


def sync_inbox() -> Dict[str, Any]:
    """Synchronize recent chats and messages into ~/.local/share/milo/whatsapp/inbox.json."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    session = get_session_info()
    sid = session["id"]
    key = get_api_key()

    # 1. Fetch live chats from OpenWA REST API (for names & unread counts)
    chats_by_id = {}
    if session["status"] == "ready":
        try:
            req = urllib.request.Request(
                f"{OPENWA_URL}/api/sessions/{sid}/chats?limit=40",
                headers={"X-API-Key": key}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                api_chats = json.loads(resp.read().decode())
                for c in api_chats:
                    chats_by_id[c["id"]] = c
        except Exception:
            pass

    # 2. Query local SQLite for recent active threads and message bodies
    unified_chats = []
    total_unread = 0

    if SQLITE_PATH.exists():
        try:
            conn = sqlite3.connect(f"file:{SQLITE_PATH}?mode=ro", uri=True)
            cur = conn.cursor()
            query = """
            SELECT 
                m.chatId,
                COALESCE(m.chatName, m.chatId) as name,
                m.body,
                m.author,
                m.timestamp,
                m.direction
            FROM messages m
            INNER JOIN (
                SELECT chatId, MAX(timestamp) as max_ts
                FROM messages
                GROUP BY chatId
            ) latest ON m.chatId = latest.chatId AND m.timestamp = latest.max_ts
            ORDER BY m.timestamp DESC
            LIMIT 30
            """
            cur.execute(query)
            rows = cur.fetchall()
            conn.close()

            for idx, r in enumerate(rows, 1):
                chat_id, raw_name, body, author, ts, direction = r
                api_info = chats_by_id.get(chat_id, {})

                display_name = api_info.get("name") or raw_name or chat_id
                if display_name == chat_id:
                    display_name = re.sub(r"@(c|g)\.us", "", chat_id)

                unread = api_info.get("unreadCount", 0)
                total_unread += unread
                is_group = "@g.us" in chat_id

                snippet = (body or "[Media Attachment]").replace("\r", " ").replace("\n", " ").strip()
                if len(snippet) > 80:
                    snippet = snippet[:77] + "..."

                time_str = time.strftime("%I:%M %p", time.localtime(ts))

                unified_chats.append({
                    "index": idx,
                    "id": chat_id,
                    "name": display_name,
                    "is_group": is_group,
                    "unread": unread,
                    "snippet": snippet,
                    "author": author or "",
                    "time": time_str,
                    "timestamp": ts,
                    "direction": direction
                })
        except Exception as e:
            sys.stderr.write(f"[Milo WA Engine] SQLite sync error: {e}\n")

    # If total_unread wasn't calculated from recent threads, sum all unread
    if not total_unread and chats_by_id:
        total_unread = sum(c.get("unreadCount", 0) for c in chats_by_id.values())

    payload = {
        "status": session["status"],
        "phone": session["phone"],
        "pushName": session["pushName"],
        "unread_count": total_unread,
        "updated_at": time.strftime("%I:%M %p"),
        "epoch": int(time.time()),
        "chats": unified_chats
    }

    # Write atomic cache
    tmp_path = DATA_DIR / "inbox.json.tmp"
    try:
        tmp_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        tmp_path.replace(INBOX_JSON)
        INBOX_JSON.chmod(0o600)
    except Exception:
        pass

    # Touch HUD trigger
    try:
        TRIGGER_PATH.write_text(f"{int(time.time()*1000)} sync\n")
    except Exception:
        pass

    return payload


def get_inbox_data(force_sync: bool = False) -> Dict[str, Any]:
    """Retrieve inbox data from cache or fresh sync."""
    if not force_sync and INBOX_JSON.exists():
        try:
            mtime = INBOX_JSON.stat().st_mtime
            if (time.time() - mtime) < 20:  # Fresh within 20s
                return json.loads(INBOX_JSON.read_text(encoding="utf-8"))
        except Exception:
            pass
    return sync_inbox()


def format_terminal_list(inbox_data: Dict[str, Any], unread_only: bool = False) -> str:
    """Format recent WhatsApp chats for terminal presentation."""
    chats = inbox_data.get("chats", [])
    if unread_only:
        chats = [c for c in chats if c.get("unread", 0) > 0]

    user_str = inbox_data.get("pushName") or "User"
    phone_str = inbox_data.get("phone") or "Active"
    unread_count = inbox_data.get("unread_count", 0)
    status_str = f"{GREEN}● Ready{RESET}" if inbox_data.get("status") == "ready" else f"{RED}○ Offline{RESET}"

    out = []
    out.append(f"\n{BOLD}{CYAN}✦ MILO WHATSAPP INBOX{RESET} // {status_str} ({user_str} · {phone_str})")
    out.append(f"{DIM}Unread Messages: {unread_count}  •  Updated: {inbox_data.get('updated_at', '')}{RESET}")
    out.append(f"{DIM}──────────────────────────────────────────────────────────────────────────{RESET}")

    if not chats:
        out.append(f"  {GREEN}✔ No unread messages. WhatsApp inbox is clear!{RESET}\n")
        return "\n".join(out)

    for c in chats[:15]:
        idx = c["index"]
        unread = c["unread"]
        badge = f"{GREEN}[{unread} NEW]{RESET}" if unread > 0 else "        "
        icon = f"{CYAN}👥{RESET}" if c["is_group"] else f"{YELLOW}👤{RESET}"
        name = c["name"]
        if len(name) > 26:
            name = name[:23] + "..."
        time_str = c["time"]
        snippet = c["snippet"]

        out.append(f" {idx:2d}. {badge} {icon} {BOLD}{name:26s}{RESET} {DIM}{time_str:8s}{RESET}  {snippet}")

    out.append(f"{DIM}──────────────────────────────────────────────────────────────────────────{RESET}")
    out.append(f"{DIM}💡 Tip: Run 'milo wa read <number>' or 'milo wa summarize' for AI briefing{RESET}\n")
    return "\n".join(out)


def read_chat(target: str, limit: int = 15) -> str:
    """Display recent message history for a specific chat index or chatId."""
    inbox = get_inbox_data()
    chats = inbox.get("chats", [])
    target_chat = None

    # Check numeric index
    if target.isdigit():
        idx = int(target)
        for c in chats:
            if c["index"] == idx:
                target_chat = c
                break

    # Check chatId or fuzzy name match
    if not target_chat:
        target_lower = target.lower()
        for c in chats:
            if target in c["id"] or target_lower in c["name"].lower():
                target_chat = c
                break

    if not target_chat:
        return f"{RED}Error: Chat '{target}' not found in recent threads.{RESET}"

    chat_id = target_chat["id"]
    chat_name = target_chat["name"]
    icon = "👥 Group" if target_chat["is_group"] else "👤 Direct"

    out = []
    out.append(f"\n{BOLD}{CYAN}✦ MILO WHATSAPP THREAD{RESET} // {icon}: {BOLD}{chat_name}{RESET} ({chat_id})")
    out.append(f"{DIM}──────────────────────────────────────────────────────────────────────────{RESET}")

    if not SQLITE_PATH.exists():
        return "\n".join(out) + "\nDatabase not found."

    try:
        conn = sqlite3.connect(f"file:{SQLITE_PATH}?mode=ro", uri=True)
        cur = conn.cursor()
        query = """
        SELECT author, body, timestamp, direction
        FROM messages
        WHERE chatId = ?
        ORDER BY timestamp DESC
        LIMIT ?
        """
        cur.execute(query, (chat_id, limit))
        rows = list(reversed(cur.fetchall()))
        conn.close()

        if not rows:
            out.append(f"  {DIM}No messages found in history for this chat.{RESET}")
        else:
            for r in rows:
                author, body, ts, direction = r
                t_str = time.strftime("%I:%M %p", time.localtime(ts))
                if direction == "outbound":
                    out.append(f"  {DIM}[{t_str}]{RESET} {BOLD}{GREEN}ME:{RESET} {body}")
                else:
                    speaker = author or "Them"
                    if "@c.us" in speaker:
                        speaker = speaker.split("@")[0]
                    out.append(f"  {DIM}[{t_str}]{RESET} {BOLD}{CYAN}{speaker}:{RESET} {body}")

    except Exception as e:
        out.append(f"{RED}Error reading chat messages: {e}{RESET}")

    out.append(f"{DIM}──────────────────────────────────────────────────────────────────────────{RESET}")
    out.append(f"{DIM}💡 Reply with: milo wa send \"{chat_name}\" \"<your message>\"{RESET}\n")
    return "\n".join(out)


def send_whatsapp_message(recipient: str, message: str) -> Tuple[bool, str]:
    """Send a WhatsApp text message to contact or chat ID."""
    session = get_session_info()
    sid = session["id"]
    key = get_api_key()

    if session["status"] != "ready":
        return False, f"WhatsApp session is not active ({session['status']}). Run 'milo wa status'."

    # Resolve target recipient
    target_chat = recipient
    if recipient.isdigit() and len(recipient) <= 3:
        # Numeric index from list
        inbox = get_inbox_data()
        idx = int(recipient)
        for c in inbox.get("chats", []):
            if c["index"] == idx:
                target_chat = c["id"]
                break
    elif "@" not in target_chat:
        # Try matching chat name
        inbox = get_inbox_data()
        r_lower = recipient.lower()
        matched = None
        for c in inbox.get("chats", []):
            if r_lower in c["name"].lower():
                matched = c["id"]
                break
        if matched:
            target_chat = matched
        else:
            # Clean digits and format as phone
            clean_digits = re.sub(r"\D", "", recipient)
            if len(clean_digits) == 10:
                clean_digits = "91" + clean_digits  # Default India code if 10 digits
            target_chat = f"{clean_digits}@c.us"

    payload = json.dumps({"chatId": target_chat, "text": message}).encode("utf-8")
    req = urllib.request.Request(
        f"{OPENWA_URL}/api/sessions/{sid}/messages/send-text",
        data=payload,
        headers={"Content-Type": "application/json", "X-API-Key": key}
    )

    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode())
            return True, str(data.get("id") or "Message delivered")
    except Exception as e:
        return False, f"Delivery failed: {e}"


def summarize_inbox(inbox_data: Optional[Dict[str, Any]] = None) -> str:
    """Generate an AI executive briefing of recent WhatsApp incoming messages."""
    if not SQLITE_PATH.exists():
        return "No WhatsApp message history found to summarize."

    # Fetch last 25 incoming messages from the last 24 hours
    since_ts = int(time.time()) - 86400
    try:
        conn = sqlite3.connect(f"file:{SQLITE_PATH}?mode=ro", uri=True)
        cur = conn.cursor()
        cur.execute("""
            SELECT COALESCE(chatName, chatId), body, author, timestamp 
            FROM messages 
            WHERE direction = 'incoming' AND timestamp > ? 
            ORDER BY timestamp DESC 
            LIMIT 30
        """, (since_ts,))
        rows = cur.fetchall()
        conn.close()
    except Exception as e:
        return f"Database error reading messages: {e}"

    if not rows:
        return "You have no incoming WhatsApp messages in the last 24 hours. Inbox is clear!"

    context_lines = []
    for name, body, author, ts in rows:
        if body and len(body.strip()) > 3:
            clean_body = body.replace("\r", " ").replace("\n", " ").strip()
            context_lines.append(f"[{name}]: {clean_body[:160]}")

    context_text = "\n".join(context_lines[:20])

    prompt = (
        "You are Milo, Jeffy's AI personal operating system companion. "
        "Summarize his recent incoming WhatsApp messages into a crisp, 3-4 bullet executive briefing. "
        "Highlight important action items, job postings, schedules, or personal messages. "
        "Filter out spam, repetitive group banter, or memes. Be concise, direct, and conversational.\n\n"
        f"Incoming WhatsApp messages:\n{context_text}"
    )

    # 1. Try local OmniRoute (port 20128)
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:20128/v1/chat/completions",
            data=json.dumps({
                "model": "claude-sonnet-5-5",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 250
            }).encode(),
            headers={"Content-Type": "application/json", "Authorization": "Bearer sk-5dced7748166b4b8-269ccb-0bc983a7"}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
            return data["choices"][0]["message"]["content"].strip()
    except Exception:
        pass

    # 2. Try direct Groq if key exists
    groq_key = os.environ.get("GROQ_API_KEY", "")
    if not groq_key and KEYS_ENV.exists():
        for line in KEYS_ENV.read_text().splitlines():
            if line.startswith("GROQ_API_KEY="):
                groq_key = line.split("=", 1)[1].strip()

    if groq_key:
        try:
            req = urllib.request.Request(
                "https://api.groq.com/openai/v1/chat/completions",
                data=json.dumps({
                    "model": "llama-3.1-8b-instant",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 250
                }).encode(),
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {groq_key}"}
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode())
                return data["choices"][0]["message"]["content"].strip()
        except Exception:
            pass

    # 3. Fallback Heuristic Summary if offline
    summary_lines = [
        f"{BOLD}{GREEN}✦ Milo WhatsApp Quick Briefing ({len(rows)} recent messages):{RESET}"
    ]
    unique_chats = {}
    for name, body, author, ts in rows:
        if name not in unique_chats:
            unique_chats[name] = body.replace("\n", " ")[:60]

    for name, snippet in list(unique_chats.items())[:4]:
        summary_lines.append(f"• {BOLD}{name}:{RESET} {snippet}...")

    summary_lines.append(f"\n{DIM}Run 'milo wa list' to view all active threads.{RESET}")
    return "\n".join(summary_lines)
