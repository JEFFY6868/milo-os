#!/usr/bin/env python3
"""
Kino — Milo's Dedicated Cinema & Screenplay Subagent
Specialized in film direction, screenplay architecture, character psychology,
scene beat doctoring, and visual shotlist creation for directors and writers.
"""

import sys
import os
import re
import json
import time
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Paths
HOME = Path.home()
VAULT_DIR = HOME / "Documents" / "Obsidian" / "Milo"
CINEMA_DIR = VAULT_DIR / "Cinema"
PROJECTS_DIR = CINEMA_DIR / "Projects"
CHARACTERS_DIR = CINEMA_DIR / "Characters"
IDEAS_DIR = CINEMA_DIR / "Ideas"
SHOTLISTS_DIR = CINEMA_DIR / "Shotlists"
DAILY_DIR = VAULT_DIR / "Daily"

# Terminal Colors
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
MAGENTA = "\033[35m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def slugify(text: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[-\s]+", "_", slug)[:40]


def update_hud(message: str):
    """Safely forward notification to Omarchy Wayland HUD."""
    try:
        clean_msg = message.replace('"', '\\"').replace("'", "")
        os.system(f"omarchy-shell -q milo say \"{clean_msg}\" >/dev/null 2>&1 &")
    except Exception:
        pass


def execute_llm(prompt: str, system_context: str) -> str:
    """Invokes Antigravity AI core with Cinema workspace attached, with fallback."""
    full_prompt = f"[System Context: {system_context}]\n\n{prompt}"
    try:
        res = subprocess.run(
            [
                "/home/jeffy/.local/bin/agy",
                "--project", "milo-desktop",
                "--add-dir", str(CINEMA_DIR),
                "--dangerously-skip-permissions",
                "-c",
                "-p", full_prompt,
                "--effort", "low"
            ],
            capture_output=True,
            text=True,
            timeout=50
        )
        out = res.stdout.strip()
        if out:
            return out
    except Exception as e:
        print(f"{YELLOW}Warning: Antigravity CLI timed out ({e}), falling back to direct GenAI...{RESET}")

    # Fallback: Direct Gemini API
    env_file = HOME / ".config" / "milo" / "browser.env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip("'\"")

    if os.environ.get("GEMINI_API_KEY"):
        try:
            from google import genai
            client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
            model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite")
            response = client.models.generate_content(
                model=model_name,
                contents=f"{system_context}\n\nTask:\n{prompt}"
            )
            return response.text
        except Exception as e:
            return f"Error contacting model: {e}"

    return "Kino encountered an issue processing the creative brief."


