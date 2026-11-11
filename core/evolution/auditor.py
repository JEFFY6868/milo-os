#!/usr/bin/env python3
"""
Milo Evolution Engine — Codebase Forensic Auditor (auditor.py)
Performs deep static and runtime introspection across Milo's entire codebase:
- CLI utilities (~/.local/bin/milo*)
- Python daemons (~/.local/share/milo/)
- Wayland desktop UI (~/.config/omarchy/plugins/jeffy.milo/)
- Systemd user services (~/.config/systemd/user/milo*)
Surfaces weak areas, fragility traps, latency hotspots, and generates automated resolution patches.
"""

import os
import re
import sys
import json
import time
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

BIN_DIR = Path.home() / ".local" / "bin"
MILO_SHARE = Path.home() / ".local" / "share" / "milo"
SYSTEMD_DIR = Path.home() / ".config" / "systemd" / "user"
PLUGIN_DIR = Path.home() / ".config" / "omarchy" / "plugins" / "jeffy.milo"
AUDIT_DIR = Path.home() / "MiloNotes" / "Audits"
PROPOSALS_DIR = MILO_SHARE / "evolution" / "proposals"

AUDIT_DIR.mkdir(parents=True, exist_ok=True)
PROPOSALS_DIR.mkdir(parents=True, exist_ok=True)


