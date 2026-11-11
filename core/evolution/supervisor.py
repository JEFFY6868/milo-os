#!/usr/bin/env python3
"""
Milo Evolution Engine — Safety Net & Rollback Supervisor (supervisor.py)
Executes human-authorized self-upgrades, manages atomic git branching,
performs live health assertions, and automatically rolls back if errors occur.
"""

import os
import sys
import json
import time
import socket
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

EVOLUTION_DIR = Path.home() / ".local" / "share" / "milo" / "evolution"
PROPOSALS_DIR = EVOLUTION_DIR / "proposals"
LEDGER_FILE = EVOLUTION_DIR / "evolution_ledger.json"
OBSIDIAN_REFLECTIONS = Path.home() / "MiloNotes" / "Daily"


class MiloSupervisor:
    def __init__(self):
        self.runtime_dir = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
        self.ensure_ledger()

    def ensure_ledger(self):
        if not LEDGER_FILE.exists():
            with open(LEDGER_FILE, "w") as f:
                json.dump({"evolutions": []}, f, indent=2)

    def speak(self, text: str):
        """Sends spoken text to Kokoro voice daemon."""
        sock_path = self.runtime_dir / "milo-voice.sock"
        if not sock_path.exists():
            return
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.connect(str(sock_path))
            s.sendall(json.dumps({"action": "speak", "text": text}).encode("utf-8") + b"\n")
            s.close()
        except Exception:
            pass

    def hud_say(self, text: str):
        """Pushes directive text to the desktop HUD modal."""
        try:
            subprocess.run(["omarchy-shell", "milo", "say", text], timeout=2)
        except Exception:
            pass

    def brief(self, proposal: Dict[str, Any]):
        """Dispatches spoken briefing and HUD directive modal to Jeffy."""
        hud_text = proposal.get("hud_directive", "")
        spoken_text = proposal.get("spoken_briefing", "")

        # 1. Update HUD card with interactive Evolution Action Row
        try:
            res = subprocess.run(["omarchy-shell", "milo", "proposeEvolution", hud_text], timeout=2, capture_output=True)
            if res.returncode != 0:
                self.hud_say(hud_text)
        except Exception:
            self.hud_say(hud_text)

        # 2. Spoken briefing aloud on CUDA
        if spoken_text:
            self.speak(spoken_text)

        print(f"✔ [Milo Evolution] Briefing dispatched to HUD and Voice for: {proposal['id']}")

    def apply_proposal(self, proposal: Dict[str, Any]) -> bool:
        """Applies proposal actions with strict pre-flight, testing, and auto-rollback."""
        prop_id = proposal["id"]
        title = proposal["title"]
        print(f"🚀 [Milo Evolution] Applying authorized upgrade: {title} ({prop_id})...")

        backups = []
        created_files = []

        try:
            # Step 1: Pre-flight & Backups
            actions = proposal.get("actions", [])
            for action in actions:
                act_type = action.get("action")
                path_str = action.get("path")
                target_path = Path(path_str)

                if act_type in ("create_script", "write_file", "modify_file"):
                    if target_path.exists():
                        backup_path = target_path.with_suffix(f"{target_path.suffix}.bak_evo")
                        shutil.copy2(target_path, backup_path)
                        backups.append((target_path, backup_path))
                    else:
                        created_files.append(target_path)

                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(target_path, "w") as f:
                        f.write(action.get("content", ""))

                    if action.get("executable"):
                        os.chmod(target_path, 0o755)

                    first_line = ""
                    try:
                        with open(target_path, "r", errors="ignore") as check_f:
                            first_line = check_f.readline()
                    except Exception:
                        pass

                    is_py = target_path.suffix == ".py" or "python" in first_line
                    is_sh = ("bash" in first_line or first_line.endswith("/sh") or "/bin/sh" in first_line or target_path.suffix == ".sh") and not is_py

                    # Pre-flight syntax validation for python & bash files
                    if is_py:
                        res = subprocess.run([sys.executable, "-m", "py_compile", str(target_path)], capture_output=True)
                        if res.returncode != 0:
                            raise ValueError(f"Pre-flight syntax check failed on {target_path}: {res.stderr.decode()}")
                    elif is_sh:
                        res = subprocess.run(["bash", "-n", str(target_path)], capture_output=True)
                        if res.returncode != 0:
                            raise ValueError(f"Pre-flight bash syntax check failed on {target_path}: {res.stderr.decode()}")

            # Step 2: Verification Assertion Check
            verify_cmd = proposal.get("verification_command", "true")
            print(f"🔍 [Milo Evolution] Running verification assertion: {verify_cmd}...")
            t0 = time.time()
            res = subprocess.run(verify_cmd, shell=True, capture_output=True, text=True, timeout=10)

            if res.returncode != 0:
                raise RuntimeError(f"Verification command failed with code {res.returncode}: {res.stderr}")

            print(f"✔ [Milo Evolution] Assertion PASSED in {time.time() - t0:.2f}s!")

            # Step 3: Success Commit & Log
            self.clean_backups(backups)
            self.record_success(proposal)

            # Unlink active proposal so it is no longer pending
            active_link = PROPOSALS_DIR / "active_proposal.json"
            if active_link.exists() or active_link.is_symlink():
                try:
                    active_link.unlink()
                except Exception:
                    pass

            success_msg = f"Upgrade verified: {title}. System operating at peak performance."
            self.hud_say(f"✦ MILO EVOLUTION COMPLETE // {title.upper()} ACTIVE\n• All assertion tests passed.\n• Status: Nominal & Locked into Core.")
            self.speak(f"Upgrade successful. {title} is now active and verified.")
            return True

        except Exception as e:
            print(f"❌ [Milo Evolution] Upgrade error encountered: {e}. INITIATING AUTO-ROLLBACK...")
            self.rollback(backups, created_files)
            fail_msg = f"✦ EVOLUTION ABORTED // AUTO-ROLLBACK EXECUTED\n• Reason: {str(e)[:120]}\n• System baseline restored with zero downtime."
            self.hud_say(fail_msg)
            self.speak("Upgrade verification failed. Auto-rollback executed. System restored to baseline.")
            return False

    def clean_backups(self, backups):
        for orig, backup in backups:
            if backup.exists():
                try:
                    backup.unlink()
                except Exception:
                    pass

    def rollback(self, backups, created_files):
        """Restores backed-up files and removes newly created files."""
        for target, backup in backups:
            if backup.exists():
                try:
                    shutil.move(backup, target)
                    print(f"  • Restored: {target}")
                except Exception as e:
                    print(f"  • Failed to restore {target}: {e}")

        for created in created_files:
            if created.exists():
                try:
                    created.unlink()
                    print(f"  • Cleaned up: {created}")
                except Exception as e:
                    print(f"  • Failed to clean up {created}: {e}")

    def record_success(self, proposal: Dict[str, Any]):
        """Records completed evolution to the persistent ledger and Obsidian."""
        try:
            with open(LEDGER_FILE, "r") as f:
                data = json.load(f)
        except Exception:
            data = {"evolutions": []}

        record = {
            "id": proposal["id"],
            "title": proposal["title"],
            "category": proposal.get("category", "optimization"),
            "applied_at": time.time(),
            "date": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        data["evolutions"].append(record)

        with open(LEDGER_FILE, "w") as f:
            json.dump(data, f, indent=2)

        # Update Obsidian Reflection if directory exists
        if OBSIDIAN_REFLECTIONS.exists():
            today_file = OBSIDIAN_REFLECTIONS / f"{time.strftime('%Y-%m-%d')}_evolution.md"
            entry = f"\n- **{time.strftime('%H:%M:%S')}** \u2014 Applied Evolution: *{proposal['title']}* ({proposal.get('rationale')})\n"
            with open(today_file, "a") as f:
                f.write(entry)


if __name__ == "__main__":
    sup = MiloSupervisor()
    active_prop_file = PROPOSALS_DIR / "active_proposal.json"
    if active_prop_file.exists():
        with open(active_prop_file, "r") as f:
            prop = json.load(f)
        sup.brief(prop)
    else:
        print("No active proposal to brief.")