class KinoEngine:
    def __init__(self):
        self._ensure_directories()

    def _ensure_directories(self):
        CINEMA_DIR.mkdir(parents=True, exist_ok=True)
        PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
        CHARACTERS_DIR.mkdir(parents=True, exist_ok=True)
        IDEAS_DIR.mkdir(parents=True, exist_ok=True)
        SHOTLISTS_DIR.mkdir(parents=True, exist_ok=True)
        DAILY_DIR.mkdir(parents=True, exist_ok=True)

    def log_daily(self, title: str, summary: str, note_path: str):
        today = datetime.now().strftime("%Y-%m-%d")
        time_str = datetime.now().strftime("%H:%M")
        daily_file = DAILY_DIR / f"{today}.md"

        if not daily_file.exists():
            daily_file.write_text(f"# 📅 Daily Note: {today}\n\n## 💬 Conversations & Interaction Log\n\n")

        entry = f"""### {time_str} - 🎬 Kino Cinema Studio
- **Action:** {title}
- **Document:** [[{note_path}|View Creative Note]]
- **Summary:** {summary[:180]}...

"""
        with open(daily_file, "a", encoding="utf-8") as f:
            f.write(entry)

    def init_project(self, title: str) -> str:
        proj_slug = slugify(title)
        proj_dir = PROJECTS_DIR / proj_slug
        proj_dir.mkdir(parents=True, exist_ok=True)

        overview_file = proj_dir / "Overview.md"
        beats_file = proj_dir / "BeatSheet.md"
        chars_file = proj_dir / "Characters.md"
        shots_file = proj_dir / "Shotlist.md"

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        overview_content = f"""# 🎬 Film Project: {title}

- **Created:** {timestamp}
- **Director / Writer:** Jeffy
- **Co-Pilot:** Kino Cinema Subagent
- **Status:** In Development

---

## 📌 Logline & Premise
*One-sentence summary defining the protagonist, inciting incident, primary conflict, and high stakes.*

## 🎭 Genre & Tone
- **Primary Genre:** 
- **Sub-genre:** 
- **Tone Reference:** 

## ⚖️ Central Moral Argument (Theme)
*What life truth does the story argue? (e.g., Justice vs Law, Ambition vs Love)*

---

## 🧭 Project Navigation
- [[Cinema/Projects/{proj_slug}/BeatSheet|Scene Beat Sheet]]
- [[Cinema/Projects/{proj_slug}/Characters|Character Roster]]
- [[Cinema/Projects/{proj_slug}/Shotlist|Director's Shot Division]]
- [[Cinema/Index|Back to Studio Dashboard]]
"""
        overview_file.write_text(overview_content)

        beats_content = f"""# 📜 Screenplay Beat Sheet: {title}

Structured according to classic 3-Act / 8-Sequence Screenplay Architecture.

---

## 🎭 ACT 1: Setup & Inciting Incident
1. **Opening Image (1-5 min):** Sets the tone, visual motif, and protagonist's normal world.
2. **Theme Stated (5 min):** Someone states the life dilemma the protagonist must face.
3. **Inciting Incident (10-15 min):** The event that shatters the protagonist's equilibrium.
4. **Plot Point 1 / Crossing the Threshold (25-30 min):** The protagonist makes an irreversible decision to enter the new world.

---

## ⚡ ACT 2A: Rising Action & Fun and Games
5. **B-Story / Relationship Arc (30-40 min):** Secondary character enters to challenge the protagonist's worldview.
6. **First Escalation & Complications (40-55 min):** The protagonist tries old habits; problems compound.
7. **Midpoint (55-60 min):** High stakes shift! A false victory or false defeat that raises the ticking clock.

---

## 🌪️ ACT 2B: The Collapse & Interval Turn
8. **Villain / Antagonist Closes In (60-75 min):** Pressure mounts from external and internal forces.
9. **All Hope is Lost / Dark Night of the Soul (75-85 min):** The absolute lowest point. The protagonist's flaw destroys everything.

---

## 💥 ACT 3: Climax & Moral Resolution
10. **The Breakthrough / Third Act Twist (85-95 min):** The protagonist synthesizes what they learned and attacks the problem anew.
11. **Climax Confrontation (95-110 min):** High tension battle of physical and philosophical ideals.
12. **Final Image & Resolution (110-120 min):** Opposite of the opening image, demonstrating permanent transformation.
"""
        beats_file.write_text(beats_content)

        chars_content = f"""# 👥 Character Roster: {title}

- **Protagonist:** 
- **Antagonist:** 
- **Foil / Catalyst:** 
- **Supporting:** 

---
*Run `milo kino character <name> "<traits>" --project {proj_slug}` to generate complete character dossiers.*
"""
        chars_file.write_text(chars_content)

        shots_content = f"""# 🎥 Director's Shot Division: {title}

Catalog of scene-by-scene camera angles, visual moods, and sound design references.

---
"""
        shots_file.write_text(shots_content)

        # Update Project Index
        proj_index = PROJECTS_DIR / "Index.md"
        row = f"| **{title}** | In Development | [[Cinema/Projects/{proj_slug}/Overview|Open Project]] | {timestamp[:10]} |\n"
        if not proj_index.exists():
            proj_index.write_text("# 📁 Cinema Projects Catalog\n\n| Title | Status | Link | Created |\n| :--- | :---: | :--- | :--- |\n")
        with open(proj_index, "a", encoding="utf-8") as f:
            f.write(row)

        self.log_daily(f"Initialized Film Project: {title}", f"Created project workspace at Cinema/Projects/{proj_slug}", f"Cinema/Projects/{proj_slug}/Overview")
        update_hud(f"🎬 Kino: Created Project '{title}'")
        return f"✦ Project '{title}' initialized successfully at [[Cinema/Projects/{proj_slug}/Overview]]!"

    def develop_idea(self, raw_idea: str) -> str:
        update_hud(f"🎬 Kino: Developing story premise...")
        system_context = (
            "You are Kino, an acclaimed visionary film director and screenwriting doctor. "
            "Your job is to transform raw story concepts into explosive, cinematic narrative treatments. "
            "Format your answer in clean GitHub-flavored markdown with the following sections:\n"
            "1. 🎯 High-Concept Logline (1 punchy sentence with Protagonist, Inciting Incident, Goal, and Stakes)\n"
            "2. 🎭 Genre, Tone & Cinema References (e.g. Neo-Noir, Thriller like Vikram Vedha, Memories of Murder, Prisoners)\n"
            "3. ⚖️ Central Conflict & Philosophical Dilemma\n"
            "4. ⚡ The Hook (Why will audiences rush to theaters for this?)\n"
            "5. 🌪️ 3 Key Dramatic Twists / Interval Highs\n"
            "Maintain deep cinematic storytelling sense. Give constructive, exciting, high-stakes suggestions."
        )

        prompt = f"Develop this raw story idea into a cinematic treatment:\n\"{raw_idea}\""
        result = execute_llm(prompt, system_context)

        # Save to Obsidian
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        slug = slugify(raw_idea[:30])
        file_name = f"{timestamp}_{slug}.md"
        file_path = IDEAS_DIR / file_name

        note_content = f"""# 💡 Story Treatment: {raw_idea[:50]}...

- **Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
- **Raw Premise:** "{raw_idea}"
- **Consultant:** Kino Cinema Subagent

---

{result}

---

## 🧭 Navigation
- [[Cinema/Index|Kino Studio Dashboard]]
- [[Cinema/Ideas/Index|Ideas Catalog]]
"""
        file_path.write_text(note_content)

        # Update Ideas Catalog
        ideas_index = IDEAS_DIR / "Index.md"
        row = f"| {datetime.now().strftime('%Y-%m-%d')} | {raw_idea[:45]}... | [[Cinema/Ideas/{timestamp}_{slug}|View Treatment]] |\n"
        if not ideas_index.exists():
            ideas_index.write_text("# 💡 Kino Story Ideas & Concept Catalog\n\n| Date | Premise | Treatment |\n| :--- | :--- | :--- |\n")
        with open(ideas_index, "a", encoding="utf-8") as f:
            f.write(row)

        self.log_daily("Story Idea Developed", raw_idea, f"Cinema/Ideas/{timestamp}_{slug}")
        update_hud("🎬 Kino: Story treatment ready in Obsidian!")
        return result

    def develop_character(self, name: str, details: str, project: Optional[str] = None) -> str:
        update_hud(f"🎬 Kino: Profiling character '{name}'...")
        system_context = (
            "You are Kino, an elite psychological character development consultant for cinema. "
            "Create a vivid, three-dimensional Character Dossier. Format as clean markdown with:\n"
            "1. 👤 Archetype & Story Role (Protagonist, Antagonist, Catalyst, Shadow, Foil)\n"
            "2. 🎯 External Want vs Internal Need (The external goal they chase vs the emotional truth they need to survive)\n"
            "3. 💔 The Ghost / Deepest Trauma (What happened in their past that defines their current behavior?)\n"
            "4. ⚡ Fatal Flaw (Hamartia) & Moral Blindspot\n"
            "5. 🗣️ Speech Rhythm & Dialogue Quirks (How do they speak? Rapid, sparse, sarcastic, formal? Sample signature lines)\n"
            "6. 👁️ Visual Motif & Physicality (Costume, body language, unique object/habit)\n"
            "Make the character layered, unpredictable, and cinematic."
        )

        prompt = f"Create a comprehensive character dossier for:\nName: {name}\nDetails/Context: {details}"
        result = execute_llm(prompt, system_context)

        char_slug = slugify(name)
        file_path = CHARACTERS_DIR / f"{char_slug}.md"

        note_content = f"""# 👤 Character Dossier: {name}

- **Created:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
- **Associated Project:** {project or 'Standalone'}
- **Profiled By:** Kino Cinema Subagent

---

{result}

---

## 🧭 Navigation
- [[Cinema/Index|Cinema Studio Dashboard]]
- [[Cinema/Characters/Index|Character Catalog]]
"""
        file_path.write_text(note_content)

        chars_index = CHARACTERS_DIR / "Index.md"
        row = f"| **{name}** | {details[:40]}... | [[Cinema/Characters/{char_slug}|View Dossier]] |\n"
        if not chars_index.exists():
            chars_index.write_text("# 👥 Character Dossiers Catalog\n\n| Name | Context | Dossier |\n| :--- | :--- | :--- |\n")
        with open(chars_index, "a", encoding="utf-8") as f:
            f.write(row)

        self.log_daily(f"Character Dossier Created: {name}", details, f"Cinema/Characters/{char_slug}")
        update_hud(f"🎬 Kino: Character '{name}' profiled!")
        return result

    def script_doctor(self, scene_pitch: str) -> str:
        update_hud("🎬 Kino: Running Script Doctor analysis...")
        system_context = (
            "You are Kino, an uncompromising Hollywood & Kollywood Script Doctor. "
            "Analyze and critique this scene pitch or dialogue sequence. "
            "Format in clean markdown with:\n"
            "1. 📊 Tension & Pacing Score (1 to 10 with detailed diagnostic justification)\n"
            "2. 🎭 Subtext vs Exposition Check (Is the scene on-the-nose? Are characters explaining too much? How can silence or action replace words?)\n"
            "3. ⚠️ Plot-Hole, Logic & Character Consistency Critique\n"
            "4. 💡 3 High-Impact Directorial Twists / Enhancements (Specific suggestions to elevate dramatic tension and emotional payoff)\n"
            "Be constructive, sharp, and deeply focused on cinematic impact."
        )

        prompt = f"Critique and doctor this scene/screenplay pitch:\n\"{scene_pitch}\""
        result = execute_llm(prompt, system_context)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        slug = slugify(scene_pitch[:30])
        file_path = IDEAS_DIR / f"Doctor_{timestamp}_{slug}.md"

        note_content = f"""# 🩺 Script Doctor Report: {scene_pitch[:45]}...

- **Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
- **Analyzed By:** Kino Script Doctor

---

## 📋 Input Pitch / Scene
> {scene_pitch}

---

## 🔬 Doctor's Critique & Recommendations
{result}

---

## 🧭 Navigation
- [[Cinema/Index|Studio Dashboard]]
"""
        file_path.write_text(note_content)
        self.log_daily("Script Doctor Analysis", scene_pitch, f"Cinema/Ideas/Doctor_{timestamp}_{slug}")
        update_hud("🎬 Kino: Script Doctor critique complete!")
        return result

    def generate_shotlist(self, scene_description: str) -> str:
        update_hud("🎬 Kino: Directing shot breakdown...")
        system_context = (
            "You are Kino, an acclaimed Director and Cinematographer. "
            "Break down this scene into a visionary Director's Shot Division. Format with:\n"
            "1. 🎥 Key Camera Shots (Shot #, Angle: Low/High/Dutch, Movement: Tracking/Steadicam/Handheld/Static, Framing: ECU/Close-up/Medium/Wide, Lens focus)\n"
            "2. 💡 Lighting & Color Palette (Contrast, Color temperature, Shadows, Practical lights)\n"
            "3. 🎵 Sound Design & BGM Mood Reference (Ambient elements, Foley focus, Musical style e.g. aggressive strings, deep synth, silence)\n"
            "4. 🎬 Actor Blocking & Physical Movement (How characters move across space to convey power dynamics)\n"
            "5. 👁️ Signature Visual Motif / Climax Frame\n"
            "Make it visually breathtaking and ready for on-set production."
        )

        prompt = f"Break down this scene into a complete directorial shot division:\n\"{scene_description}\""
        result = execute_llm(prompt, system_context)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        slug = slugify(scene_description[:30])
        file_path = SHOTLISTS_DIR / f"Shotlist_{timestamp}_{slug}.md"

        note_content = f"""# 🎥 Director's Shot Division: {scene_description[:45]}...

- **Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
- **Director:** Jeffy
- **Co-Director:** Kino Cinema Subagent

---

{result}

---

## 🧭 Navigation
- [[Cinema/Index|Studio Dashboard]]
- [[Cinema/Shotlists/Index|All Shotlists]]
"""
        file_path.write_text(note_content)

        shots_index = SHOTLISTS_DIR / "Index.md"
        row = f"| {datetime.now().strftime('%Y-%m-%d')} | {scene_description[:45]}... | [[Cinema/Shotlists/Shotlist_{timestamp}_{slug}|View Shotlist]] |\n"
        if not shots_index.exists():
            shots_index.write_text("# 🎥 Shotlists Catalog\n\n| Date | Scene | Link |\n| :--- | :--- | :--- |\n")
        with open(shots_index, "a", encoding="utf-8") as f:
            f.write(row)

        self.log_daily("Shot Division Generated", scene_description, f"Cinema/Shotlists/Shotlist_{timestamp}_{slug}")
        update_hud("🎬 Kino: Shotlist generated!")
        return result


