#!/usr/bin/env python3
"""
Milo Voice Resident Daemon (milo-voice-daemon)
High-performance resident Kokoro-82M TTS service.
Eliminates model load latency and provides instant speech synthesis.
"""

import sys
import os
import re
import json
import socket
import signal
import time
import threading
import subprocess
from pathlib import Path
import torch
import numpy as np

# Force offline mode for fast deterministic execution
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

CONFIG_PATH = Path.home() / ".config" / "milo" / "voice.json"
PID_FILE = Path(f"/tmp/milo-voice-{os.getuid()}.pid")

def get_socket_path() -> Path:
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
    if runtime_dir and Path(runtime_dir).exists():
        return Path(runtime_dir) / "milo-voice.sock"
    return Path(f"/tmp/milo-voice-{os.getuid()}.sock")

SOCKET_PATH = get_socket_path()

def clean_text_for_speech(text: str) -> str:
    """Prepares text for natural speech synthesis by removing code, markdown, and URLs."""
    if not text:
        return ""
    
    # Remove code blocks
    text = re.sub(r"```[\s\S]*?```", " Code block omitted. ", text)
    # Remove inline code
    text = re.sub(r"`([^`]+)`", r"\1", text)
    # Remove markdown links: [text](url) -> text
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    # Remove bare URLs
    text = re.sub(r"https?://\S+", "", text)
    # Remove markdown headers and bullets
    text = re.sub(r"^[#\*\-\+]\s+", "", text, flags=re.MULTILINE)
    # Remove markdown bold/italics
    text = re.sub(r"[\*_]{1,3}", "", text)
    # Remove excessive punctuation or special symbols
    text = re.sub(r"[✦★⚡●▪■]", "", text)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    
    # Cap maximum word count for assistant voice responses (prevent 10-minute monologues)
    words = text.split()
    if len(words) > 120:
        text = " ".join(words[:120]) + "... and so on."
        
    return text

