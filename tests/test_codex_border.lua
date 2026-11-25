-- Exercise the real Lua callbacks, including color restoration after a pulse.
-- Run from the repository root: lua tests/test_codex_border.lua
local published = {}
local now = 1000
local written = now
local window = {
    address = "0x123", class = "com.mitchellh.ghostty", title = "Long job | project",
    mapped = true, hidden = false, workspace = { visible = true },
}
local colors = {
    ["general.col.active_border"] = { colors = { "0xFF91A7BF" }, angle = 0 },
    ["general.col.inactive_border"] = { colors = { "0xFF363D47" }, angle = 0 },
}
local props, events, timers = {}, {}, {}
local original_open, original_time, original_getenv = io.open, os.time, os.getenv
io.open = function(path, mode)
    if path:match("/codex%-border%-state$") then
        return {
            read = function() return tostring(written) end,
            lines = function()
                local i = 0
                return function() i = i + 1; return published[i] end
            end,
            close = function() end,
        }
    end
    return original_open(path, mode)
end
os.time = function() return now end
os.getenv = function(key)
    if key == "XDG_RUNTIME_DIR" then return "/unused-test-runtime" end
    return original_getenv(key)
end
hl = {
    get_config = function(key) return colors[key] end,
    get_windows = function() return { window } end,
    get_window = function() return window end,
    dsp = { window = { set_prop = function(action) return action end } },
    dispatch = function(action) props[action.prop] = action.value end,
    on = function(name, callback) events[name] = callback end,
    timer = function(callback)
        local timer = {
            callback = callback,
            set_enabled = function(self, enabled) self.enabled = enabled end,
        }
        timers[#timers + 1] = timer
        return timer
    end,
}

local function normal_border()
    assert(props.active_border_color == "0xFF91A7BF", "Active theme color was not restored")
    assert(props.inactive_border_color == "0xFF363D47", "Inactive theme color was not restored")
    assert(props.border_size == "unset", "Normal border width was not restored")
end
local function pulse()
    published = { window.address }
    written = now
    events["window.title"](window)
    timers[1].callback()
    assert(props.active_border_color:find("rgba", 1, true), "Confirmed idle window did not pulse")
    assert(props.border_size == "3")
end

dofile("home/.config/hypr/codex-border.lua")
normal_border()
pulse()
-- Actual turn state returns busy while its title still lacks a spinner.
published = {}
events["window.title"](window)
normal_border()
pulse()
window.title = "⠋ Long job | project"
events["window.title"](window)
normal_border()
window.title = "Long job | project"
pulse()
now = now + 4
timers[2].callback()
normal_border()

-- Restore the current desktop theme rather than hardcoded palette colors.
colors["general.col.active_border"] = { colors = { "0xFF112233" }, angle = 0 }
colors["general.col.inactive_border"] = { colors = { "0xFF445566" }, angle = 0 }
pulse()
published = {}
timers[2].callback()
assert(props.active_border_color == "0xFF112233")
assert(props.inactive_border_color == "0xFF445566")
io.open, os.time, os.getenv = original_open, original_time, original_getenv
print("Lua border transitions passed: idle, busy without spinner, resumed work, stale state, changed theme")
