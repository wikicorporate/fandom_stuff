local p = {}

local function split(inputstr, sep)
    if not inputstr or inputstr == "" then
        return {}
    end
    sep = sep or "%s"
    local t = {}
    for str in string.gmatch(inputstr, "([^" .. sep .. "]+)") do
        table.insert(t, mw.text.trim(str))
    end
    return t
end

local function prepareValue(raw)
    if not raw then return 0 end
    local prepared = tostring(raw):gsub("%%", ""):gsub(",", "."):gsub("%s+", "")
    return tonumber(prepared) or 0
end

local function generateBack(colors_arr, nums_arr)
    local backcolor = colors_arr[#colors_arr] or "transparent"
    for i, val in ipairs(nums_arr) do
        if prepareValue(val) >= 50 or i == #nums_arr then
            backcolor = colors_arr[i] or backcolor
            break
        end
    end
    return backcolor
end

local function GeneratePie(colors_str, nums_str)
    local colors_arr = split(colors_str, ".")
    local nums_arr = split(nums_str, ".")

    if #colors_arr == 0 or #nums_arr == 0 then
        return ""
    end

    local first_num = prepareValue(nums_arr[1])
    local back_color = generateBack(colors_arr, nums_arr)

    local parts = {
        '<div class="diagram-main">',
        string.format('<div class="pie-background" style="background-color: %s"></div>', back_color),
        string.format(
            '<div style="transform: rotate(270deg)" class="pie-piece"><div class="pie" style="background-color: %s; transform: rotate(%sdeg)"></div></div>',
            colors_arr[1],
            tostring(first_num * -3.6)
        )
    }

    local cumulative = first_num
    for i = 2, #colors_arr do
        local current_num = prepareValue(nums_arr[i])
        local rot1 = tostring(270 - (3.6 * cumulative)) .. "deg"
        local rot2 = tostring(current_num * -3.6) .. "deg"
        table.insert(
            parts,
            string.format(
                '<div style="transform: rotate(%s)" class="pie-piece"><div class="pie" style="background-color: %s; transform: rotate(%s)"></div></div>',
                rot1,
                colors_arr[i],
                rot2
            )
        )
        cumulative = cumulative + current_num
    end

    table.insert(parts, '</div>')
    return table.concat(parts)
end

function p.e(frame)
    local args = frame.args
    if not args[1] then
        local parent = frame:getParent()
        if parent and parent.args then
            args = parent.args
        end
    end

    local colors = args[1] or ""
    local nums = args[2] or ""
    return GeneratePie(colors, nums)
end

return p
