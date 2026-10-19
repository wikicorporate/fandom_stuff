local p = {}

local function count_bullets(base)
    if not base or base == "" then
        return 0
    end
    local _, total = string.gsub(base, "%*%s", "")
    return total
end

function p.e(frame)
    local args = frame.args
    if not args[1] then
        local parent = frame:getParent()
        if parent and parent.args then
            args = parent.args
        end
    end

    local content = args[1] or ""
    if content == "" then
        return ""
    end

    if count_bullets(content) > 4 then
        return '<div class="mw-collapsible mw-collapsed">\n' .. content .. '\n</div>'
    end

    return content
end

return p
