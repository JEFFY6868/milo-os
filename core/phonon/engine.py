#!/usr/bin/env python3
"""
Milo Phonon Engine — Offline 2.1-bit QAT Speech Recognition
Wraps Fermion Research's Phonon-2 model (164 MB) for zero-cloud, sub-second
ASR on local CPU (AVX2 native kernels).
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

# Ensure dependencies from phonon-env are importable if run from external python
ENV_SITE_PACKAGES = Path.home() / ".local/share/milo/phonon-env/lib/python3.12/site-packages"
if ENV_SITE_PACKAGES.exists() and str(ENV_SITE_PACKAGES) not in sys.path:
    sys.path.insert(0, str(ENV_SITE_PACKAGES))

from fermion import _catalog
from fermion._speech import backends

MODEL_CACHE_DIR = Path.home() / ".cache/fermion/speech/FermionResearch__Phonon-2/model_phonon2_c4c_int6"
DEFAULT_HOTWORDS = ["Milo", "Arch Linux", "Hyprland", "Ena Di Solra", "Cortex", "Omarchy", "Wayland"]


def format_timestamp_srt(seconds: float) -> str:
    """Format seconds into SRT timestamp: HH:MM:SS,mmm"""
    millis = int(round((seconds - int(seconds)) * 1000))
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def format_timestamp_vtt(seconds: float) -> str:
    """Format seconds into WebVTT timestamp: HH:MM:SS.mmm"""
    millis = int(round((seconds - int(seconds)) * 1000))
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


class PhononEngine:
    """Resident Phonon-2 Speech Recognition Engine."""
    _instance = None

    def __init__(self, model_dir: Optional[Union[str, Path]] = None, threads: Optional[int] = None):
        self.model_dir = Path(model_dir) if model_dir else MODEL_CACHE_DIR
        if not self.model_dir.exists():
            raise FileNotFoundError(f"Phonon-2 model directory not found at: {self.model_dir}")

        if threads:
            os.environ["FERMION_CPU_THREADS"] = str(int(threads))

        print(f"🎙️ [Phonon Engine] Loading Phonon-2 ({self.model_dir.name})...")
        t0 = time.time()
        pin = _catalog.SPEECH_PROFILES["five-value"]
        self.speech = backends.load(
            "cpu",
            self.model_dir,
            profile="five-value",
            backend=pin["backend"],
            quiet=True
        )
        self.load_time = time.time() - t0
        print(f"✅ [Phonon Engine] Loaded in {self.load_time:.2f}s (AVX2 native, CPU).")

        # Set default system hotwords
        self.set_hotwords(DEFAULT_HOTWORDS)

    @classmethod
    def get_instance(cls, model_dir: Optional[Union[str, Path]] = None, threads: Optional[int] = None) -> "PhononEngine":
        """Singleton accessor to reuse resident warm model."""
        if cls._instance is None:
            cls._instance = PhononEngine(model_dir=model_dir, threads=threads)
        return cls._instance

    def set_hotwords(self, words: List[str], lam: float = 2.0) -> int:
        """Inject domain vocabulary / hotwords to favor correct spelling."""
        if hasattr(self.speech, "set_hotwords"):
            return self.speech.set_hotwords(words, lam=lam)
        return 0

    def transcribe_file(self, audio_path: Union[str, Path], hotwords: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Transcribe an audio file (.wav, .flac, .ogg, .mp3, etc.).
        Returns text, segment timestamps, word timestamps, and metrics.
        """
        audio_file = Path(audio_path).expanduser().resolve()
        if not audio_file.is_file():
            raise FileNotFoundError(f"Audio file not found: {audio_file}")

        if hotwords:
            self.set_hotwords(hotwords)

        t0 = time.time()
        result = self.speech.transcribe_detailed(str(audio_file))
        wall_time = time.time() - t0

        text, decode_s, duration_s = result.triple()

        return {
            "text": text.strip(),
            "duration_seconds": duration_s,
            "decode_seconds": decode_s,
            "wall_seconds": wall_time,
            "realtime_factor": (duration_s / decode_s) if decode_s > 0 else 0.0,
            "segment_count": len(result.segments),
            "segments": result.segments,
            "words": getattr(result, "words", []),
            "truncated": getattr(result, "truncated", False)
        }

    def transcribe_array(self, audio_data, sample_rate: int = 16000, hotwords: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Transcribe an in-memory numpy array of float32 or int16 samples (16kHz mono).
        """
        if hotwords:
            self.set_hotwords(hotwords)

        t0 = time.time()
        result = self.speech.transcribe_array_detailed(audio_data, sample_rate=sample_rate)
        wall_time = time.time() - t0

        text, decode_s, duration_s = result.triple()

        return {
            "text": text.strip(),
            "duration_seconds": duration_s,
            "decode_seconds": decode_s,
            "wall_seconds": wall_time,
            "realtime_factor": (duration_s / decode_s) if decode_s > 0 else 0.0,
            "segment_count": len(result.segments),
            "segments": result.segments,
            "words": getattr(result, "words", []),
            "truncated": getattr(result, "truncated", False)
        }

    def generate_srt(self, result: Dict[str, Any], max_words_per_line: int = 10) -> str:
        """Convert transcription segments into standard SubRip (.srt) text."""
        lines = []
        segments = result.get("segments", [])

        idx = 1
        for seg in segments:
            text = seg.get("text", "").strip()
            if not text:
                continue

            start_t = format_timestamp_srt(seg.get("start", 0.0))
            end_t = format_timestamp_srt(seg.get("end", 0.0))

            lines.append(f"{idx}")
            lines.append(f"{start_t} --> {end_t}")
            lines.append(text)
            lines.append("")
            idx += 1

        return "\n".join(lines)

    def generate_vtt(self, result: Dict[str, Any]) -> str:
        """Convert transcription segments into standard WebVTT (.vtt) text."""
        lines = ["WEBVTT", ""]
        segments = result.get("segments", [])

        idx = 1
        for seg in segments:
            text = seg.get("text", "").strip()
            if not text:
                continue

            start_t = format_timestamp_vtt(seg.get("start", 0.0))
            end_t = format_timestamp_vtt(seg.get("end", 0.0))

            lines.append(f"{idx}")
            lines.append(f"{start_t} --> {end_t}")
            lines.append(text)
            lines.append("")
            idx += 1

        return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        audio_target = sys.argv[1]
        engine = PhononEngine.get_instance()
        res = engine.transcribe_file(audio_target)
        print("\n--- Transcription ---")
        print(res["text"])
        print(f"\n--- Metrics: {res['duration_seconds']:.2f}s audio in {res['decode_seconds']:.2f}s ({res['realtime_factor']:.1f}x realtime) ---")
    else:
        print("Usage: python3 engine.py <audio_file>")
