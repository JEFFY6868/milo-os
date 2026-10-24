-- Learn how to configure Hyprland: https://wiki.hypr.land/Configuring/Start/

-- Omarchy's bootstrap keeps path setup out of this user config.
dofile((os.getenv("OMARCHY_PATH") or "/usr/share/omarchy") .. "/default/hypr/bootstrap.lua")

-- Disable all Omarchy default bindings. Add your own in hypr/bindings.lua.
-- omarchy_default_bindings = false
--
-- Or disable only bindings for Omarchy's preinstalled apps/web apps while
-- keeping core window-manager bindings:
-- omarchy_preinstalled_bindings = false

-- Load Omarchy defaults.
require("default.hypr.omarchy")

-- Put your personal overrides in these files. They're loaded after Omarchy's
-- defaults so package updates can improve the defaults without rewriting your
-- ~/.config/hypr files.
require("hypr.monitors")
require("hypr.input")
require("hypr.bindings")
require("hypr.looknfeel")
require("hypr.autostart")

-- Toggle config flags dynamically.
require("default.hypr.toggles")

-- Add any other personal Hyprland configuration below.
-- o.window("qemu", { workspace = "5" })

-- Milo Spotlight Assistant modal rule
o.window({ class = "(milo|milo-app|org.omarchy.milo)", title = "^Milo$" }, {
    float = true,
    pin = true,
    center = true,
    stay_focused = true,
    tag = "-default-opacity",
    opacity = "1 1",
    border_size = 0,
})

-- Milo Live Wallpaper HUD rule
o.window({ class = "(milo|milo-app|org.omarchy.milo)", title = "^Milo Wallpaper$" }, {
    float = true,
    pin = true,
    tag = "-default-opacity",
    opacity = "1 1",
    border_size = 0,
    no_focus = true,
    move = "1430 50",
})

-- Kino Cinema Studio Director Suite Native Window Rule
o.window({ class = "kino-studio" }, {
    workspace = "4",
    tag = "-default-opacity",
    opacity = "0.98 0.95",
})
o.window({ title = "^Kino Cinema Studio" }, {
    workspace = "4",
    tag = "-default-opacity",
    opacity = "0.98 0.95",
})
