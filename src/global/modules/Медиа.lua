local p = {}

local tabli = mw.loadData('Модуль:Медиа/Данные')

function p.decodeString(str)
    if str and str ~= "" then
        return mw.uri.decode(str, "PATH")
    end
    return ""
end

function p.e(frame)
    local args = frame.args
    if not args[1] or mw.text.trim(args[1]) == "" then
        local parent = frame:getParent()
        if parent and parent.args and parent.args[1] then
            args = parent.args
        else
            return ""
        end
    end

    local serviceKey = mw.text.trim(args[1] or "")
    if serviceKey == "" then
        return ""
    end

    local typeofcall = mw.ustring.upper(serviceKey)

    local argsList = {}
    for i = 2, 10 do
        local rawVal = args[i]
        if rawVal then
            local trimmed = mw.text.trim(rawVal)
            if trimmed ~= "" then
                table.insert(argsList, trimmed)
            else
                break
            end
        else
            break
        end
    end

    local numofargs = #argsList
    local serviceData = tabli[typeofcall]

    if type(serviceData) ~= "table" or not serviceData[numofargs] then
        return "'''[Ошибка: Неверный формат или сервис не поддерживается]'''"
    end

    local text = serviceData[numofargs].pattern

    for i, v in ipairs(argsList) do
        local decodedArg = p.decodeString(v)
        local urlArg = decodedArg:gsub(" ", "%%20")
        text = text:gsub("%$url" .. tostring(i), function() return urlArg end)
        text = text:gsub("%$" .. tostring(i), function() return decodedArg end)
    end

    return text
end

return p
