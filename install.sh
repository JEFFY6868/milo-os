#!/usr/bin/env bash
# ==============================================================================
# ⚡ MILO AI & KINO CINEMA OS - MASTER RECOVERY & INSTALLER SCRIPT
# Single-command turnkey installer to restore Milo & Kino on Arch Linux / Omarchy
# ==============================================================================

set -e

COLOR_CYAN='\033[0;36m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_RED='\033[0;31m'
COLOR_BOLD='\033[1m'
COLOR_RESET='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${COLOR_CYAN}${COLOR_BOLD}"
echo "================================================================="
echo "   🤖 MILO AI & KINO CINEMA ECOSYSTEM - FULL RESTORATION   "
echo "================================================================="
echo -e "${COLOR_RESET}"

# 1. System Package Requirements
echo -e "${COLOR_YELLOW}[1/8] Checking system packages (Arch Linux)...${COLOR_RESET}"
PACKAGES=(python python-pip git ffmpeg sox alsa-utils qrencode jq curl rsync)
MISSING_PKGS=()

for pkg in "${PACKAGES[@]}"; do
    if ! pacman -Qi "$pkg" &>/dev/null; then
        MISSING_PKGS+=("$pkg")
    fi
done

if [ ${#MISSING_PKGS[@]} -gt 0 ]; then
    echo -e "${COLOR_YELLOW}Installing missing packages: ${MISSING_PKGS[*]}...${COLOR_RESET}"
    sudo pacman -S --needed --noconfirm "${MISSING_PKGS[@]}"
else
    echo -e "${COLOR_GREEN}✓ All core system dependencies installed.${COLOR_RESET}"
fi

# 2. Setup Dotfiles (Hyprland, Omarchy, Quickshell, Foot)
echo -e "\n${COLOR_YELLOW}[2/8] Restoring dotfiles & desktop configuration...${COLOR_RESET}"
mkdir -p "$HOME/.config/hypr" "$HOME/.config/omarchy" "$HOME/.config/foot" "$HOME/.config/milo"

# Hyprland
if [ -d "$SCRIPT_DIR/dotfiles/hypr" ]; then
    rsync -av --update "$SCRIPT_DIR/dotfiles/hypr/" "$HOME/.config/hypr/"
    echo -e "${COLOR_GREEN}✓ Hyprland configs restored (~/.config/hypr)${COLOR_RESET}"
fi

# Omarchy & Quickshell Milo Plugin
if [ -d "$SCRIPT_DIR/dotfiles/omarchy" ]; then
    rsync -av --update "$SCRIPT_DIR/dotfiles/omarchy/" "$HOME/.config/omarchy/"
    echo -e "${COLOR_GREEN}✓ Omarchy & Quickshell Milo HUD plugin restored (~/.config/omarchy)${COLOR_RESET}"
fi

# Foot Terminal
if [ -d "$SCRIPT_DIR/dotfiles/foot" ]; then
    rsync -av --update "$SCRIPT_DIR/dotfiles/foot/" "$HOME/.config/foot/"
    echo -e "${COLOR_GREEN}✓ Foot terminal config restored (~/.config/foot)${COLOR_RESET}"
fi

# Milo Config
if [ -f "$SCRIPT_DIR/dotfiles/milo/config.json" ]; then
    cp "$SCRIPT_DIR/dotfiles/milo/config.json" "$HOME/.config/milo/config.json"
fi

if [ ! -f "$HOME/.config/milo/browser.env" ]; then
    if [ -f "$SCRIPT_DIR/dotfiles/milo/browser.env.example" ]; then
        cp "$SCRIPT_DIR/dotfiles/milo/browser.env.example" "$HOME/.config/milo/browser.env"
        echo -e "${COLOR_YELLOW}⚠ Created ~/.config/milo/browser.env template. Please add your GEMINI_API_KEY!${COLOR_RESET}"
    fi
else
    echo -e "${COLOR_GREEN}✓ Existing ~/.config/milo/browser.env preserved.${COLOR_RESET}"
fi

# 3. Restore Milo CLI binaries
echo -e "\n${COLOR_YELLOW}[3/8] Installing Milo CLI commands into ~/.local/bin...${COLOR_RESET}"
mkdir -p "$HOME/.local/bin"
cp -a "$SCRIPT_DIR/milo-core/bin/"* "$HOME/.local/bin/"
chmod +x "$HOME/.local/bin/milo"*
echo -e "${COLOR_GREEN}✓ Installed 10 Milo commands (milo, milo-query, milo-kino, milo-reflect, etc.)${COLOR_RESET}"

# Ensure ~/.local/bin is in PATH
if ! echo "$PATH" | grep -q "$HOME/.local/bin"; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    [ -f "$HOME/.zshrc" ] && echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc"
    export PATH="$HOME/.local/bin:$PATH"
fi

# 4. Restore Milo Core & Kino Studio Files
echo -e "\n${COLOR_YELLOW}[4/8] Deploying Milo Core & Kino Studio...${COLOR_RESET}"
mkdir -p "$HOME/.local/share/milo/kino" "$HOME/.local/share/milo/voice"

rsync -av --update "$SCRIPT_DIR/milo-core/kino/" "$HOME/.local/share/milo/kino/"
rsync -av --update "$SCRIPT_DIR/milo-core/voice/" "$HOME/.local/share/milo/voice/"
[ -f "$SCRIPT_DIR/milo-core/browser_agent.py" ] && cp "$SCRIPT_DIR/milo-core/browser_agent.py" "$HOME/.local/share/milo/"
[ -f "$SCRIPT_DIR/milo-core/wa_bridge.py" ] && cp "$SCRIPT_DIR/milo-core/wa_bridge.py" "$HOME/.local/share/milo/"
echo -e "${COLOR_GREEN}✓ Milo Core, Kino Agent, and Studio deployed to ~/.local/share/milo${COLOR_RESET}"

# 5. Setup Python Virtual Environment
echo -e "\n${COLOR_YELLOW}[5/8] Setting up Python virtual environment...${COLOR_RESET}"
VENV_DIR="$HOME/.local/share/milo/venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment at $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
fi

echo "Installing/updating Python dependencies from requirements.txt..."
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$SCRIPT_DIR/milo-core/requirements.txt"
echo -e "${COLOR_GREEN}✓ Python virtual environment ready.${COLOR_RESET}"

# 6. Initialize Obsidian Neural Vault
echo -e "\n${COLOR_YELLOW}[6/8] Initializing Obsidian Neural Vault...${COLOR_RESET}"
VAULT_DIR="$HOME/Documents/Obsidian/Milo"
mkdir -p "$VAULT_DIR"/{Daily,Memories,Profile,Cinema,Knowledge}

if [ -d "$SCRIPT_DIR/obsidian-template" ]; then
    rsync -av --ignore-existing "$SCRIPT_DIR/obsidian-template/" "$VAULT_DIR/"
fi
echo -e "${COLOR_GREEN}✓ Obsidian Neural Vault initialized at $VAULT_DIR${COLOR_RESET}"

# 7. Setup Android Native App
echo -e "\n${COLOR_YELLOW}[7/8] Setting up Android Native App...${COLOR_RESET}"
ANDROID_DIR="$HOME/milo-android-native"
if [ -d "$SCRIPT_DIR/android/milo-android-native" ]; then
    mkdir -p "$ANDROID_DIR"
    rsync -av --update "$SCRIPT_DIR/android/milo-android-native/" "$ANDROID_DIR/"
    
    # Copy APK to studio static for direct mobile downloads
    STATIC_DIR="$HOME/.local/share/milo/kino/studio/static"
    mkdir -p "$STATIC_DIR"
    if [ -f "$ANDROID_DIR/MiloNativeCall.apk" ]; then
        cp "$ANDROID_DIR/MiloNativeCall.apk" "$STATIC_DIR/MiloNativeCall.apk"
        ln -sf MiloNativeCall.apk "$STATIC_DIR/milo.apk"
        ln -sf MiloNativeCall.apk "$STATIC_DIR/app.apk"
        ln -sf MiloNativeCall.apk "$STATIC_DIR/MiloNativeCall.apk "
        echo -e "${COLOR_GREEN}✓ MiloNativeCall.apk linked for web distribution${COLOR_RESET}"
    fi
fi

# 8. Install and Enable Systemd User Services
echo -e "\n${COLOR_YELLOW}[8/8] Configuring and enabling systemd user services...${COLOR_RESET}"
mkdir -p "$HOME/.config/systemd/user"
cp -a "$SCRIPT_DIR/milo-core/systemd/"* "$HOME/.config/systemd/user/"

systemctl --user daemon-reload
systemctl --user enable --now milo-kino-studio.service
echo -e "${COLOR_GREEN}✓ milo-kino-studio.service enabled and started!${COLOR_RESET}"

# Final Status Check
echo -e "\n${COLOR_CYAN}=================================================================${COLOR_RESET}"
echo -e "${COLOR_GREEN}${COLOR_BOLD}🎉 FULL RESTORATION COMPLETE!${COLOR_RESET}"
echo -e "${COLOR_CYAN}=================================================================${COLOR_RESET}"
echo -e "• Milo CLI:           ${COLOR_BOLD}milo status${COLOR_RESET} / ${COLOR_BOLD}milo-query \"hello\"${COLOR_RESET}"
echo -e "• Kino Cinema Studio: ${COLOR_BOLD}http://localhost:3140${COLOR_RESET}"
echo -e "• Android App:        ${COLOR_BOLD}http://localhost:3140/download${COLOR_RESET}"
echo -e "• Obsidian Vault:     ${COLOR_BOLD}$HOME/Documents/Obsidian/Milo${COLOR_RESET}"
echo -e "${COLOR_CYAN}=================================================================${COLOR_RESET}"
