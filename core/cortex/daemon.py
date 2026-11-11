#!/usr/bin/env python3
"""
Milo Cognitive Core (Cortex) — Resident LLM Daemon
Keeps the Qwen2.5-0.5B local GGUF model warm in resident memory to eliminate
cold-start delays and provide sub-second token streaming via UNIX domain socket.

Socket Path: /run/user/<UID>/milo-cortex.sock (or /tmp/milo-cortex-<UID>.sock)
Protocol: Line-delimited JSON over UNIX Domain Socket
"""

import sys
import os
import json
import socket
import socketserver
import signal
import time
import threading
from pathlib import Path
from typing import Dict, Any

# Ensure cortex and venv paths are available
sys.path.insert(0, str(Path.home() / ".local/share/milo/cortex"))
if "/usr/lib/python3.14/site-packages" not in sys.path:
    sys.path.append("/usr/lib/python3.14/site-packages")

MODEL_DIR = Path.home() / ".local" / "share" / "models"
ACTIVE_MODEL_PATH = MODEL_DIR / "qwen2.5-0.5b-cortex-active.gguf"
OPERATED_MODEL_PATH = MODEL_DIR / "qwen2.5-0.5b-cortex-milo.gguf"
BASE_MODEL_PATH = MODEL_DIR / "qwen2.5-0.5b-instruct-q4_k_m.gguf"

if ACTIVE_MODEL_PATH.exists():
    LOCAL_GGUF_PATH = ACTIVE_MODEL_PATH
elif OPERATED_MODEL_PATH.exists():
    LOCAL_GGUF_PATH = OPERATED_MODEL_PATH
else:
    LOCAL_GGUF_PATH = BASE_MODEL_PATH

# Socket Path resolution
RUNTIME_DIR = os.environ.get("XDG_RUNTIME_DIR")
if RUNTIME_DIR and Path(RUNTIME_DIR).exists():
    SOCKET_PATH = Path(RUNTIME_DIR) / "milo-cortex.sock"
else:
    SOCKET_PATH = Path(f"/tmp/milo-cortex-{os.getuid()}.sock")

PID_FILE = Path.home() / ".local" / "share" / "milo" / "cortex" / "daemon.pid"

SYSTEM_PROMPT = """You are Milo Cortex, a fast and helpful personal AI assistant on Arch Linux.
Answer the user's question clearly and concisely in 1-2 short sentences using the verified facts.
Do not repeat lines or commands in a loop."""


class ResidentModel:
    """Singleton wrapper for resident GGUF model in memory."""
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self.llm = None
        self.start_time = time.time()
        self.queries_served = 0
        self.total_tokens_generated = 0
        self.load_model()

    def load_model(self):
        print(f"🧠 [Cortex Daemon] Loading local GGUF into memory on GPU: {LOCAL_GGUF_PATH.name}...")
        t0 = time.time()
        os.environ["LLAMA_CPP_LIB"] = "/usr/lib/libllama.so"
        os.environ["GGML_VK_VISIBLE_DEVICES"] = "1"
        try:
            import ctypes
            ggml = ctypes.CDLL("/usr/lib/libggml.so")
            ggml.ggml_backend_load_all()
        except Exception:
            pass

        try:
            from llama_cpp import Llama
            gpu_layers = int(os.environ.get("CORTEX_GPU_LAYERS", "0"))
            self.llm = Llama(
                model_path=str(LOCAL_GGUF_PATH),
                n_gpu_layers=gpu_layers,
                n_ctx=512,
                n_threads=4,
                n_batch=512,
                verbose=False
            )
            # Warmup KV cache & graph pre-allocation
            try:
                for _ in self.llm.create_chat_completion(
                    messages=[{"role": "user", "content": "hi"}],
                    max_tokens=2,
                    stream=True
                ):
                    pass
            except Exception:
                pass
            print(f"✨ [Cortex Daemon] Model resident and warm on GPU in {time.time() - t0:.2f}s!")
        except Exception as e:
            print(f"❌ [Cortex Daemon] Failed to load local model on GPU: {e}")
            self.llm = None

    def stream_completion(self, user_prompt: str, max_tokens: int = 180, temperature: float = 0.3):
        with self._lock:
            if not self.llm:
                yield {"error": "Local LLM not loaded"}
                return

            try:
                stream = self.llm.create_chat_completion(
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=0.9,
                    repeat_penalty=1.2,
                    stream=True
                )
                self.queries_served += 1
                token_count = 0
                for chunk in stream:
                    delta = chunk["choices"][0].get("delta", {})
                    content = delta.get("content")
                    if content:
                        token_count += 1
                        yield {"chunk": content}
                self.total_tokens_generated += token_count
                yield {"done": True, "tokens": token_count}
            except Exception as e:
                yield {"error": str(e)}


