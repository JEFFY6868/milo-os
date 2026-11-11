#!/usr/bin/env python3
"""
Milo Cognitive Core (Cortex) — Local Knowledge Engine
Offline-first Linux documentation and personal vault resolver:
  Tier 1: Personal Milo Notes Vault (vector + FTS5 hybrid search via MiloBrainEngine)
  Tier 2: System Command Syntax & Subcommand Help (--help extractor in <5ms)
  Tier 3: Local System Manpage Decompressor (/usr/share/man/**/*.gz via gzip)
"""

import sys
import os
import re
import gzip
import time
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List

# Ensure access to milo brain and cortex
sys.path.insert(0, str(Path.home() / ".local/share/milo/brain"))
sys.path.insert(0, str(Path.home() / ".local/share/milo/cortex"))

KNOWN_COMMANDS = {
    "btrfs", "pacman", "hyprctl", "ffmpeg", "systemctl", "journalctl",
    "git", "ip", "nmcli", "tar", "find", "grep", "sed", "awk", "curl",
    "chmod", "chown", "ss", "lsof", "foot", "kdenlive", "mpv", "grim",
    "slurp", "wl-copy", "wl-paste", "udisksctl", "mount", "umount", "lsblk",
    "fdisk", "mkfs.btrfs", "zramctl", "timedatectl", "localectl", "hostnamectl"
}

MAN_DIRS = [
    Path("/usr/share/man/man1"),
    Path("/usr/share/man/man8"),
    Path("/usr/share/man/man5"),
    Path("/usr/share/man/man7"),
    Path("/usr/share/man/man2"),
]


