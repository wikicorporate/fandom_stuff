local p = {}

local function split(inputstr, sep)
    if not inputstr or inputstr == "" then
        return {}
    end
    sep = sep or "%s"
    local t = {}
    for str in mw.ustring.gmatch(inputstr, "([^" .. sep .. "]+)") do
        table.insert(t, mw.text.trim(str))
    end
    return t
end

local tags = {
    ["Основатель"] = {"Основатель", "<i class='fa-solid fa-web-awesome'></i>"},
    ["Бюрократ"] = {"Бюрократ", "<i class='fa-solid fa-code'></i>"},
    ["Администратор"] = {"Администратор", "<i class='fa-solid fa-gear'></i>"},
    ["Модератор контента"] = {"Модератор контента", "<i class='fa-solid fa-gear'></i>"},
    ["Модератор сообщества"] = {"Модератор сообщества", "<i class='fa-solid fa-gear'></i>"},
    ["Администратор Discord"] = {"Администратор Discord", "<i class='fa-brands fa-discord'></i>"},
    ["Модератор Discord"] = {"Модератор Discord", "<i class='fa-brands fa-discord'></i>"},
    ["Откатчик"] = {"Откатчик", "<i class='fa-solid fa-clock-rotate-left'></i>"},
    ["Бот"] = {"Бот", "<i class='fa-solid fa-robot'></i>"}
}

local userdb = {
    ["Swit4er"] = "Основатель!Бюрократ!Администратор",
    ["Hwjeei"] = "Администратор"
}

function p.profiletags(frame)
    local nomi = mw.text.trim(frame.args[1] or "")
    if nomi == "" or not userdb[nomi] then
        return ""
    end

    local res = {}
    for _, value in ipairs(split(userdb[nomi], "!")) do
        local tag = tags[value]
        if tag then
            table.insert(
                res,
                string.format(
                    '<div class="user-tag">%s<div class="user-tag__tooltip">%s</div></div>',
                    tag[2],
                    tag[1]
                )
            )
        end
    end

    if #res == 0 then
        return ""
    end

    return '<div class="user-tags">' .. table.concat(res) .. '</div>'
end

return p