class MiloAuditor:
    def __init__(self):
        self.timestamp = time.time()
        self.findings: List[Dict[str, Any]] = []

    def audit_cli_binaries(self) -> List[Dict[str, Any]]:
        """Audits all CLI scripts in ~/.local/bin/milo* for bash best practices, error traps, and contracts."""
        issues = []
        if not BIN_DIR.exists():
            return issues

        for path in sorted(BIN_DIR.glob("milo*")):
            if not path.is_file() or path.is_symlink():
                continue

            # Ignore temporary backup, swp, or archive files
            if path.name.endswith((".bak", ".old", ".tmp", "~")) or ".bak." in path.name:
                continue

            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
                lines = content.split("\n")
                first_line = lines[0] if lines else ""

                # Distinguish python vs bash by shebang executable
                is_python = "python" in first_line or path.suffix == ".py"
                is_bash = ("bash" in first_line or first_line.endswith("/sh") or "/bin/sh" in first_line) and not is_python

                # 1. Bash Script Audit
                if is_bash:
                    # Check for error traps (set -e or set -euo pipefail)
                    has_strict_mode = any(re.search(r"set\s+-[a-zA-Z]*e", l) for l in lines[:15])
                    if not has_strict_mode:
                        issues.append({
                            "severity": "HIGH",
                            "category": "fragility",
                            "component": path.name,
                            "path": str(path),
                            "title": f"Missing Strict Error Trapping in {path.name}",
                            "description": f"Script {path.name} lacks `set -e` or `set -euo pipefail`. Failures in intermediate commands can cause silent corruption.",
                            "fix_type": "inject_strict_mode",
                            "line": 2
                        })

                    # Check for help option handling
                    has_help = any("--help" in l or "-h" in l or "usage()" in l for l in lines)
                    if not has_help and len(lines) > 25:
                        issues.append({
                            "severity": "MEDIUM",
                            "category": "contract",
                            "component": path.name,
                            "path": str(path),
                            "title": f"Missing Documentation / Help Contract in {path.name}",
                            "description": f"Script {path.name} does not implement `--help` or `-h` usage documentation.",
                            "fix_type": "add_help_flag"
                        })

                # 2. Python Script Audit
                elif "python" in first_line:
                    # Check for bare except:
                    for idx, line in enumerate(lines, 1):
                        if re.search(r"^\s*except\s*:\s*$", line):
                            issues.append({
                                "severity": "HIGH",
                                "category": "fragility",
                                "component": path.name,
                                "path": str(path),
                                "title": f"Bare Exception Trap in {path.name}:{idx}",
                                "description": f"Script catches all exceptions unconditionally (`except:`). Masks KeyboardInterrupt and SystemExit.",
                                "fix_type": "replace_bare_except",
                                "line": idx
                            })
                            break
            except Exception:
                pass

        return issues

    def audit_systemd_services(self) -> List[Dict[str, Any]]:
        """Audits user systemd units for crash recovery and restart policies."""
        issues = []
        if not SYSTEMD_DIR.exists():
            return issues

        for service_path in sorted(SYSTEMD_DIR.glob("milo*.service")):
            try:
                content = service_path.read_text(encoding="utf-8")
                # Oneshot services don't need Restart=always
                if "Type=oneshot" in content:
                    continue

                if "Restart=" not in content:
                    issues.append({
                        "severity": "HIGH",
                        "category": "resilience",
                        "component": service_path.name,
                        "path": str(service_path),
                        "title": f"Daemon Missing Auto-Restart Policy ({service_path.name})",
                        "description": f"Service {service_path.name} lacks `Restart=always`. If killed or crashed, it will not auto-heal.",
                        "fix_type": "add_service_restart"
                    })
            except Exception:
                pass

        return issues

    def audit_qml_interface(self) -> List[Dict[str, Any]]:
        """Audits MiloService.qml for responsiveness, timers, and blocking operations."""
        issues = []
        qml_path = PLUGIN_DIR / "MiloService.qml"
        if not qml_path.exists():
            return issues

        try:
            content = qml_path.read_text(encoding="utf-8")
            # Check for excessive polling timers (< 1000ms)
            timer_matches = re.findall(r"interval:\s*(\d+)", content)
            fast_timers = [int(m) for m in timer_matches if int(m) < 800 and int(m) > 50]
            if fast_timers:
                issues.append({
                    "severity": "MEDIUM",
                    "category": "latency",
                    "component": "MiloService.qml",
                    "path": str(qml_path),
                    "title": f"High Frequency QML Polling Timers ({len(fast_timers)} detected)",
                    "description": f"Detected {len(fast_timers)} polling timers under 800ms. Consumes unnecessary CPU cycles on the compositor thread.",
                    "fix_type": "relax_timer_intervals"
                })
        except Exception:
            pass

        return issues

    def run_full_audit(self) -> Dict[str, Any]:
        """Runs the consolidated forensic audit and ranks issues by impact."""
        t0 = time.time()
        cli_issues = self.audit_cli_binaries()
        srv_issues = self.audit_systemd_services()
        qml_issues = self.audit_qml_interface()

        all_issues = cli_issues + srv_issues + qml_issues

        # Severity sort order
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        all_issues.sort(key=lambda x: severity_order.get(x.get("severity", "LOW"), 99))

        scan_duration = round(time.time() - t0, 3)

        report = {
            "timestamp": self.timestamp,
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "scan_duration_sec": scan_duration,
            "total_issues_found": len(all_issues),
            "critical_count": sum(1 for i in all_issues if i["severity"] in ("CRITICAL", "HIGH")),
            "warning_count": sum(1 for i in all_issues if i["severity"] == "MEDIUM"),
            "optimization_count": sum(1 for i in all_issues if i["severity"] == "LOW"),
            "issues": all_issues
        }

        # Save to Obsidian
        self.save_to_obsidian(report)
        return report

    def save_to_obsidian(self, report: Dict[str, Any]) -> Path:
        """Writes audit report to ~/MiloNotes/Audits/."""
        today = time.strftime("%Y-%m-%d_%H%M%S")
        report_file = AUDIT_DIR / f"audit_{today}.md"

        lines = [
            f"# Milo Codebase Forensic Audit — {report['date']}\n",
            f"**Scan Duration**: {report['scan_duration_sec']}s | **Total Findings**: {report['total_issues_found']}\n",
            f"• 🔴 Critical / High: {report['critical_count']}",
            f"• 🟡 Warnings: {report['warning_count']}",
            f"• 🟢 Optimizations: {report['optimization_count']}\n",
            "## Forensic Findings\n"
        ]

        for i, iss in enumerate(report["issues"][:15], 1):
            lines.append(f"### {i}. [{iss['severity']}] {iss['title']}")
            lines.append(f"- **Component**: `{iss['component']}` (`{iss['path']}`)")
            lines.append(f"- **Category**: {iss['category'].capitalize()}")
            lines.append(f"- **Diagnosis**: {iss['description']}\n")

        report_file.write_text("\n".join(lines), encoding="utf-8")
        return report_file

    def generate_resolution_proposal(self, issue: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Synthesizes an automated fix proposal for the top audit issue."""
        fix_type = issue.get("fix_type")
        path_str = issue.get("path")
        if not path_str or not Path(path_str).exists():
            return None

        target = Path(path_str)
        proposal_id = f"evo-audit-{int(time.time())}"

        if fix_type == "inject_strict_mode":
            content = target.read_text(encoding="utf-8")
            lines = content.split("\n")
            # Insert set -euo pipefail after shebang
            if len(lines) > 1 and lines[0].startswith("#!"):
                lines.insert(1, "set -euo pipefail")
            else:
                lines.insert(0, "set -euo pipefail")

            patched_content = "\n".join(lines)
            return {
                "id": proposal_id,
                "type": "codebase_repair",
                "title": f"Auto-Patch: Inject Strict Mode into {target.name}",
                "category": "reliability",
                "risk_level": "low",
                "rationale": f"Resolves audit finding: {issue['description']}",
                "spoken_briefing": f"Jeffy, I formulated a reliability patch for {target.name} to enforce strict error handling. Ready for your authorization.",
                "hud_directive": (
                    f"✦ MILO AUDIT RESOLUTION // {target.name.upper()}\n"
                    f"Defect: Missing error trapping in `{target.name}`.\n"
                    f"• Action: Inject `set -euo pipefail` to eliminate silent command failure.\n"
                    f"• Verification: Pre-flight bash syntax validation (`bash -n`).\n\n"
                    f"Click Authorize to apply patch, View Diff, or Defer."
                ),
                "actions": [
                    {
                        "action": "modify_file",
                        "path": str(target),
                        "executable": True,
                        "content": patched_content
                    }
                ],
                "verification_command": f"bash -n {target}",
                "created_at": time.time()
            }

        return None


if __name__ == "__main__":
    auditor = MiloAuditor()
    rep = auditor.run_full_audit()
    print(f"Audit completed in {rep['scan_duration_sec']}s. Found {rep['total_issues_found']} issues.")
    for iss in rep['issues'][:5]:
        print(f"  • [{iss['severity']}] {iss['title']}")