class LocalKnowledgeEngine:
    def __init__(self):
        self.brain = None
        self._init_brain()

    def _init_brain(self):
        try:
            from engine import MiloBrainEngine
            self.brain = MiloBrainEngine()
        except Exception:
            self.brain = None

    def search_vault(self, query: str) -> Optional[Dict[str, Any]]:
        """Search personal Milo Notes vault via Milo Semantic Brain."""
        if not self.brain:
            return None

        t0 = time.perf_counter()
        try:
            results = self.brain.hybrid_search(query, limit=3)
            latency_ms = (time.perf_counter() - t0) * 1000

            # Filter for notes inside MiloNotes with strong relevance
            for top in results:
                file_path = Path(top.get("path", ""))
                score = top.get("score", 0)
                # Must be inside MiloNotes or have high semantic score
                is_vault = "MiloNotes" in str(file_path) or file_path.suffix == ".md"
                if is_vault and score > 0.20:
                    # Read excerpt from file
                    content = ""
                    if file_path.exists():
                        try:
                            text = file_path.read_text(encoding="utf-8", errors="ignore")
                            lines = [l for l in text.splitlines() if l.strip() and not l.startswith("# ")]
                            content = "\n".join(lines[:10])
                        except Exception:
                            content = top.get("snippet", "")
                    else:
                        content = top.get("snippet", "")

                    if len(content) > 400:
                        content = content[:397] + "..."

                    return {
                        "source": "Milo Notes Vault",
                        "title": file_path.name if file_path else "Personal Vault Note",
                        "path": str(file_path),
                        "content": content.strip(),
                        "score": score,
                        "latency_ms": round(latency_ms, 1)
                    }
        except Exception:
            pass
        return None

    def search_cli_help(self, query: str) -> Optional[Dict[str, Any]]:
        """Extract instant flags and syntax for installed command line tools."""
        t0 = time.perf_counter()
        words = re.findall(r"[a-z0-9_-]+", query.lower())

        target_cmd = None
        target_subcmd = None

        for idx, w in enumerate(words):
            if w in KNOWN_COMMANDS and shutil.which(w):
                target_cmd = w
                # Check if next word is a subcommand
                if idx + 1 < len(words) and len(words[idx + 1]) >= 3:
                    candidate = words[idx + 1]
                    if candidate not in {"how", "can", "the", "command", "flags", "options"}:
                        target_subcmd = candidate
                break

        if not target_cmd:
            return None

        # Build execution command
        cmd_args = [target_cmd]
        if target_subcmd:
            cmd_args.append(target_subcmd)
        cmd_args.append("--help")

        try:
            proc = subprocess.run(
                cmd_args,
                capture_output=True,
                text=True,
                timeout=0.4
            )
            out = proc.stdout or proc.stderr
            if out and len(out.strip()) > 30:
                latency_ms = (time.perf_counter() - t0) * 1000
                lines = out.strip().splitlines()
                # Keep first 15 lines of concise help
                summary = "\n".join(lines[:15])
                if len(summary) > 600:
                    summary = summary[:597] + "..."

                title_str = f"{target_cmd} {target_subcmd}".strip()
                return {
                    "source": "System Command Syntax",
                    "title": f"`{title_str} --help`",
                    "path": shutil.which(target_cmd),
                    "content": summary,
                    "latency_ms": round(latency_ms, 1)
                }
        except Exception:
            pass

        return None

    def search_manpage(self, query: str) -> Optional[Dict[str, Any]]:
        """Decompress and parse local manpage sections using standard gzip."""
        t0 = time.perf_counter()
        words = re.findall(r"[a-z0-9_-]+", query.lower())

        target_cmd = None
        for w in words:
            if len(w) >= 3 and w in KNOWN_COMMANDS:
                target_cmd = w
                break

        if not target_cmd:
            return None

        # Look for matching manpage in /usr/share/man
        for d in MAN_DIRS:
            if not d.exists():
                continue
            for p in d.glob(f"{target_cmd}.*.gz"):
                try:
                    with gzip.open(p, "rt", encoding="utf-8", errors="ignore") as f:
                        text = f.read(4096)  # Read first 4KB for Name/Synopsis
                        # Clean roff formatting macros (.TH, .SH, .B, .I, etc.)
                        clean_lines = []
                        for line in text.splitlines():
                            line_s = line.strip()
                            if not line_s or line_s.startswith((".", "'\\\"")):
                                # Extract header text if .SH
                                if line_s.startswith(".SH "):
                                    clean_lines.append(f"\n[{line_s[4:].strip('\"')}]")
                                continue
                            # Remove bold/italic inline roff tags: \fB, \fI, \fR
                            clean_line = re.sub(r"\\f[BIRP]", "", line_s)
                            clean_line = re.sub(r"\\e", "\\", clean_line)
                            clean_lines.append(clean_line)

                        summary = "\n".join(clean_lines[:15]).strip()
                        if summary and len(summary) > 40:
                            latency_ms = (time.perf_counter() - t0) * 1000
                            return {
                                "source": "Arch Linux Manpages",
                                "title": f"man {p.name}",
                                "path": str(p),
                                "content": summary[:600],
                                "latency_ms": round(latency_ms, 1)
                            }
                except Exception:
                    pass

        return None

    def resolve(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Unified Local Knowledge Resolver:
        Priority 1: System Command CLI Help (<5ms)
        Priority 2: Personal Milo Notes Vault (<15ms)
        Priority 3: Local System Manpages (<20ms)
        """
        # 1. System CLI Help (fastest, exact version syntax)
        res = self.search_cli_help(query)
        if res:
            return res

        # 2. Personal Vault (highest customized value)
        res = self.search_vault(query)
        if res:
            return res

        # 3. Manpages
        res = self.search_manpage(query)
        if res:
            return res

        return None


if __name__ == "__main__":
    eng = LocalKnowledgeEngine()

    test_queries = [
        "How do I create a btrfs subvolume?",
        "Hyprland keybindings",
        "pacman package search options"
    ]

    for q in test_queries:
        print(f"\nQuery: {q}")
        r = eng.resolve(q)
        if r:
            print(f"✔ Found in {r['source']} ({r['latency_ms']}ms): {r['title']}")
            print(f"Content preview:\n{r['content'][:150]}...\n")
        else:
            print("❌ No local knowledge found.")