_resident_model: ResidentModel = None


class CortexSocketHandler(socketserver.StreamRequestHandler):
    """Handles JSON requests over UNIX socket."""

    def handle(self):
        global _resident_model
        try:
            line = self.rfile.readline().decode("utf-8").strip()
            if not line:
                return

            req = json.loads(line)
            action = req.get("action", "synthesize")

            if action == "ping":
                uptime = time.time() - _resident_model.start_time
                resp = {
                    "status": "pong",
                    "model": "Qwen2.5-0.5B-Instruct",
                    "uptime_sec": round(uptime, 1),
                    "queries_served": _resident_model.queries_served,
                    "total_tokens": _resident_model.total_tokens_generated,
                    "resident": _resident_model.llm is not None
                }
                self.wfile.write((json.dumps(resp) + "\n").encode("utf-8"))
                self.wfile.flush()
                return

            elif action == "status":
                resp = {
                    "status": "ok",
                    "model_path": str(LOCAL_GGUF_PATH),
                    "queries_served": _resident_model.queries_served,
                    "total_tokens": _resident_model.total_tokens_generated,
                    "socket": str(SOCKET_PATH),
                    "threads": 4,
                    "ctx_size": 512
                }
                self.wfile.write((json.dumps(resp) + "\n").encode("utf-8"))
                self.wfile.flush()
                return

            elif action == "synthesize":
                query = req.get("query", "")
                context_facts = req.get("context_facts", "")
                web_snippets = req.get("web_snippets", "")
                max_tokens = int(req.get("max_tokens", 180))
                temperature = float(req.get("temperature", 0.3))

                # Build full prompt
                prompt_parts = [f"Question: {query}"]
                if context_facts:
                    prompt_parts.append(f"\n[Verified Local Memory Facts]:\n{context_facts}")
                if web_snippets:
                    prompt_parts.append(f"\n[Latest Web Discoveries]:\n{web_snippets}")
                full_prompt = "\n".join(prompt_parts)

                # Stream tokens
                for payload in _resident_model.stream_completion(full_prompt, max_tokens, temperature):
                    out_line = json.dumps(payload) + "\n"
                    self.wfile.write(out_line.encode("utf-8"))
                    self.wfile.flush()
            else:
                resp = {"error": f"Unknown action: {action}"}
                self.wfile.write((json.dumps(resp) + "\n").encode("utf-8"))
                self.wfile.flush()

        except Exception as e:
            err = {"error": str(e)}
            try:
                self.wfile.write((json.dumps(err) + "\n").encode("utf-8"))
                self.wfile.flush()
            except Exception:
                pass


class ThreadedUnixServer(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True


def cleanup_socket():
    if SOCKET_PATH.exists():
        try:
            SOCKET_PATH.unlink()
        except Exception:
            pass
    if PID_FILE.exists():
        try:
            PID_FILE.unlink()
        except Exception:
            pass


def signal_handler(sig, frame):
    print(f"\n🛑 [Cortex Daemon] Received signal {sig}, shutting down...")
    cleanup_socket()
    sys.exit(0)


def run_daemon():
    global _resident_model

    # Cleanup any stale socket
    cleanup_socket()
    SOCKET_PATH.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print(f"🚀 [Cortex Daemon] Starting Milo Cognitive Core Resident Daemon...")
    _resident_model = ResidentModel()

    server = ThreadedUnixServer(str(SOCKET_PATH), CortexSocketHandler)

    # Write PID
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    # Ensure socket has user rw permissions
    os.chmod(str(SOCKET_PATH), 0o600)

    print(f"📡 [Cortex Daemon] Listening on UNIX domain socket: {SOCKET_PATH}")
    print(f"⚡ [Cortex Daemon] Ready for zero-cold-start inference requests.")

    try:
        server.serve_forever()
    finally:
        cleanup_socket()


if __name__ == "__main__":
    run_daemon()