class VoiceService:
    def __init__(self):
        self.lock = threading.Lock()
        self.playback_proc = None
        self.pipeline = None
        self.load_config()
        self.init_pipeline()

    def load_config(self):
        self.config = {
            "enabled": True,
            "voice": "bm_fable,am_adam",
            "speed": 1.0,
            "lang_code": "b"
        }
        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.config.update(data)
            except Exception as e:
                print(f"[VoiceDaemon] Error reading config: {e}", file=sys.stderr)

    def save_config(self):
        try:
            CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"[VoiceDaemon] Error saving config: {e}", file=sys.stderr)

    def init_pipeline(self):
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[VoiceDaemon] Loading Kokoro-82M pipeline on {device} (lang: {self.config['lang_code']})...")
        t0 = time.time()
        from kokoro import KPipeline
        self.pipeline = KPipeline(
            lang_code=self.config.get("lang_code", "b"),
            repo_id="hexgrad/Kokoro-82M",
            device=device
        )
        # Warmup GPU
        try:
            list(self.pipeline("warmup", voice=self.config.get("voice", "bm_fable,am_adam"), speed=1.0))
        except Exception:
            pass
        print(f"[VoiceDaemon] Model warm and ready on {device} in {time.time() - t0:.2f}s.")

    def stop_playback(self):
        with self.lock:
            if self.playback_proc and self.playback_proc.poll() is None:
                try:
                    self.playback_proc.kill()
                    self.playback_proc.wait(timeout=0.3)
                except Exception:
                    pass
                self.playback_proc = None
                return True
        return False

    def is_speaking(self) -> bool:
        with self.lock:
            return bool(self.playback_proc and self.playback_proc.poll() is None)

    def speak(self, raw_text: str, voice_override: str = None, speed_override: float = None) -> bool:
        self.load_config()
        if not self.config.get("enabled", True):
            print("[VoiceDaemon] Voice is disabled in config. Skipping speech.")
            return False

        clean_text = clean_text_for_speech(raw_text)
        if not clean_text:
            return False

        voice = voice_override or self.config.get("voice", "bm_fable,am_adam")
        speed = speed_override or float(self.config.get("speed", 1.0))

        # Stop any existing playback before starting new speech
        self.stop_playback()

        try:
            import numpy as np

            t0 = time.time()
            generator = self.pipeline(clean_text, voice=voice, speed=speed)

            # Start real-time raw audio streaming into PipeWire via pw-cat
            with self.lock:
                proc = subprocess.Popen(
                    ["pw-cat", "-p", "--raw", "--rate", "24000", "--channels", "1", "--format", "f32", "-"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                self.playback_proc = proc

            total_chunks = 0
            t_first = None
            for _, _, chunk in generator:
                with self.lock:
                    if self.playback_proc is not proc or proc.poll() is not None:
                        break
                if chunk is not None and len(chunk) > 0:
                    if t_first is None:
                        t_first = time.time() - t0
                        print(f"[VoiceDaemon] Time to first audio chunk: {t_first:.3f}s (TTFA)")
                    try:
                        if hasattr(chunk, "detach"):
                            raw_bytes = chunk.detach().cpu().to(torch.float32).numpy().tobytes()
                        elif isinstance(chunk, np.ndarray):
                            raw_bytes = chunk.astype(np.float32).tobytes()
                        else:
                            raw_bytes = np.array(chunk, dtype=np.float32).tobytes()

                        proc.stdin.write(raw_bytes)
                        proc.stdin.flush()
                        total_chunks += 1
                    except Exception as ex:
                        print(f"[VoiceDaemon] Chunk write error: {ex}", file=sys.stderr)
                        break

            try:
                if proc.stdin:
                    proc.stdin.close()
            except Exception:
                pass

            gen_time = time.time() - t0
            print(f"[VoiceDaemon] Synthesized and streamed {len(clean_text)} chars ({total_chunks} chunks) in {gen_time:.2f}s using {voice}.")
            return total_chunks > 0
        except Exception as e:
            print(f"[VoiceDaemon] Synthesis failed: {e}", file=sys.stderr)
            return False

voice_service = None

def handle_client(conn):
    global voice_service
    try:
        data = conn.recv(16384)
        if not data:
            return
        req = json.loads(data.decode("utf-8"))
        action = req.get("action", "")

        if action == "ping":
            conn.sendall(json.dumps({"status": "pong"}).encode() + b"\n")

        elif action == "speak":
            text = req.get("text", "")
            voice = req.get("voice")
            speed = req.get("speed")
            success = voice_service.speak(text, voice_override=voice, speed_override=speed)
            conn.sendall(json.dumps({"status": "ok" if success else "failed"}).encode() + b"\n")

        elif action == "stop":
            stopped = voice_service.stop_playback()
            conn.sendall(json.dumps({"status": "stopped", "was_playing": stopped}).encode() + b"\n")

        elif action == "status":
            voice_service.load_config()
            conn.sendall(json.dumps({
                "status": "ok",
                "speaking": voice_service.is_speaking(),
                "enabled": voice_service.config.get("enabled", True),
                "voice": voice_service.config.get("voice", "bm_fable,am_adam"),
                "speed": voice_service.config.get("speed", 1.0)
            }).encode() + b"\n")

        elif action == "set_enabled":
            enabled = bool(req.get("enabled", True))
            voice_service.config["enabled"] = enabled
            voice_service.save_config()
            if not enabled:
                voice_service.stop_playback()
            conn.sendall(json.dumps({"status": "ok", "enabled": enabled}).encode() + b"\n")

        elif action == "set_voice":
            voice = str(req.get("voice", "bm_fable,am_adam"))
            voice_service.config["voice"] = voice
            voice_service.save_config()
            conn.sendall(json.dumps({"status": "ok", "voice": voice}).encode() + b"\n")

        else:
            conn.sendall(json.dumps({"status": "unknown_action"}).encode() + b"\n")

    except Exception as e:
        try:
            conn.sendall(json.dumps({"status": "error", "error": str(e)}).encode() + b"\n")
        except Exception:
            pass
    finally:
        conn.close()

def main():
    global voice_service
    
    # Write PID
    PID_FILE.write_text(str(os.getpid()))

    # Setup signal handlers
    def shutdown(sig, frame):
        print("\n[VoiceDaemon] Shutting down...")
        if SOCKET_PATH.exists():
            SOCKET_PATH.unlink()
        if PID_FILE.exists():
            PID_FILE.unlink()
        if voice_service:
            voice_service.stop_playback()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Initialize Service
    voice_service = VoiceService()

    # Clean old socket
    if SOCKET_PATH.exists():
        SOCKET_PATH.unlink()

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(str(SOCKET_PATH))
    server.listen(10)
    print(f"[VoiceDaemon] Listening on {SOCKET_PATH}")

    while True:
        try:
            conn, _ = server.accept()
            t = threading.Thread(target=handle_client, args=(conn,), daemon=True)
            t.start()
        except Exception as e:
            time.sleep(0.1)

if __name__ == "__main__":
    main()
