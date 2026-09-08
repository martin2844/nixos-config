-- Register descriptions and generate the searchable help from the same bindings.
local shortcuts = {}
local shortcutByKey = {}
local motionKeys = { left = "H", down = "J", up = "K", right = "L" }
local function motionKey(key)
    return (key:gsub("(%S+)$", motionKeys))
end
local function bind(key, action, description, options)
    key = motionKey(key)
    options = options or {}
    options.description = description
    hl.bind(key, action, options)
    local displayKey = key:gsub("mouse:272", "Left mouse drag"):gsub("mouse:273", "Right mouse drag")
        :gsub("minus", "-"):gsub("equal", "=")
    local row = string.format("%-38s  %s", displayKey, description)
    table.insert(shortcuts, row)
    shortcutByKey[key] = row
end
local function app(key, command, description)
    bind(key, hl.dsp.exec_cmd("uwsm app -- " .. command), description)
end
app("SUPER + Return", "ghostty", "Open terminal")
app("SUPER + E", "dolphin", "Open file manager")
app("SUPER + space", "rofi -show drun", "Application launcher")
app("SUPER + slash", os.getenv("HOME") .. "/.config/hypr/scripts/shortcuts", "Search keyboard shortcuts")
app("SUPER + V", os.getenv("HOME") .. "/.config/hypr/scripts/clipboard", "Clipboard history")
app("Print", os.getenv("HOME") .. "/.config/hypr/scripts/screenshot full", "Screenshot entire desktop")
app("SHIFT + Print", os.getenv("HOME") .. "/.config/hypr/scripts/screenshot region", "Screenshot region and edit")
bind("ALT + F4", hl.dsp.window.close(), "Close window")
bind("SUPER + F", hl.dsp.window.fullscreen({ mode = "fullscreen", action = "toggle" }), "Toggle fullscreen")
bind("SUPER + T", function()
    local window = hl.get_active_window()
    if not window then return end
    local wasFloating = window.floating
    hl.dispatch(hl.dsp.window.fullscreen_state({ internal = 0, client = 0, action = "set" }))
    -- Pseudo tiling can retain a tiny size while reserving an entire tile.
    -- Returning to normal tiling should always fill the available tile.
    hl.dispatch(hl.dsp.window.pseudo({ action = "off" }))
    if wasFloating then
        hl.dispatch(hl.dsp.window.float({ action = "off" }))
    else
        hl.dispatch(hl.dsp.window.float({ action = "on" }))
        local monitor = hl.get_active_monitor()
        if monitor then
            local scale = monitor.scale > 0 and monitor.scale or 1
            hl.dispatch(hl.dsp.window.resize({
                x = math.floor(math.min(1100, monitor.width / scale * 0.65)),
                y = math.floor(math.min(750, monitor.height / scale * 0.65)),
            }))
        end
        hl.dispatch(hl.dsp.window.center())
    end
end, "Float at centered size / return to tiling")
-- Capitalized Right keeps this explicitly chosen arrow outside motion remapping.
bind("SUPER + Right", function()
    local workspace = hl.get_active_workspace()
    if not workspace then return end
    local layout = workspace.tiled_layout == "dwindle" and "scrolling" or "dwindle"
    hl.workspace_rule({ workspace = tostring(workspace.id), layout = layout })
end, "Toggle workspace layout (dwindle / scrolling)")
app("SUPER + N", "swaync-client -t", "Notification center")
app("SUPER + SHIFT + E", os.getenv("HOME") .. "/.config/hypr/scripts/session-menu", "Session menu / log out / power")
for _, dir in ipairs({"left", "right", "up", "down"}) do
    bind("SUPER + " .. dir, hl.dsp.focus({ direction = dir }), "Focus window " .. dir)
    bind("SUPER + SHIFT + " .. dir, hl.dsp.window.swap({ direction = dir }), "Swap window " .. dir)
end
for i = 1, 10 do
    local key = i % 10
    bind("SUPER + " .. key, hl.dsp.focus({ workspace = i }), "Switch to workspace " .. i)
    bind("SUPER + SHIFT + " .. key, hl.dsp.window.move({ workspace = i }), "Move window to workspace " .. i)
end
bind("SUPER + mouse:272", hl.dsp.window.drag(), "Move / rearrange window")
bind("SUPER + mouse:273", hl.dsp.window.resize(), "Resize window")
for _, audio in ipairs({
    { "XF86AudioRaiseVolume", "wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ 5%+", "Volume up" },
    { "XF86AudioLowerVolume", "wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-", "Volume down" },
    { "XF86AudioMute", "wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle", "Toggle speaker mute" },
    { "XF86AudioMicMute", "wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle", "Toggle microphone mute" },
}) do
    bind(audio[1], hl.dsp.exec_cmd(audio[2]), audio[3], { locked = true, repeating = audio[1]:find("Volume") ~= nil })
end
bind("SUPER + M", hl.dsp.exec_cmd("wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle"), "Toggle microphone mute")

