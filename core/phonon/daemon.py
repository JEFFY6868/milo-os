#!/usr/bin/env python3
"""
Milo Phonon Daemon — Resident Offline Speech Recognition Daemon
Keeps Phonon-2 loaded in memory to provide instantaneous (<200ms) transcription
via UNIX domain socket without reload penalty.

Socket Path: /run/user/<UID>/milo-phonon.sock (or /tmp/milo-phonon-<UID>.sock)
Protocol: Line-delimited JSON over UNIX Domain Socket
"""

import sys
import os
import json
import base64
import socket
import socketserver
import signal
import time
import tempfile
import threading
from pathlib import Path
from typing import Dict, Any

# Ensure phonon-env and local paths
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

ENV_SITE_PACKAGES = Path.home() / ".local/share/milo/phonon-env/lib/python3.12/site-packages"
if ENV_SITE_PACKAGES.exists() and str(ENV_SITE_PACKAGES) not in sys.path:
    sys.path.insert(0, str(ENV_SITE_PACKAGES))

from engine import PhononEngine

# Socket Path resolution
RUNTIME_DIR = os.environ.get("XDG_RUNTIME_DIR")
if RUNTIME_DIR and Path(RUNTIME_DIR).exists():
    SOCKET_PATH = Path(RUNTIME_DIR) / "milo-phonon.sock"
else:
    SOCKET_PATH = Path(f"/tmp/milo-phonon-{os.getuid()}.sock")

PID_FILE = SCRIPT_DIR / "daemon.pid"
LOG_FILE = SCRIPT_DIR / "daemon.log"


class PhononServerHandler(socketserver.StreamRequestHandler):
    """Handles JSON requests over UNIX socket."""

    def handle(self):
        engine = PhononEngine.get_instance()
        for line in self.rfile:
            line_str = line.decode("utf-8").strip()
            if not line_str:
                continue

            try:
                req = json.loads(line_str)
                action = req.get("action", "ping")

                if action == "ping":
                    resp = {
                        "status": "ok",
                        "model": "Phonon-2",
                        "model_dir": str(engine.model_dir),
                        "load_time": engine.load_time
                    }
                    self.send_json(resp)

                elif action == "transcribe_file":
                    path = req.get("path")
                    hotwords = req.get("hotwords")
                    if not path or not Path(path).is_file():
                        self.send_json({"status": "error", "message": f"File not found: {path}"})
                        continue

                    res = engine.transcribe_file(path, hotwords=hotwords)
                    res["status"] = "ok"
                    self.send_json(res)

                elif action == "transcribe_bytes":
                    data_b64 = req.get("data_b64")
                    hotwords = req.get("hotwords")
                    if not data_b64:
                        self.send_json({"status": "error", "message": "Missing data_b64"})
                        continue

                    raw_bytes = base64.b64decode(data_b64)
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                        tmp.write(raw_bytes)
                        tmp_path = tmp.name

                    try:
                        res = engine.transcribe_file(tmp_path, hotwords=hotwords)
                        res["status"] = "ok"
                        self.send_json(res)
                    finally:
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)

                elif action == "stop":
                    self.send_json({"status": "ok", "message": "Daemon shutting down"})
                    threading.Thread(target=self.server.shutdown).start()
                    break

                else:
                    self.send_json({"status": "error", "message": f"Unknown action: {action}"})

            except Exception as e:
                err_resp = {"status": "error", "message": str(e)}
                self.send_json(err_resp)

    def send_json(self, data: Dict[str, Any]):
        out = json.dumps(data) + "\n"
        self.wfile.write(out.encode("utf-8"))
        self.wfile.flush()


class UnixStreamServer(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True


def run_daemon():
    """Start the resident socket server."""
    # Write PID
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    # Clean old socket
    if SOCKET_PATH.exists():
        try:
            SOCKET_PATH.unlink()
        except OSError:
            pass

    print(f"🎙️ [Phonon Daemon] Pre-loading Phonon-2 speech model...")
    PhononEngine.get_instance()

    server = UnixStreamServer(str(SOCKET_PATH), PhononServerHandler)

    # Set permissions: user only
    try:
        os.chmod(str(SOCKET_PATH), 0o600)
    except OSError:
        pass

    def cleanup(signum=None, frame=None):
        print("\n🎙️ [Phonon Daemon] Shutting down...")
        if SOCKET_PATH.exists():
            SOCKET_PATH.unlink()
        if PID_FILE.exists():
            PID_FILE.unlink()
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    print(f"🚀 [Phonon Daemon] Ready and listening at: {SOCKET_PATH}")
    try:
        server.serve_forever()
    finally:
        cleanup()


if __name__ == "__main__":
    run_daemon()
