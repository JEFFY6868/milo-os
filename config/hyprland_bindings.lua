-- MiloOS Keybindings Configuration
-- Personal keybinding overrides for MiloOS

-- Milo Desktop Assistant & Spotlight (Milo Tactical HUD)
hl.unbind("SUPER + SPACE")
o.bind("SUPER + SPACE", "Milo Tactical HUD", "/home/jeffy/.local/bin/milo-hud")
hl.unbind("SUPER + SHIFT + SPACE")
o.bind("SUPER + SHIFT + SPACE", "Milo Clipboard AI", "milo-clipboard")
o.bind("SUPER + SLASH", "Milo Semantic Brain", "/home/jeffy/.local/bin/milo-brain")
o.bind("SUPER + ALT + B", "Milo Semantic Brain", "/home/jeffy/.local/bin/milo-brain")
o.bind("SUPER + ALT + X", "Milo Cognitive Cortex", "/home/jeffy/.local/bin/milo-cortex-hud")
o.bind("SUPER + A", "Milo Tactical HUD", "/home/jeffy/.local/bin/milo-hud")
o.bind("SUPER + D", "Milo Wallpaper Studio", { tui = "milo-paper hud" })
o.bind("SUPER + ALT + W", "Next Milo Wallpaper", "milo-paper next")
o.bind("SUPER + R", "App Launcher", "fuzzel")

-- System Activity Monitor (MiloTop)
o.bind("CTRL + SHIFT + ESCAPE", "System Monitor (MiloTop)", { tui = "milotop" })
o.bind("SUPER + ESCAPE", "System Monitor (MiloTop)", { tui = "milotop" })

-- Terminal shortcuts
o.bind("ALT + RETURN", "Terminal", "foot")
o.bind("CTRL + ALT + T", "Terminal", "foot")

-- Kino Cinema Studio Director Suite
o.bind("SUPER + SHIFT + K", "Kino Cinema Studio", { launch = "kino-app", focus = "kino-studio" })

-- Milo Live Call App
o.bind("SUPER + C", "Milo Live Call", { launch = "milo-call-app", focus = "title:Milo AI — Live Voice Call" })

-- Milo WhatsApp Gateway & Pairing
o.bind("SUPER + SHIFT + W", "Milo WhatsApp Gateway", "foot -T 'Milo WhatsApp Gateway' -e milo wa qr")

-- Google DeepMind Antigravity AI Agent (with live log watcher for Milo Guardian)
o.bind("SUPER + G", "Antigravity AI", "foot -T 'Antigravity AI' -e /home/jeffy/.local/bin/agy")
hl.unbind("SUPER + ALT + G")
o.bind("SUPER + ALT + G", "Milo Game Mode Toggle", "/home/jeffy/.local/bin/milo-game toggle")

-- Screenshot, Snipping Tool, OCR & Color Picker
o.bind("PRINT", "Screenshot Region", "milo-snip")
o.bind("SUPER + SHIFT + S", "Snipping Tool (Edit)", "milo-snip --edit")
o.bind("SUPER + SHIFT + O", "Screen OCR (Text to Clipboard)", "milo-ocr")
o.bind("SUPER + ALT + O", "Screen OCR & Ask Milo", "milo-ocr --ask")
o.bind("SUPER + P", "Color Picker", "milo-colorpicker")

-- Milo Eyes — Multimodal Screen Perception & Tactical Vision Intelligence
hl.unbind("SUPER + SHIFT + E")
o.bind("SUPER + I", "Milo Eyes Vision HUD", "milo-eyes snap")
o.bind("SUPER + SHIFT + E", "Milo Eyes Vision HUD", "milo-eyes snap")
o.bind("SUPER + SHIFT + I", "Milo Eyes Window Inspect", "milo-eyes window")
o.bind("SUPER + ALT + E", "Milo Eyes Window Inspect", "milo-eyes window")
o.bind("SUPER + ALT + I", "Milo Eyes Full Screen Inspect", "milo-eyes full")

-- Milo Optical Vision — Hardware Webcam Perception (Milo Optical Sensor)
o.bind("SUPER + SHIFT + C", "Milo Camera Optical Vision", "/home/jeffy/.local/bin/milo-look")

-- File Manager (Milo Files Native GUI)
hl.unbind("SUPER + SHIFT + F")
hl.unbind("SUPER + ALT + SHIFT + F")
hl.unbind("SUPER + E")
o.bind("SUPER + E", "Milo Files", "/home/jeffy/.local/bin/milo-files")
o.bind("SUPER + SHIFT + F", "Milo Files", "/home/jeffy/.local/bin/milo-files")

-- Firefox Browser & Milo Drop
o.bind("SUPER + B", "Firefox Browser", { launch = "firefox", focus = "firefox" })
o.bind("SUPER + L", "Milo Drop", { tui = "milo-drop recv" })

