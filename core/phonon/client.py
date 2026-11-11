#!/usr/bin/env python3
"""
Milo Phonon Client Helper
Provides a lightweight client to interact with the resident milo-phonon daemon
via UNIX domain socket, falling back to direct engine execution if needed.
"""

import os
import sys
import json
import base64
import socket
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

CANDIDATE_SOCKETS = [
    Path(f"/run/user/{os.getuid()}/milo-phonon.sock"),
    Path(f"/tmp/milo-phonon-{os.getuid()}.sock"),
    Path(f"/tmp/milo-phonon-1000.sock"),
]


def get_active_socket() -> Optional[Path]:
    """Find the first responsive milo-phonon UNIX socket."""
    for sock in CANDIDATE_SOCKETS:
        if sock.exists():
            try:
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                    s.settimeout(0.4)
                    s.connect(str(sock))
                    s.sendall(json.dumps({"action": "ping"}).encode("utf-8") + b"\n")
                    data = s.recv(2048)
                    resp = json.loads(data.decode("utf-8").strip())
                    if resp.get("status") == "ok":
                        return sock
            except Exception:
                pass
    return None


def is_daemon_running() -> bool:
    """Check if the resident milo-phonon daemon is responsive."""
    return get_active_socket() is not None


def request_transcribe_file(file_path: Union[str, Path], hotwords: Optional[List[str]] = None) -> Dict[str, Any]:
    """Transcribe via daemon socket if available, otherwise direct execution."""
    path_str = str(Path(file_path).expanduser().resolve())
    active_sock = get_active_socket()

    if active_sock:
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.settimeout(300.0)
                s.connect(str(active_sock))
                req = {"action": "transcribe_file", "path": path_str, "hotwords": hotwords}
                s.sendall(json.dumps(req).encode("utf-8") + b"\n")

                buf = b""
                while not buf.endswith(b"\n"):
                    chunk = s.recv(4096)
                    if not chunk:
                        break
                    buf += chunk

                if buf:
                    return json.loads(buf.decode("utf-8").strip())
        except Exception:
            pass

    # Direct inline engine fallback
    from engine import PhononEngine
    engine = PhononEngine.get_instance()
    res = engine.transcribe_file(path_str, hotwords=hotwords)
    res["status"] = "ok"
    return res


def request_transcribe_bytes(wav_bytes: bytes, hotwords: Optional[List[str]] = None) -> Dict[str, Any]:
    """Transcribe raw audio bytes via daemon socket if available."""
    active_sock = get_active_socket()

    if active_sock:
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.settimeout(120.0)
                s.connect(str(active_sock))
                b64 = base64.b64encode(wav_bytes).decode("ascii")
                req = {"action": "transcribe_bytes", "data_b64": b64, "hotwords": hotwords}
                s.sendall(json.dumps(req).encode("utf-8") + b"\n")

                buf = b""
                while not buf.endswith(b"\n"):
                    chunk = s.recv(4096)
                    if not chunk:
                        break
                    buf += chunk

                if buf:
                    return json.loads(buf.decode("utf-8").strip())
        except Exception:
            pass

    # Direct inline engine fallback
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(wav_bytes)
        tmp_path = tmp.name

    try:
        from engine import PhononEngine
        engine = PhononEngine.get_instance()
        res = engine.transcribe_file(tmp_path, hotwords=hotwords)
        res["status"] = "ok"
        return res
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
