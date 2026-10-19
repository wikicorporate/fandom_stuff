local p = {}

local TAG_MAP = {
    ["<n0>"] = "<span class='text--bold'>",
    ["<n1>"] = "<span class='text--main'>",
    ["<n2>"] = "<span class='text--response'>",
    ["<n3>"] = "<span class='text--danger'>",
    ["<n4>"] = "<span class='text--message'>",
    ["<n5>"] = "<span class='text--n5'>",
    ["<n6>"] = "<span class='text--n6'>",
    ["<n7>"] = "<span class='text--n7'>",
    ["<n8>"] = "<span class='text--n8'>",
    ["<n9>"] = "<span class='text--n9'>",
    ["<n10>"] = "<span class='text--n10'>",
    ["<n11>"] = "<span class='text--n11'>",
    ["<n12>"] = "<span class='text--n12'>",
    ["<green>"] = "<span class='text--green'>",
    ["<red>"] = "<span class='text--danger'>",
    ["<mono>"] = "<span class='text--mono'>",
    ["<monolarge>"] = "<span class='text--monolarge'>",
    ["<title>"] = "<span class='text--title'>",
    ["<perma>"] = "<span class='text--perma'>",
    ["<smallbold>"] = "<span class='text--smallbold'>",
    ["<b>"] = "<span class='text--bold'>"
}

function p.e(frame)
    local args = frame.args
    if not args[1] then
        local parent = frame:getParent()
        if parent and parent.args then
            args = parent.args
        end
    end

    local text = args[1] or ""
    if text == "" then
        return ""
    end

    text = text:gsub("<([a-zA-Z0-9]+)>", function(tag)
        local key = "<" .. tag:lower() .. ">"
        return TAG_MAP[key] or ("<span class='text--" .. tag:lower() .. "'>")
    end)

    text = text:gsub("</>", "</span>")
    return text
end

return p
