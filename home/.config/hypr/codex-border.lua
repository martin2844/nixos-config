-- Animate only windows confirmed idle by codex-border-state.service.
-- A missing title spinner is never evidence that a turn or goal has finished.
local interval_ms = 50
local pulse_seconds = 2.4
local rotation_seconds = 10
local palette = {
    { 255, 83, 112 }, { 255, 180, 84 }, { 255, 230, 109 },
    { 92, 224, 154 }, { 84, 199, 236 }, { 167, 139, 255 },
    { 255, 83, 112 },
}
local spinners = {}
for _, frame in ipairs({ "⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏" }) do
    spinners[frame] = true
end
local tracked = {}
local elapsed = 0
local timer
local state_file = os.getenv("XDG_RUNTIME_DIR") .. "/codex-border-state"

local function definitely_busy(title)
    local first = title:match("^(%S+)")
    return spinners[first] or first == "●" or title:find("Action Required", 1, true)
end

local function set_prop(window, prop, value)
    hl.dispatch(hl.dsp.window.set_prop({ window = window, prop = prop, value = value }))
end

local function theme_gradient(key)
    local value = hl.get_config(key)
    if type(value) == "string" then return value end
    assert(type(value) == "table" and value.colors and #value.colors > 0,
        "Missing desktop border gradient: " .. key)
    if #value.colors == 1 then return value.colors[1] end
    -- The 0.55.4 multi-color dispatcher drops the first token, as below.
    return value.colors[1] .. " " .. table.concat(value.colors, " ") .. " "
        .. math.floor(value.angle or 0) .. "deg"
end

local function reset(window)
    -- In 0.55.4, -1 installs an empty gradient instead of removing the override.
    -- The shader then reads gradient[0] from a preceding window's GPU uniforms.
    -- Explicit nonempty theme colors prevent rainbow leaking to busy windows.
    set_prop(window, "active_border_color", theme_gradient("general.col.active_border"))
    set_prop(window, "inactive_border_color", theme_gradient("general.col.inactive_border"))
    set_prop(window, "border_size", "unset")
end

local function gradient()
    local brightness = 0.60 + 0.40 * (0.5 - 0.5 * math.cos(elapsed * 2 * math.pi / pulse_seconds))
    local colors = {}
    for _, rgb in ipairs(palette) do
        colors[#colors + 1] = string.format("rgba(%02x%02x%02xff)",
            math.floor(rgb[1] * brightness + 0.5),
            math.floor(rgb[2] * brightness + 0.5),
            math.floor(rgb[3] * brightness + 0.5))
    end
    -- Hyprland 0.55.4's multi-color set_prop parser skips the first token.
    -- Repeat the first color so the rendered gradient keeps the full palette.
    return colors[1] .. " " .. table.concat(colors, " ") .. " "
        .. math.floor(elapsed * 360 / rotation_seconds % 360) .. "deg"
end

local function visible_idle(window, state)
    return state == "idle" and window.mapped and not window.hidden
        and window.workspace and window.workspace.visible
end

local function animate()
    elapsed = elapsed + interval_ms / 1000
    local color
    local any_visible = false
    for address, state in pairs(tracked) do
        local window = hl.get_window("address:" .. address)
        if not window then
            tracked[address] = nil
        elseif visible_idle(window, state) then
            any_visible = true
            color = color or gradient()
            set_prop(window, "active_border_color", color)
            set_prop(window, "inactive_border_color", color)
        end
    end
    -- No polling or rendering while every session is busy or off-screen.
    timer:set_enabled(any_visible)
end

local function sync()
    local confirmed = {}
    local file = io.open(state_file, "r")
    if file then
        local written = tonumber(file:read("*l"))
        local age = written and os.time() - written
        -- Fail closed if the watcher stops, errors, or publishes a stale file.
        if age and age >= 0 and age <= 3 then
            for address in file:lines() do
                if address:match("^0x%x+$") then confirmed[address] = true end
            end
        end
        file:close()
    end
    for _, window in ipairs(hl.get_windows()) do
        if window.class == "com.mitchellh.ghostty" then
            local address = window.address
            local idle = confirmed[address] and not definitely_busy(window.title or "")
            if idle and not tracked[address] then
                tracked[address] = "idle"
                set_prop(window, "border_size", "3")
                timer:set_enabled(true)
            elseif not idle and tracked[address] then
                tracked[address] = nil
                reset(window)
            end
        end
    end
end

timer = hl.timer(animate, { timeout = interval_ms, type = "repeat" })
timer:set_enabled(false)
hl.on("window.title", sync)
hl.on("window.open", sync)
hl.on("window.close", function(window)
    if window then tracked[window.address] = nil end
end)
hl.on("workspace.active", function() timer:set_enabled(true) end)
hl.on("window.move_to_workspace", function() timer:set_enabled(true) end)
hl.on("config.reloaded", sync)
hl.timer(sync, { timeout = 500, type = "repeat" })

-- Clear properties left by earlier title-based versions when reloading.
for _, window in ipairs(hl.get_windows()) do
    if window.class == "com.mitchellh.ghostty" then reset(window) end
end
sync()
