-- Hyprland 0.55.4 (Lua). Choose Hyprland (uwsm-managed) in SDDM.
-- UWSM handles XDG autostart as systemd units; no exec-once daemons here.
hl.monitor({ output = "", mode = "preferred", position = "auto", scale = "auto" })
hl.config({
    general = {
        layout = "dwindle", gaps_in = 5, gaps_out = 10, border_size = 2,
        resize_on_border = true,
        extend_border_grab_area = 10,
        col = { active_border = "rgba(91a7bfff)", inactive_border = "rgba(363d47ff)" },
    },
    decoration = {
        rounding = 7, active_opacity = 1.0, inactive_opacity = 1.0,
        blur = { enabled = false }, shadow = { enabled = true, range = 8, color = "rgba(00000033)" },
    },
    animations = { enabled = false },
    dwindle = { preserve_split = true },
    input = { kb_layout = "us", follow_mouse = 1 },
    misc = { disable_hyprland_logo = true, force_default_wallpaper = 0,
             mouse_move_enables_dpms = true, key_press_enables_dpms = true },
})
-- Customize shortcuts here; the help list updates on reload.
dofile(os.getenv("HOME") .. "/.config/hypr/bindings.lua")

-- Keep advanced network settings and applet dialogs floating too.
hl.window_rule({
    name = "network-dialogs",
    match = { class = "^(nm-connection-editor|nm-applet)$" },
    float = true,
    size = "780 560",
    center = true,
})

-- Graphical Wi-Fi manager, separate from the tiled workspace.
hl.window_rule({
    name = "wifi-manager",
    match = { class = "^com\\.network\\.manager$" },
    float = true,
    size = "850 650",
    center = true,
})