-- Omarchy tiling-v2 and app bindings, adapted to this NixOS/Lua desktop.
-- Omarchy window/tiling controls. Lock is Super+Ctrl+Escape; Super+/ retains full help.
bind("SUPER + Q", hl.dsp.window.close(), "Close window")
bind("SUPER + W", function()
    local window = hl.get_active_window()
    local workspace = hl.get_active_workspace()
    if not window or not workspace or workspace.tiled_layout ~= "dwindle" then return end
    hl.dispatch(hl.dsp.window.fullscreen_state({ internal = 0, client = 0, action = "set" }))
    hl.dispatch(hl.dsp.window.pseudo({ action = "off" }))
    hl.dispatch(hl.dsp.window.float({ action = "off" }))
    -- Already-root windows need only the ratio reset; movetoroot is a no-op there.
    hl.dispatch(hl.dsp.layout("movetoroot"))
    hl.dispatch(hl.dsp.layout("splitratio 1.0 exact"))
    -- At the root with a 50/50 ratio, a top/bottom tile spans more of
    -- the monitor's width than height. Rotate only that orientation.
    local monitor = hl.get_active_monitor()
    if monitor then
        local size = window.size
        if size.x / monitor.width > size.y / monitor.height then
            hl.dispatch(hl.dsp.layout("togglesplit"))
        end
    end
end, "Give window full-height left/right half (dwindle)")
bind("SUPER + CTRL + J", hl.dsp.layout("togglesplit"), "Toggle window split")
bind("SUPER + P", hl.dsp.window.pseudo(), "Toggle pseudo tiling (small window inside reserved tile)")
bind("SUPER + ALT + F", hl.dsp.window.fullscreen({ mode = "maximized" }), "Full width / maximize")
bind("SUPER + CTRL + F", hl.dsp.window.fullscreen_state({ internal = 0, client = 2 }), "Tiled fullscreen")
bind("SUPER + O", function()
    hl.dispatch(hl.dsp.window.float({ action = "on" }))
    hl.dispatch(hl.dsp.window.pin())
end, "Float and toggle pin window")
app("SUPER + CTRL + K", os.getenv("HOME") .. "/.config/hypr/scripts/shortcuts windows", "Window-management shortcuts (Omarchy order)")
app("SUPER + Escape", os.getenv("HOME") .. "/.config/hypr/scripts/session-menu", "Session / power menu")
app("SUPER + SHIFT + F", "dolphin", "File manager")
app("SUPER + SHIFT + Return", "google-chrome", "Browser")
app("SUPER + SHIFT + B", "google-chrome", "Browser")
app("SUPER + SHIFT + ALT + B", "google-chrome --incognito", "Private browser")
app("SUPER + SHIFT + N", "ghostty -e nvim", "Neovim editor")
app("SUPER + SHIFT + O", "obsidian", "Obsidian")
app("SUPER + SHIFT + A", os.getenv("HOME") .. "/.nix-profile/bin/chatgpt", "ChatGPT desktop")
app("SUPER + CTRL + A", "pavucontrol", "Audio controls")
app("SUPER + CTRL + B", "blueman-manager", "Bluetooth controls")
app("SUPER + CTRL + W", os.getenv("HOME") .. "/.nix-profile/bin/nmgui", "Wi-Fi / network controls")
bind("SUPER + CTRL + Escape", hl.dsp.exec_cmd("loginctl lock-session"), "Lock screen")
bind("SUPER + SHIFT + space", hl.dsp.exec_cmd("pkill -SIGUSR1 -x waybar"), "Toggle status bar")
app("SUPER + CTRL + space", os.getenv("HOME") .. "/.config/hypr/scripts/wallpaper", "Choose wallpaper")
for key, workspace in pairs({ ["SUPER + Tab"] = "e+1", ["SUPER + SHIFT + Tab"] = "e-1",
    ["SUPER + CTRL + Tab"] = "previous", ["SUPER + mouse_down"] = "e+1", ["SUPER + mouse_up"] = "e-1" }) do
    bind(key, hl.dsp.focus({ workspace = workspace }), "Switch workspace " .. workspace)
end
for _, dir in ipairs({"left", "right", "up", "down"}) do
    bind("SUPER + SHIFT + ALT + " .. dir, hl.dsp.workspace.move({ monitor = dir:sub(1,1) }), "Move workspace to monitor " .. dir)
    bind("SUPER + ALT + " .. dir, hl.dsp.window.move({ into_group = dir }), "Join window group " .. dir)
end
bind("CTRL + ALT + Tab", hl.dsp.focus({ monitor = "+1" }), "Focus next monitor")
bind("CTRL + ALT + SHIFT + Tab", hl.dsp.focus({ monitor = "-1" }), "Focus previous monitor")
for _, spec in ipairs({{"ALT + Tab", true}, {"ALT + SHIFT + Tab", false}}) do
    bind(spec[1], function()
        hl.dispatch(hl.dsp.window.cycle_next({ next = spec[2] }))
        hl.dispatch(hl.dsp.window.bring_to_top())
    end, spec[2] and "Next window" or "Previous window")
