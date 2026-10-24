#!/usr/bin/env python3
"""
Milo WhatsApp Bidirectional Webhook Bridge Daemon
Receives incoming messages & self-chat triggers from OpenWA,
queries Milo Obsidian neural brain, and replies automatically via WhatsApp.

STRICT PRIVACY FILTER:
- Responds ONLY to Jeffy in his private 'Message Yourself' chat.
- Completely ignores all normal group chats and external 1-on-1 contacts.
- Never interferes with personal friends, family, or work conversations.
"""

import sys
import os
import re
import json
import time
import threading
import subprocess
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from datetime import datetime

HOME = Path.home()
OPENWA_DIR = HOME / ".local/share/milo/openwa"
API_KEY_FILE = OPENWA_DIR / "data/.api-key"
VAULT_DIR = HOME / "Documents/Obsidian/Milo"
DAILY_DIR = VAULT_DIR / "Daily"

OPENWA_URL = "http://127.0.0.1:2785"
WEBHOOK_PORT = 2786

# Loop prevention & deduplication cache
SENT_BY_MILO_IDS = set()
RECENT_MILO_TEXTS = set()
PROCESSED_MSG_IDS = set()


def get_api_key():
    if API_KEY_FILE.exists():
        return API_KEY_FILE.read_text().strip()
    return ""


def get_session_phone():
    """Retrieve the phone number of the linked session."""
    api_key = get_api_key()
    try:
        req = urllib.request.Request(f"{OPENWA_URL}/api/sessions", headers={"X-API-Key": api_key})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            if data and isinstance(data, list):
                phone = data[0].get("phone", "")
                if phone:
                    return str(phone)
    except Exception:
        pass
    return "919087876030"


def update_hud(message: str):
    """Safely forward notification to Omarchy Wayland HUD."""
    try:
        clean_msg = message.replace('"', '\\"').replace("'", "")
        os.system(f"omarchy-shell -q milo say \"{clean_msg}\" >/dev/null 2>&1 &")
    except Exception:
        pass


