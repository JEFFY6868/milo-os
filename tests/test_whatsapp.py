"""
Tests for Milo WhatsApp Integration
Covers:
- core.whatsapp.engine: session lookup, sync, list formatting, read thread
- core.cortex.intelligence_router: handle_whatsapp_intent routing
"""

import os
import json
import pytest
from pathlib import Path
from core.whatsapp.engine import (
    get_session_info,
    sync_inbox,
    get_inbox_data,
    format_terminal_list,
    read_chat,
)
from core.cortex.intelligence_router import handle_whatsapp_intent


def test_get_session_info():
    info = get_session_info()
    assert isinstance(info, dict)
    assert "id" in info
    assert "name" in info
    assert "status" in info
    assert "phone" in info
    assert "pushName" in info


def test_sync_inbox_and_data():
    inbox = sync_inbox()
    assert isinstance(inbox, dict)
    assert "status" in inbox
    assert "unread_count" in inbox
    assert "updated_at" in inbox
    assert "chats" in inbox
    assert isinstance(inbox["chats"], list)

    cached = get_inbox_data(force_sync=False)
    assert cached["status"] == inbox["status"]
    assert len(cached["chats"]) == len(inbox["chats"])


def test_format_terminal_list():
    sample_data = {
        "status": "ready",
        "phone": "919087876030",
        "pushName": "JEFFY",
        "unread_count": 1,
        "updated_at": "06:00 PM",
        "chats": [
            {
                "index": 1,
                "id": "12345@c.us",
                "name": "Test User",
                "is_group": False,
                "unread": 1,
                "snippet": "Hello Milo!",
                "time": "05:50 PM",
                "direction": "incoming",
            }
        ],
    }
    output = format_terminal_list(sample_data)
    assert "MILO WHATSAPP INBOX" in output
    assert "Test User" in output
    assert "Hello Milo!" in output


def test_read_chat_fallback():
    # Reading an unknown ID should gracefully return not found message
    res = read_chat("nonexistent_contact_9999999")
    assert "not found" in res.lower()


def test_handle_whatsapp_intent_check():
    res = handle_whatsapp_intent("check whatsapp")
    assert res is not None
    output, provider = res
    assert provider == "Milo WhatsApp Copilot"
    assert "MILO WHATSAPP INBOX" in output


def test_handle_whatsapp_intent_read():
    res = handle_whatsapp_intent("read whatsapp 1")
    assert res is not None
    output, provider = res
    assert provider == "Milo WhatsApp Copilot"
    assert "MILO WHATSAPP THREAD" in output or "No chat thread found" in output


def test_handle_whatsapp_intent_ignore_unrelated():
    assert handle_whatsapp_intent("what is the weather in Tokyo?") is None
    assert handle_whatsapp_intent("play some jazz music") is None