-- Telegram Desktop
o.bind("SUPER + T", "Telegram Desktop", "telegram-desktop")
o.bind("SUPER + SHIFT + T", "Telegram Desktop", "telegram-desktop")

-- Milo Notes (Native Markdown Knowledge Studio)
o.bind("SUPER + N", "Milo Notes", "/home/jeffy/.local/bin/milo-notes")

-- BitTorrent Clients
o.bind("SUPER + SHIFT + D", "qBittorrent", "qbittorrent")
o.bind("SUPER + ALT + SHIFT + D", "Milo Torrent Swarm", { tui = "milo-torrent swarm" })

-- Milo Offline Voice Dictation & AI Assistant (Phonon-2)
hl.unbind("SUPER + V")
o.bind("SUPER + V", "Milo Voice Dictation", "/home/jeffy/.local/bin/milo-listen")
o.bind("SUPER + ALT + J", "Milo Voice AI Chat", { tui = "/home/jeffy/.local/bin/milo-voice-chat" })

-- Media Players (Video & Music)
o.bind("SUPER + SHIFT + V", "Celluloid Video Player", "celluloid")
o.bind("SUPER + M", "Milo Music Player", { tui = "milo-music" })
o.bind("SUPER + ALT + M", "Milo Music Track Picker", { launch = "foot -a milo-floating -T 'MILO // Track Picker' /home/jeffy/.local/bin/milo-music pick" })
hl.unbind("SUPER + ALT + SPACE")
o.bind("SUPER + ALT + SPACE", "Milo Music Play/Pause", "/home/jeffy/.local/bin/milo-music play-pause")
o.bind("SUPER + ALT + P", "Milo Music Play/Pause", "/home/jeffy/.local/bin/milo-music play-pause")
o.bind("SUPER + ALT + RIGHT", "Milo Music Next Track", "/home/jeffy/.local/bin/milo-music next")
o.bind("SUPER + ALT + LEFT", "Milo Music Prev Track", "/home/jeffy/.local/bin/milo-music prev")
o.bind("SUPER + ALT + PERIOD", "Milo Music Next Track", "/home/jeffy/.local/bin/milo-music next")
o.bind("SUPER + ALT + COMMA", "Milo Music Prev Track", "/home/jeffy/.local/bin/milo-music prev")

-- Milo Audio Volume & Media Controls (Milo-Vol)
hl.unbind("XF86AudioRaiseVolume")
hl.unbind("XF86AudioLowerVolume")
hl.unbind("XF86AudioMute")
hl.unbind("XF86AudioMicMute")
hl.unbind("XF86AudioPlay")
hl.unbind("XF86AudioPause")
hl.unbind("XF86AudioNext")
hl.unbind("XF86AudioPrev")

o.bind("XF86AudioRaiseVolume", "Volume up", "milo-vol up", { locked = true, repeating = true })
o.bind("XF86AudioLowerVolume", "Volume down", "milo-vol down", { locked = true, repeating = true })
o.bind("XF86AudioMute", "Mute toggle", "milo-vol mute", { locked = true })
o.bind("XF86AudioMicMute", "Mic mute toggle", "milo-vol mic-mute", { locked = true })
o.bind("XF86AudioPlay", "Play/Pause", "milo-vol play-pause", { locked = true })
o.bind("XF86AudioPause", "Play/Pause", "milo-vol play-pause", { locked = true })
o.bind("XF86AudioNext", "Next track", "milo-vol next", { locked = true })
o.bind("XF86AudioPrev", "Prev track", "milo-vol prev", { locked = true })

-- Milo Visual HUD & Status Bar Shortcuts
o.bind("SUPER + ALT + V", "Milo Volume HUD", { tui = "milo-vol hud" })
o.bind("SUPER + SHIFT + B", "Milo Status Bar", "milo-bar dock")

-- Milo Executive AI Workstation (Claude, Hermes, Aider, CEO Dispatcher)
o.bind("SUPER + ALT + C", "Milo Claude Architect", { tui = "/home/jeffy/.local/bin/milo-code" })
o.bind("SUPER + ALT + H", "Milo Hermes Operations", { tui = "/home/jeffy/.local/bin/milo-hermes" })
o.bind("SUPER + ALT + T", "Milo Aider QA Debugger", { tui = "/home/jeffy/.local/bin/milo-test" })
o.bind("SUPER + ALT + D", "Milo CEO Dispatcher", { tui = "/home/jeffy/.local/bin/milo-dispatch" })
o.bind("SUPER + ALT + S", "Milo Scratchpad Matrix", "/home/jeffy/.local/bin/milo-task gui")

--- Milo Tactical Control Center (Option B Native Overlay)
hl.unbind("SUPER + S")
o.bind("SUPER + S", "Milo Tactical Control Center", "/home/jeffy/.local/bin/milo-control-center toggle")



