local p = {}

local tabli = mw.loadData('Модуль:Медиа/Данные')

-- Быстрая нативная декодировка вместо ручного string.char
function p.decodeString(str)
    if str and str ~= "" then
        return mw.uri.decode(str, "WIKI")
    end
    return ""
end

function p.e(frame)
    -- Защита от nil (если шаблон вызвали вообще без аргументов)
    if not frame.args[1] or frame.args[1] == "" then return "" end
    
    local typeofcall = mw.ustring.upper(frame.args[1])
    
    -- Собираем аргументы, игнорируя первый (это ключ)
    local argsList = {}
    for i = 2, 10 do -- Ограничиваемся 10 аргументами
        if frame.args[i] and frame.args[i] ~= "" then
            table.insert(argsList, frame.args[i])
        else
            break -- Прерываем цикл на первом же пустом аргументе
        end
    end
    
    local numofargs = #argsList
    
    -- Логика разрешения псевдонимов
    local serviceData = tabli[typeofcall]
    
    -- Если по ключу лежит строка (например, 'YOUTUBE'), значит это псевдоним.
    -- Запрашиваем реальные данные по этому псевдониму.
    if type(serviceData) == "string" then
        serviceData = tabli[serviceData]
    end
    
    -- Если сервис или нужное количество аргументов не найдено
    if not serviceData or not serviceData[numofargs] then
        return "'''[Ошибка: Неверный формат или сервис не поддерживается]'''"
    end
    -- ===========================================
    
    local text = serviceData[numofargs].pattern
    
    -- Вживляем аргументы в строку
    for i, v in ipairs(argsList) do
        local decodedArg = p.decodeString(v)
        -- Заменяем $url1, $url2... (с заменой пробелов на %20)
        local urlArg = decodedArg:gsub(" ", "%%20")
        text = text:gsub("%$url" .. tostring(i), urlArg)
        -- Заменяем обычные $1, $2...
        text = text:gsub("%$" .. tostring(i), decodedArg)
    end
    
    return text
end

return p