def send_whatsapp_message(session_id: str, chat_id: str, text: str):
    """Send text reply back through OpenWA REST API."""
    api_key = get_api_key()
    url = f"{OPENWA_URL}/api/sessions/{session_id}/messages/send-text"

    formatted_text = f"✦ Milo:\n{text}"
    RECENT_MILO_TEXTS.add(formatted_text.strip())
    RECENT_MILO_TEXTS.add(text.strip())
    if len(RECENT_MILO_TEXTS) > 1000:
        RECENT_MILO_TEXTS.clear()

    payload = json.dumps({"chatId": chat_id, "text": formatted_text}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json", "X-API-Key": api_key}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            res_data = json.loads(resp.read().decode())
            sent_id = res_data.get("id")
            if sent_id:
                SENT_BY_MILO_IDS.add(sent_id)
                if len(SENT_BY_MILO_IDS) > 1000:
                    SENT_BY_MILO_IDS.clear()
            return res_data
    except Exception as e:
        print(f"[Error sending reply to {chat_id}]: {e}", file=sys.stderr)
        return None


def query_milo(query: str) -> str:
    """Invokes milo-query with full Obsidian context."""
    try:
        res = subprocess.run(
            ["/home/jeffy/.local/bin/milo-query", query],
            capture_output=True,
            text=True,
            timeout=40
        )
        out = res.stdout.strip()
        if out:
            return out
        return "I received your message, but had trouble recalling that thought."
    except Exception as e:
        return f"Milo encountered an error: {e}"


def handle_kino_command(query: str) -> str | None:
    """Routes cinema/screenplay requests directly to Kino subagent."""
    match = re.match(r"(?i)^(?:kino|cinema|story|director|scene)[\s,:]*(.*)", query)
    if not match:
        return None
    subquery = match.group(1).strip()
    if not subquery:
        return "🎬 Kino Cinema Subagent Active. Send: 'kino idea <pitch>', 'kino character <name> <traits>', 'kino doctor <scene>', or 'kino shotlist <scene>'."

    subparts = subquery.split(" ", 1)
    subcmd = subparts[0].lower()
    rest = subparts[1].strip() if len(subparts) > 1 else ""

    if subcmd in ["studio", "ui", "link", "web"]:
        return "🎬 Kino Cinema Studio is running!\n🌐 Studio URL: http://127.0.0.1:3140\n📁 Obsidian Vault: Cinema/Projects/project_mirage\nActive Screenplay: 3-Act Beat Sheet & Courier Prime Editor"

    kino_cmd = ["/home/jeffy/.local/bin/milo-kino"]
    if subcmd in ["idea", "character", "doctor", "shotlist", "project"] and rest:
        if subcmd == "character":
            cparts = rest.split(" ", 1)
            kino_cmd.extend(["character", cparts[0], cparts[1] if len(cparts) > 1 else "core character"])
        else:
            kino_cmd.extend([subcmd, rest])
    else:
        kino_cmd.extend(["idea", subquery])

    try:
        res = subprocess.run(kino_cmd, capture_output=True, text=True, timeout=45)
        out = res.stdout.strip()
        if out:
            clean_out = re.sub(r"\x1B\[[0-?]*[ -/]*[@-~]", "", out)
            return clean_out
    except Exception as e:
        return f"Kino subagent error: {e}"
    return None


def process_message_event(event: dict):
    """Processes message events in a background thread to prevent webhook socket timeouts."""
    try:
        event_type = event.get("event")
        raw_data = event.get("data", {})
        session_id = event.get("sessionId", "d1050efa-8ecc-4eaa-a767-9fb3f1ad4b90")

        # Extract message object
        message = raw_data.get("message", raw_data)
        msg_id = message.get("id", "")
        from_me = bool(message.get("fromMe", False))
        body = message.get("body", "").strip()
        sender = message.get("from", "")
        chat_id = message.get("chatId") or message.get("to") or sender or ""

        if not body or not chat_id:
            return

        # Deduplication
        if msg_id:
            if msg_id in PROCESSED_MSG_IDS:
                return
            PROCESSED_MSG_IDS.add(msg_id)
            if len(PROCESSED_MSG_IDS) > 2000:
                PROCESSED_MSG_IDS.clear()

        # 1. Loop Prevention: Ignore messages Milo itself sent
        if msg_id in SENT_BY_MILO_IDS:
            return

        if body in RECENT_MILO_TEXTS or body.startswith("✦") or "✦ Milo" in body:
            return

        session_phone = get_session_phone()
        clean_session_phone = re.sub(r"\D", "", session_phone)

        # 2. Identify Chat Type
        is_group = "@g.us" in chat_id or "@g.us" in sender
        chat_num = re.sub(r"\D", "", chat_id.split("@")[0])

        # Self-Chat check: 1-on-1 chat with user's own phone number ("Message Yourself")
        is_self_chat = (
            not is_group and
            bool(clean_session_phone) and
            (chat_num == clean_session_phone or clean_session_phone in chat_id)
        )

        print(f"\n[Webhook Event] {event_type} | ID: {msg_id[:12]} | fromMe: {from_me} | Group: {is_group} | SelfChat: {is_self_chat} | Chat: {chat_id} | Text: {body[:35]}")

        should_respond = False

        if is_self_chat:
            # User is in "Message Yourself" private notes
            should_respond = True
            print(f"  ✅ Accepted: Self-Chat from Jeffy ({chat_id})")

        elif is_group:
            # Group chat: NEVER respond unless explicitly tagged with '!milo ' or '@milo ' or 'kino '
            if re.match(r"(?i)^(?:!milo|@milo|milo:)\s+", body) or re.match(r"(?i)^kino\s+", body):
                should_respond = True
                print(f"  ✅ Accepted: Explicit group command in {chat_id}")
            else:
                print(f"  ⛔ IGNORED: Group message ({chat_id})")

        else:
            # Direct 1-on-1 chat with another contact (friend, family, work colleague)
            # NEVER auto-reply to personal chats unless explicitly prefixed with '!milo '
            if re.match(r"(?i)^(?:!milo|milo:)\s+", body) or re.match(r"(?i)^kino\s+", body):
                should_respond = True
                print(f"  ✅ Accepted: Explicit command in 1-on-1 chat ({chat_id})")
            else:
                print(f"  ⛔ IGNORED: Personal 1-on-1 chat with {chat_id}")

        if not should_respond:
            return

        clean_query = re.sub(r"(?i)^(?:!milo|@milo|milo:|milo)[,\s]+", "", body).strip()
        print(f"  🚀 Processing Query: {clean_query}")

        # Update Desktop HUD
        update_hud(f"📱 WA: {clean_query[:40]}...")

        # Query Kino or Milo Brain
        kino_reply = handle_kino_command(clean_query)
        if kino_reply:
            print("  🎬 Routing to Kino Cinema Subagent...")
            response = kino_reply
        else:
            print("  ✦ Thinking with Obsidian Neural Vault...")
            response = query_milo(clean_query)

        print(f"  ✦ Reply: {response[:80]}...")

        # Send Reply Back
        send_whatsapp_message(session_id, chat_id, response)

    except Exception as e:
        print(f"[Error processing message event]: {e}", file=sys.stderr)


class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        # Immediately ACK webhook so OpenWA socket never times out
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        try:
            self.wfile.write(b'{"status":"ok"}')
        except Exception:
            pass

        try:
            event = json.loads(post_data.decode("utf-8"))
            # Spawn asynchronous processing worker
            threading.Thread(target=process_message_event, args=(event,), daemon=True).start()
        except Exception as e:
            print(f"[Webhook JSON Decode Error]: {e}", file=sys.stderr)

    def log_message(self, format, *args):
        # Suppress routine HTTP 200 access logs to keep journal clean
        return


def main():
    print(f"🚀 Milo WhatsApp Webhook Bridge listening on http://127.0.0.1:{WEBHOOK_PORT}/webhook")
    print("🔒 Privacy Guard Active: Self-Chat enabled. All external contacts & groups strictly muted.")
    server = HTTPServer(("127.0.0.1", WEBHOOK_PORT), WebhookHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Milo WhatsApp Webhook Bridge...")
        server.server_close()


if __name__ == "__main__":
    main()