def main():
    parser = argparse.ArgumentParser(description="Kino — Milo's Dedicated Cinema & Screenplay Subagent")
    subparsers = parser.add_subparsers(dest="subcommand", help="Cinema subagent actions")

    # kino project <title>
    proj_parser = subparsers.add_parser("project", help="Initialize a new film/series project")
    proj_parser.add_argument("title", nargs="+", help="Project title")

    # kino idea "<prompt>"
    idea_parser = subparsers.add_parser("idea", help="Develop a raw idea into a high-concept treatment")
    idea_parser.add_argument("prompt", nargs="+", help="Raw premise or story thought")

    # kino character <name> "<traits>"
    char_parser = subparsers.add_parser("character", help="Create a deep psychological character dossier")
    char_parser.add_argument("name", help="Character name")
    char_parser.add_argument("traits", nargs="+", help="Description, role, and quirks")
    char_parser.add_argument("--project", default=None, help="Associated project slug")

    # kino doctor "<scene>"
    doc_parser = subparsers.add_parser("doctor", help="Critique and doctor a scene or pitch")
    doc_parser.add_argument("pitch", nargs="+", help="Scene summary, plot point, or dialogue")

    # kino shotlist "<scene>"
    shot_parser = subparsers.add_parser("shotlist", help="Director's camera framing, lighting, and sound cues")
    shot_parser.add_argument("scene", nargs="+", help="Scene description")

    # kino studio / ui / app
    studio_parser = subparsers.add_parser("studio", help="Launch Kino Cinema Studio Native Desktop App")
    ui_parser = subparsers.add_parser("ui", help="Launch Kino Cinema Studio Native Desktop App")
    app_parser = subparsers.add_parser("app", help="Launch Kino Cinema Studio Native Desktop App")

    args = parser.parse_args()
    engine = KinoEngine()

    if args.subcommand in ("studio", "ui", "app"):
        print(f"\n{BOLD}{CYAN}🎬 KINO CINEMA STUDIO — Native Desktop Workstation{RESET}")
        os.system("systemctl --user start milo-kino-studio.service >/dev/null 2>&1")
        print(f"  {GREEN}● Status:{RESET} Active (GTK3 / WebKit2 Native Wayland Window)")
        print(f"  {DIM}Vault path:{RESET} {CINEMA_DIR}")
        print(f"  {DIM}Hotkey:{RESET} {YELLOW}SUPER + SHIFT + K{RESET}")
        print(f"  {DIM}Launching native desktop workstation...{RESET}\n")
        subprocess.Popen(["/home/jeffy/.local/bin/kino-app"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    elif args.subcommand == "project":
        title = " ".join(args.title)
        print(f"\n{BOLD}{CYAN}🎬 KINO CINEMA STUDIO: Initializing Project...{RESET}")
        res = engine.init_project(title)
        print(f"{GREEN}{res}{RESET}\n")

    elif args.subcommand == "idea":
        prompt = " ".join(args.prompt)
        print(f"\n{BOLD}{MAGENTA}🎬 KINO CINEMA STUDIO: Developing Story Treatment...{RESET}")
        print(f"  {DIM}Premise:{RESET} {prompt}\n")
        res = engine.develop_idea(prompt)
        print(f"\n{BOLD}{GREEN}✦ Cinematic Treatment:{RESET}\n\n{res}\n")

    elif args.subcommand == "character":
        traits = " ".join(args.traits)
        print(f"\n{BOLD}{MAGENTA}🎬 KINO CINEMA STUDIO: Building Character Dossier: {args.name}...{RESET}")
        res = engine.develop_character(args.name, traits, args.project)
        print(f"\n{BOLD}{GREEN}✦ Character Dossier:{RESET}\n\n{res}\n")

    elif args.subcommand == "doctor":
        pitch = " ".join(args.pitch)
        print(f"\n{BOLD}{YELLOW}🎬 KINO SCRIPT DOCTOR: Analyzing Scene / Screenplay...{RESET}")
        res = engine.script_doctor(pitch)
        print(f"\n{BOLD}{GREEN}✦ Script Doctor Report:{RESET}\n\n{res}\n")

    elif args.subcommand == "shotlist":
        scene = " ".join(args.scene)
        print(f"\n{BOLD}{CYAN}🎬 KINO DIRECTOR: Designing Camera & Lighting Division...{RESET}")
        res = engine.generate_shotlist(scene)
        print(f"\n{BOLD}{GREEN}✦ Director's Shot Division:{RESET}\n\n{res}\n")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
