# 🤖 Milo AI & Kino Cinema Studio OS Ecosystem

> **100% Turnkey Personal AI Companion & Filmmaking Subagent System for Arch Linux (Hyprland / Omarchy)**  
> Includes Native Android App, Quickshell Wallpaper HUD, Obsidian Neural Vault, Voice Calls over Tailscale, and Automated One-Command Recovery.

---

## 🌟 What is Inside This Repository?

This repository contains the complete ecosystem of **Milo** (personal AI desktop companion) and **Kino** (creative screenplay subagent):

1. **Dotfiles (`dotfiles/`):**
   - **Hyprland:** Complete window rules, animations, keybindings, monitors, look & feel (`~/.config/hypr/`).
   - **Omarchy & Quickshell:** Desktop companion Quickshell HUD service plugin (`jeffy.milo`) rendering Milo directly onto the wallpaper bottom layer (`~/.config/omarchy/`).
   - **Foot Terminal:** Tokyo night styled lightweight Wayland terminal config (`~/.config/foot/`).
   - **Milo Settings:** AI runtime settings (`~/.config/milo/config.json`).

2. **Milo Core & CLI (`milo-core/`):**
   - 10 custom CLI binaries (`milo`, `milo-query`, `milo-kino`, `milo-reflect`, `milo-call`, `milo-browser`, etc.).
   - Full Kino Cinema Studio web platform & API server (`server.py`, `kino_agent.py`, `milo_companion.py`).
   - Systemd user services (`milo-kino-studio.service`, `milo-wa-bridge.service`, etc.).
   - Multi-model Gemini fallback engine with live Hyprland desktop introspection.

3. **Android Native Call App (`android/milo-android-native/`):**
   - Pure 100% native Android application (Zero WebView).
   - Custom 2D Canvas Neon waveform visualizer.
   - Low-latency native `AudioRecord` PCM capture (16kHz mono).
   - Push-to-talk & real-time two-way voice call over Tailscale mesh.
   - Automated rootless APK build script (`build_native.sh`).

4. **Obsidian Neural Vault (`obsidian-template/`):**
   - Persistent long-term memory engine (`Core_Memories.md`, `Preferences.md`).
   - User profile (`Profile/Jeffy.md`).
   - Screenplay beats, characters, shotlists, and daily interaction logs.

---

## 🚀 One-Command Disaster Recovery & Fresh Install

If your Arch Linux OS ever crashes, is wiped, or you move to a new machine, restore the entire ecosystem in **one single command**:

```bash
git clone https://github.com/jeffy1122/milo-os.git
cd milo-os
./install.sh
```

### What `install.sh` Does Automatically:
1. Installs all required Arch Linux system packages (`python`, `pip`, `ffmpeg`, `sox`, `qrencode`, etc.).
2. Deploys Hyprland, Omarchy, Foot, and Quickshell dotfiles to `~/.config/`.
3. Installs all 10 Milo CLI commands into `~/.local/bin/` and exports to PATH.
4. Deploys Kino Cinema Studio to `~/.local/share/milo/`.
5. Creates the Python virtual environment and installs all dependencies (`requirements.txt`).
6. Configures and enables systemd user services (`milo-kino-studio.service` auto-starts on boot).
7. Sets up the Obsidian Neural Vault structure.
8. Deploys the Android Native APK ready for mobile download.

---

## 🔑 Post-Install Setup: API Key

After running `./install.sh`, add your Gemini API Key:

```bash
nano ~/.config/milo/browser.env
```
Add your key:
```bash
GEMINI_API_KEY="your_actual_gemini_api_key_here"
```

Restart the service:
```bash
systemctl --user restart milo-kino-studio.service
```

---

## 📱 Mobile App Download

Once installed and running on your Tailnet, your Android phone can download the app directly:

- **Browser URL:** `http://<your-tailscale-ip>:3140/download` or `http://<your-tailscale-ip>:3140/app`
- **QR Code:** Available on the studio dashboard or run `qrencode -t ANSIUTF8 "http://<your-tailscale-ip>:3140/download"` in your terminal.

---

## 🛠️ CLI Quick Reference

| Command | Action |
| :--- | :--- |
| `milo status` | View active Milo & Kino system services and health |
| `milo-query "question"` | Query Milo with Obsidian memory and desktop awareness |
| `milo-kino` | Launch Kino Cinema Studio interactive CLI |
| `milo-call` | Trigger voice call session |
| `milo-reflect` | Run background reflection to distill new Obsidian memories |
