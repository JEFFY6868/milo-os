#!/usr/bin/env python3
"""
Kino Cinema Studio — Native Linux Desktop Application
Powered by GTK3 & WebKit2. Runs as a dedicated native Wayland window.
"""

import sys
import os
import signal
import subprocess
import time
from pathlib import Path

# Ensure backend service is up
def ensure_backend():
    try:
        import urllib.request
        urllib.request.urlopen("http://127.0.0.1:3140/api/status", timeout=1)
    except Exception:
        os.system("systemctl --user start milo-kino-studio.service >/dev/null 2>&1")
        # Give it a second
        for _ in range(10):
            try:
                import urllib.request
                urllib.request.urlopen("http://127.0.0.1:3140/api/status", timeout=0.5)
                break
            except Exception:
                time.sleep(0.3)

ensure_backend()

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('WebKit2', '4.1')
from gi.repository import Gtk, Gdk, WebKit2, GLib, GdkPixbuf

class KinoDesktopApp(Gtk.Window):
    def __init__(self, target_url="http://127.0.0.1:3140"):
        super().__init__(title="Kino Cinema Studio — Director's Workstation")

        # Window Metadata & WM Class for Hyprland
        self.set_wmclass("kino-studio", "KinoStudio")
        self.set_role("kino-studio")
        self.set_default_size(1560, 920)
        self.set_position(Gtk.WindowPosition.CENTER)

        # Dark theme preference
        settings = Gtk.Settings.get_default()
        if settings:
            settings.set_property("gtk-application-prefer-dark-theme", True)

        # Set Window Icon
        icon_path = Path.home() / ".local" / "share" / "icons" / "kino.svg"
        if icon_path.exists():
            try:
                self.set_icon_from_file(str(icon_path))
            except Exception:
                pass

        # Configure WebKit Settings
        web_settings = WebKit2.Settings()
        web_settings.set_enable_developer_extras(True)
        web_settings.set_enable_smooth_scrolling(True)
        web_settings.set_enable_webgl(True)
        web_settings.set_enable_page_cache(True)
        web_settings.set_javascript_can_access_clipboard(True)

        # Initialize WebView
        self.webview = WebKit2.WebView.new_with_settings(web_settings)
        self.webview.connect("permission-request", self.on_permission_request)
        
        # OLED Deep Dark Background Color to eliminate any white flicker
        bg_rgba = Gdk.RGBA()
        bg_rgba.red = 0.03
        bg_rgba.green = 0.04
        bg_rgba.blue = 0.05
        bg_rgba.alpha = 1.0
        self.webview.set_background_color(bg_rgba)

        # Scrolled container
        scrolled = Gtk.ScrolledWindow()
        scrolled.add(self.webview)
        self.add(scrolled)

        # Load Studio URL
        self.webview.load_uri(target_url)

        # Connect Key Bindings
        self.connect("key-press-event", self.on_key_press)
        self.connect("destroy", Gtk.main_quit)
        self.is_fullscreen = False

    def on_permission_request(self, webview, request):
        # Auto-grant UserMedia (microphone/audio) for local Studio
        if isinstance(request, WebKit2.UserMediaPermissionRequest):
            request.allow()
            return True
        return False

    def on_key_press(self, widget, event):
        keyval = event.keyval
        state = event.state & Gtk.accelerator_get_default_mod_mask()

        # F11: Toggle Fullscreen
        if keyval == Gdk.KEY_F11:
            if self.is_fullscreen:
                self.unfullscreen()
                self.is_fullscreen = False
            else:
                self.fullscreen()
                self.is_fullscreen = True
            return True

        # Ctrl + R: Reload
        if (state & Gdk.ModifierType.CONTROL_MASK) and keyval in (Gdk.KEY_r, Gdk.KEY_R):
            self.webview.reload()
            return True

        # Ctrl + Q: Quit
        if (state & Gdk.ModifierType.CONTROL_MASK) and keyval in (Gdk.KEY_q, Gdk.KEY_Q):
            self.destroy()
            return True

        return False


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    GLib.set_prgname("kino-studio")
    GLib.set_application_name("Kino Cinema Studio")

    target_url = "http://127.0.0.1:3140"
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ("voice", "call"):
            target_url = "http://127.0.0.1:3140/?tab=voice&autocall=1"
        elif arg.startswith("http"):
            target_url = sys.argv[1]

    app = KinoDesktopApp(target_url=target_url)
    app.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
