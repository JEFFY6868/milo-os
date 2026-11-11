#!/usr/bin/env python3
"""
Milo Evolution Engine — System & Capability Scanner (scanner.py)
Collects real-time diagnostic telemetry, detects performance bottlenecks,
mines Obsidian wishlists, runs doctor diagnostics, and surfaces self-upgrade/self-repair opportunities.
"""

import os
import sys
import json
import time
import socket
import sqlite3
import subprocess
from pathlib import Path
from typing import Dict, Any, List

MILO_DIR = Path.home() / ".local" / "share" / "milo"
OBSIDIAN_DIR = Path.home() / "MiloNotes"
PLUGIN_DIR = Path.home() / ".config" / "omarchy" / "plugins" / "jeffy.milo"


class MiloScanner:
    def __init__(self):
        self.timestamp = time.time()
        self.runtime_dir = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))

    def check_socket_latency(self, socket_path: Path, ping_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Measures ping/response latency for a UNIX domain socket."""
        if not socket_path.exists():
            return {"online": False, "latency_ms": -1, "error": "Socket not found"}

        t0 = time.time()
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(2.0)
            s.connect(str(socket_path))
            s.sendall(json.dumps(ping_payload).encode("utf-8") + b"\n")
            data = s.recv(4096)
            s.close()
            latency = (time.time() - t0) * 1000.0
            return {"online": True, "latency_ms": round(latency, 2), "response": data.decode("utf-8")[:100]}
        except Exception as e:
            return {"online": False, "latency_ms": -1, "error": str(e)}

    def check_gpu_telemetry(self) -> Dict[str, Any]:
        """Extracts live GPU metrics from nvidia-smi."""
        try:
            res = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,temperature.gpu,power.draw,memory.used,memory.free,memory.total",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=3
            )
            if res.returncode == 0:
                parts = [p.strip() for p in res.stdout.strip().split(",")]
                return {
                    "available": True,
                    "name": parts[0],
                    "temp_c": int(parts[1]),
                    "power_w": float(parts[2]),
                    "vram_used_mib": int(parts[3]),
                    "vram_free_mib": int(parts[4]),
                    "vram_total_mib": int(parts[5]),
                }
        except Exception as e:
            return {"available": False, "error": str(e)}
        return {"available": False}

    def check_system_memory(self) -> Dict[str, Any]:
        """Reads system RAM and swap stats."""
        try:
            with open("/proc/meminfo", "r") as f:
                lines = f.readlines()
            mem = {}
            for line in lines:
                parts = line.split(":")
                if len(parts) == 2:
                    key = parts[0].strip()
                    val = parts[1].strip().split()[0]
                    mem[key] = int(val)
            total = mem.get("MemTotal", 0) / 1024
            avail = mem.get("MemAvailable", 0) / 1024
            used = total - avail
            return {
                "ram_total_mb": round(total, 1),
                "ram_used_mb": round(used, 1),
                "ram_free_mb": round(avail, 1),
                "ram_usage_pct": round((used / total) * 100, 1) if total > 0 else 0
            }
        except Exception as e:
            return {"error": str(e)}

    def scan_git_repositories(self) -> List[Dict[str, Any]]:
        """Checks for uncommitted modifications or divergence in Milo repositories."""
        repos = [
            ("milo_core", MILO_DIR),
            ("milo_hud", PLUGIN_DIR),
        ]
        results = []
        for name, repo_path in repos:
            if (repo_path / ".git").exists():
                try:
                    res = subprocess.run(["git", "status", "-s"], cwd=str(repo_path), capture_output=True, text=True)
                    uncommitted = [l for l in res.stdout.split("\n") if l.strip()]
                    results.append({
                        "repo": name,
                        "path": str(repo_path),
                        "dirty": len(uncommitted) > 0,
                        "uncommitted_count": len(uncommitted),
                        "files": uncommitted[:5]
                    })
                except Exception as e:
                    results.append({"repo": name, "error": str(e)})
        return results

    def scan_obsidian_wishes(self) -> List[Dict[str, str]]:
        """Scans MiloNotes for user wishes tagged with #milo-wish, Wish:, or in Wishes.md."""
        wishes = []
        if not OBSIDIAN_DIR.exists():
            return wishes

        # 1. Check dedicated Wishes.md file
        wishes_file = OBSIDIAN_DIR / "Wishes.md"
        if wishes_file.exists():
            try:
                content = wishes_file.read_text(encoding="utf-8")
                for line in content.split("\n"):
                    clean = line.strip().lstrip("-* ").strip()
                    if clean and not clean.startswith("#") and len(clean) > 5:
                        wishes.append({"wish": clean, "source": "Wishes.md"})
            except Exception:
                pass

        # 2. Grep for #milo-wish or Wish: across notes
        try:
            res = subprocess.run(
                ["grep", "-rEihn", "(#milo-wish:?|Wish:)", str(OBSIDIAN_DIR)],
                capture_output=True, text=True, timeout=4
            )
            for line in res.stdout.split("\n"):
                raw = line.strip()
                if not raw:
                    continue
                # Extract text after the tag
                clean = re.sub(r"^.*?#(?:milo-wish:?|Wish:)\s*", "", raw, flags=re.IGNORECASE).strip()
                if clean and len(clean) > 5 and not any(w["wish"] == clean for w in wishes):
                    wishes.append({"wish": clean, "source": "MiloNotes"})
        except Exception:
            pass

        return wishes[:5]

    def run_doctor_diagnostics(self) -> List[Dict[str, Any]]:
        """Audits system health, crashed services, socket dropouts, and driver issues."""
        issues = []

        # 1. Check failed systemd user services
        try:
            res = subprocess.run(
                ["systemctl", "--user", "--failed", "--plain", "--no-legend"],
                capture_output=True, text=True, timeout=3
            )
            lines = [l.strip() for l in res.stdout.split("\n") if l.strip()]
            for line in lines:
                parts = line.split()
                if len(parts) >= 4:
                    unit_name = parts[0]
                    issues.append({
                        "category": "failed_service",
                        "unit": unit_name,
                        "description": f"Service {unit_name} is in failed state ({parts[3]})."
                    })
        except Exception:
            pass

        # 2. Check critical daemon sockets
        sockets_to_check = [
            ("milo-voice", self.runtime_dir / "milo-voice.sock"),
            ("milo-cortex", self.runtime_dir / "milo-cortex.sock"),
        ]
        for name, sock in sockets_to_check:
            if not sock.exists():
                issues.append({
                    "category": "socket_dropout",
                    "daemon": name,
                    "description": f"Daemon socket {sock.name} is missing."
                })

        # 3. Check disk space headroom (warn if root disk free < 5GB)
        try:
            res = subprocess.run(["df", "-B1G", "/"], capture_output=True, text=True)
            lines = res.stdout.strip().split("\n")
            if len(lines) >= 2:
                avail = int(lines[1].split()[3])
                if avail < 5:
                    issues.append({
                        "category": "disk_space",
                        "available_gb": avail,
                        "description": f"Root filesystem has only {avail}GB free space remaining."
                    })
        except Exception:
            pass

        return issues

    def benchmark_system_latencies(self) -> Dict[str, Any]:
        """Measures instant response times for Voice TTS, Cortex LLM, and GPU query."""
        voice_sock = self.runtime_dir / "milo-voice.sock"
        cortex_sock = self.runtime_dir / "milo-cortex.sock"

        bench = {
            "timestamp": time.time(),
            "voice_ping_ms": self.check_socket_latency(voice_sock, {"action": "ping"}).get("latency_ms", -1),
            "cortex_ping_ms": self.check_socket_latency(cortex_sock, {"prompt": "ping"}).get("latency_ms", -1),
        }

        # GPU query benchmark
        t0 = time.time()
        gpu_stat = self.check_gpu_telemetry()
        bench["gpu_query_ms"] = round((time.time() - t0) * 1000.0, 2)
        bench["gpu_available"] = gpu_stat.get("available", False)
        return bench

    def run_full_scan(self) -> Dict[str, Any]:
        """Executes full diagnostic and returns consolidated telemetry payload."""
        voice_sock = self.runtime_dir / "milo-voice.sock"
        cortex_sock = self.runtime_dir / "milo-cortex.sock"

        wishes = self.scan_obsidian_wishes()
        doctor_issues = self.run_doctor_diagnostics()
        benchmark = self.benchmark_system_latencies()

        report = {
            "timestamp": self.timestamp,
            "voice_service": self.check_socket_latency(voice_sock, {"action": "ping"}),
            "cortex_service": self.check_socket_latency(cortex_sock, {"prompt": "ping"}),
            "gpu": self.check_gpu_telemetry(),
            "system_memory": self.check_system_memory(),
            "repositories": self.scan_git_repositories(),
            "wishes": wishes,
            "doctor_issues": doctor_issues,
            "benchmark": benchmark,
            "opportunities": []
        }

        # Priority 1: Self-Repair (Doctor Issues)
        for issue in doctor_issues:
            report["opportunities"].append({
                "type": "self_repair",
                "domain": "system_doctor",
                "title": f"Milo Doctor Repair: {issue.get('description')}",
                "reason": issue.get("description"),
                "priority": "critical",
                "issue_data": issue
            })

        # Priority 2: User Wishes (Thought-to-Code Pipeline)
        for w in wishes:
            report["opportunities"].append({
                "type": "user_wish",
                "domain": "thought_to_code",
                "title": f"Milo Feature Genesis: {w['wish'][:60]}",
                "reason": f"Obsidian thought detected in {w['source']}: {w['wish']}",
                "priority": "high",
                "wish": w["wish"]
            })

        # Priority 3: A/B Benchmark & Latency Optimization
        if benchmark.get("voice_ping_ms", 0) > 150:
            report["opportunities"].append({
                "type": "optimization_opportunity",
                "domain": "voice_pipeline",
                "title": "Voice TTS Daemon Socket Latency Spike",
                "reason": f"Observed {benchmark['voice_ping_ms']}ms ping latency on Kokoro socket.",
                "priority": "medium"
            })

        # Priority 4: GPU VRAM & Memory Headroom
        gpu = report["gpu"]
        if gpu.get("available"):
            vram_free = gpu.get("vram_free_mib", 0)
            if vram_free > 1200:
                report["opportunities"].append({
                    "type": "feature_opportunity",
                    "domain": "gpu_compute",
                    "title": "GPU VRAM Headroom Available for Realtime Vision or Heavy Embeddings",
                    "reason": f"Over {vram_free} MiB of VRAM is idle.",
                    "priority": "low"
                })

        return report


if __name__ == "__main__":
    import re
    scanner = MiloScanner()
    data = scanner.run_full_scan()
    print(json.dumps(data, indent=2))