end
for _, spec in ipairs({{"SUPER + minus", -100, 0}, {"SUPER + equal", 100, 0},
    {"SUPER + SHIFT + minus", 0, -100}, {"SUPER + SHIFT + equal", 0, 100}}) do
    bind(spec[1], hl.dsp.window.resize({ x = spec[2], y = spec[3], relative = true }),
        "Resize window by " .. spec[2] .. ", " .. spec[3], { repeating = true })
end
for i = 1, 10 do
    bind("SUPER + SHIFT + ALT + " .. (i % 10), hl.dsp.window.move({ workspace = i, follow = false }), "Move silently to workspace " .. i)
end
bind("SUPER + S", hl.dsp.workspace.toggle_special("scratchpad"), "Toggle scratchpad")
bind("SUPER + ALT + S", hl.dsp.window.move({ workspace = "special:scratchpad", follow = false }), "Move window to scratchpad")
bind("SUPER + G", hl.dsp.group.toggle(), "Toggle window group")
bind("SUPER + ALT + G", hl.dsp.window.move({ out_of_group = true }), "Move window out of group")
bind("SUPER + ALT + mouse_down", hl.dsp.group.next(), "Next grouped window")
bind("SUPER + ALT + mouse_up", hl.dsp.group.prev(), "Previous grouped window")
bind("SUPER + ALT + Tab", hl.dsp.group.next(), "Next grouped window")
bind("SUPER + ALT + SHIFT + Tab", hl.dsp.group.prev(), "Previous grouped window")
bind("SUPER + CTRL + left", hl.dsp.group.prev(), "Previous grouped window")
bind("SUPER + CTRL + right", hl.dsp.group.next(), "Next grouped window")
for i = 1, 5 do
    bind("SUPER + ALT + " .. i, hl.dsp.group.active({ index = i }), "Focus group window " .. i)
end

-- Refreshed on every config load; add future bindings through bind()/app() above.
local cache = os.getenv("XDG_CACHE_HOME") or (os.getenv("HOME") .. "/.cache")
local help = assert(io.open(cache .. "/hypr-shortcuts.txt", "w"))
help:write(table.concat(shortcuts, "\n"), "\n")
help:close()

-- Presentation order follows Omarchy's tiling-v2.conf. Descriptions come from
-- the actual bindings above, so help cannot drift from their assigned actions.
local windowHelp = {}
local function section(title, keys)
    if #windowHelp > 0 then table.insert(windowHelp, "") end
    table.insert(windowHelp, "── " .. title .. " ──")
    for _, key in ipairs(keys) do
        local row = assert(shortcutByKey[motionKey(key)], "Missing binding: " .. key)
        table.insert(windowHelp, row)
    end
end
local function directions(prefix)
    local keys = {}
    for _, dir in ipairs({"left", "right", "up", "down"}) do table.insert(keys, prefix .. dir) end
    return keys
end
local function numbers(prefix, count)
    local keys = {}
    for i = 1, count do table.insert(keys, prefix .. (i % 10)) end
    return keys
end
section("Close windows", {"SUPER + Q", "ALT + F4"})
section("Control tiling", {"SUPER + W", "SUPER + CTRL + J", "SUPER + P", "SUPER + T", "SUPER + F", "SUPER + CTRL + F", "SUPER + ALT + F", "SUPER + O", "SUPER + Right"})
section("Move focus", directions("SUPER + "))
section("Switch workspaces", numbers("SUPER + ", 10))
section("Move window to workspace", numbers("SUPER + SHIFT + ", 10))
section("Move window silently", numbers("SUPER + SHIFT + ALT + ", 10))
section("Scratchpad", {"SUPER + S", "SUPER + ALT + S"})
section("Cycle workspaces", {"SUPER + Tab", "SUPER + SHIFT + Tab", "SUPER + CTRL + Tab"})
section("Move workspace to monitor", directions("SUPER + SHIFT + ALT + "))
section("Swap windows", directions("SUPER + SHIFT + "))
section("Cycle windows", {"ALT + Tab", "ALT + SHIFT + Tab"})
section("Cycle monitors", {"CTRL + ALT + Tab", "CTRL + ALT + SHIFT + Tab"})
section("Resize window", {"SUPER + minus", "SUPER + equal", "SUPER + SHIFT + minus", "SUPER + SHIFT + equal"})
section("Scroll workspaces", {"SUPER + mouse_down", "SUPER + mouse_up"})
section("Mouse move / resize", {"SUPER + mouse:272", "SUPER + mouse:273"})
section("Toggle groups", {"SUPER + G", "SUPER + ALT + G"})
section("Join groups", directions("SUPER + ALT + "))
section("Navigate grouped windows", {"SUPER + ALT + Tab", "SUPER + ALT + SHIFT + Tab", "SUPER + CTRL + left", "SUPER + CTRL + right"})
section("Scroll grouped windows", {"SUPER + ALT + mouse_down", "SUPER + ALT + mouse_up"})
section("Activate group window", numbers("SUPER + ALT + ", 5))
local windowFile = assert(io.open(cache .. "/hypr-window-shortcuts.txt", "w"))
windowFile:write(table.concat(windowHelp, "\n"), "\n")
windowFile:close()
