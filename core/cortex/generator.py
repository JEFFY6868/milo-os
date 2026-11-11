#!/usr/bin/env python3
"""
Milo Cognitive Core (Cortex) — Natural Language Generator & Streamer
Multi-backend generator supporting real-time streaming:
  1. Resident Daemon UNIX Socket (zero cold-start, sub-second latency)
  2. Local In-Process Llama-CPP with Qwen2.5-0.5B GGUF (offline fallback)
  3. Gemini-2.5-flash-lite fallback (instant cloud generation via eyes.env)
  4. Structured Fact Synthesis fallback (zero dependencies, 100% offline)
"""

import sys
import os
import json
import socket
from pathlib import Path
from typing import Optional, List, Dict, Any, Generator

# Ensure access to milo venv
if "/usr/lib/python3.14/site-packages" not in sys.path:
    sys.path.append("/usr/lib/python3.14/site-packages")
sys.path.insert(0, str(Path.home() / ".local/share/milo/cortex"))

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
CONFIG_ENV_PATH = Path.home() / ".config" / "milo" / "eyes.env"

# Socket Path resolution with multi-path discovery
def get_socket_path() -> Path:
    xdg = os.environ.get("XDG_RUNTIME_DIR")
    if xdg:
        p = Path(xdg) / "milo-cortex.sock"
        if p.exists():
            return p
    tmp_p = Path(f"/tmp/milo-cortex-{os.getuid()}.sock")
    if tmp_p.exists():
        return tmp_p
    if xdg and Path(xdg).exists() and os.access(xdg, os.W_OK):
        return Path(xdg) / "milo-cortex.sock"
    return tmp_p

SYSTEM_PROMPT = """You are Milo Cortex, a fast and helpful personal AI assistant on Arch Linux.
Answer the user's question clearly and concisely in 1-2 short sentences using the verified facts.
Do not repeat lines or commands in a loop."""


class CortexGenerator:
    def __init__(self):
        self.local_llm = None
        self._local_llm_attempted = False

    def _stream_daemon(self, query: str, context_facts: str = "", web_snippets: str = "") -> Generator[str, None, None]:
        """Stream completion tokens from resident daemon over UNIX domain socket."""
        sock_path = get_socket_path()
        if not sock_path.exists():
            return

        sock = None
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            sock.connect(str(sock_path))
            sock.settimeout(15.0)  # Streaming timeout

            req = {
                "action": "synthesize",
                "query": query,
                "context_facts": context_facts,
                "web_snippets": web_snippets,
                "max_tokens": 180,
                "temperature": 0.3
            }
            sock.sendall((json.dumps(req) + "\n").encode("utf-8"))

            buffer = ""
            while True:
                data = sock.recv(1024)
                if not data:
                    break
                buffer += data.decode("utf-8")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        resp = json.loads(line)
                        if "chunk" in resp:
                            yield resp["chunk"]
                        elif resp.get("done"):
                            return
                        elif "error" in resp:
                            return
                    except json.JSONDecodeError:
                        continue
        except Exception:
            return
        finally:
            if sock:
                try:
                    sock.close()
                except Exception:
                    pass

    def _init_local_model(self):
        """Lazy load local GGUF model via llama_cpp only if daemon is down."""
        if self._local_llm_attempted:
            return
        self._local_llm_attempted = True

        if LOCAL_GGUF_PATH.exists():
            try:
                os.environ["LLAMA_CPP_LIB"] = "/usr/lib/libllama.so"
                os.environ["GGML_VK_VISIBLE_DEVICES"] = "1"
                try:
                    import ctypes
                    ggml = ctypes.CDLL("/usr/lib/libggml.so")
                    ggml.ggml_backend_load_all()
                except Exception:
                    pass

                from llama_cpp import Llama
                self.local_llm = Llama(
                    model_path=str(LOCAL_GGUF_PATH),
                    n_gpu_layers=99,
                    n_ctx=512,
                    n_threads=4,
                    n_batch=512,
                    verbose=False
                )
            except Exception:
                self.local_llm = None

    def _stream_local_llm(self, user_prompt: str) -> Generator[str, None, None]:
        self._init_local_model()
        if not self.local_llm:
            return
        try:
            stream = self.local_llm.create_chat_completion(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=180,
                temperature=0.3,
                top_p=0.9,
                repeat_penalty=1.2,
                stream=True
            )
            for chunk in stream:
                delta = chunk["choices"][0].get("delta", {})
                content = delta.get("content")
                if content:
                    yield content
        except Exception:
            return

    def _stream_gemini(self, user_prompt: str) -> Generator[str, None, None]:
        if not CONFIG_ENV_PATH.exists():
            return
        try:
            api_key = None
            with open(CONFIG_ENV_PATH, "r") as f:
                for line in f:
                    if line.startswith("GEMINI_API_KEY="):
                        api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break

            if not api_key:
                return

            from google import genai
            client = genai.Client(api_key=api_key)
            response_stream = client.models.generate_content_stream(
                model="gemini-2.5-flash-lite",
                contents=f"{SYSTEM_PROMPT}\n\n{user_prompt}"
            )
            for chunk in response_stream:
                if chunk.text:
                    yield chunk.text
        except Exception:
            return

    def stream_synthesize(self, query: str, mode: str, context_facts: str = "", web_snippets: str = "") -> Generator[str, None, None]:
        """
        Streams response tokens in real-time according to intelligence mode:
        - 'online': Gemini Cloud first with local daemon fallback.
        - 'offline': Local Resident Daemon only (100% offline, 0ms network).
        - 'auto': Checks network probe (0.1ms). Online -> Gemini; Offline -> Local Daemon.
        """
        try:
            from intelligence_router import get_mode, is_online
            intel_mode = get_mode()
            online = is_online()
        except Exception:
            intel_mode = "auto"
            online = False

        prompt_parts = [f"Question: {query}"]
        if context_facts:
            prompt_parts.append(f"\n[Verified Local Memory Facts]:\n{context_facts}")
        if web_snippets:
            prompt_parts.append(f"\n[Latest Web Discoveries]:\n{web_snippets}")
        full_prompt = "\n".join(prompt_parts)

        # 1. Mode: ONLINE or AUTO (when online) -> Prefer Gemini Cloud
        if intel_mode == "online" or (intel_mode == "auto" and online):
            generated = False
            for token in self._stream_gemini(full_prompt):
                generated = True
                yield token
            if generated:
                return

        # 2. Mode: OFFLINE or AUTO (when offline) or Cloud Fallback -> Resident Local Daemon
        generated = False
        for token in self._stream_daemon(query, context_facts, web_snippets):
            generated = True
            yield token
        if generated:
            return

        # 3. Try In-Process Local GGUF LLM if daemon is down
        for token in self._stream_local_llm(full_prompt):
            generated = True
            yield token
        if generated:
            return

        # 4. Direct Fact Formatter Fallback
        if context_facts:
            yield context_facts
        elif web_snippets:
            yield web_snippets
        else:
            yield "No verified context available for this topic yet."

    def synthesize(self, query: str, mode: str, context_facts: str = "", web_snippets: str = "") -> str:
        """Non-streaming convenience wrapper."""
        chunks = list(self.stream_synthesize(query, mode, context_facts, web_snippets))
        return "".join(chunks).strip()


if __name__ == "__main__":
    gen = CortexGenerator()
    print("Testing streaming output:")
    for t in gen.stream_synthesize("Btrfs subvolume command", "MASTERED", context_facts="command: btrfs subvolume create @home"):
        sys.stdout.write(t)
        sys.stdout.flush()
    print("\n[Done]")
