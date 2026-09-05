local p = {}

local monthsInGenetive = {
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря"
}

-- Безопасный перевод строки в число (извлекает только цифры)
local function parse_number(val)
    if not val then return 0 end
    local num = tostring(val):match("%d+")
    return tonumber(num) or 0
end

-- Склонение слова "год/года/лет"
local function ruslang_age(age)
    if age <= 0 then
        return "менее года"
    end
    
    local count = age % 100
    if count >= 5 and count <= 20 then 
        return age .. " лет"
    end
    
    count = count % 10
    if count == 1 then
        return age .. " год"
    elseif count >= 2 and count <= 4 then
        return age .. " года"
    else
        return age .. " лет"
    end
end

-- Вычисление возраста
local function GetAge(d, m, y)
    -- Получаем текущее системное время ровно 1 раз
    local today = os.date("*t") 
    local age = today.year - y
    
    -- Если день рождения в этом году ещё не наступил — отнимаем 1 год
    if today.month < m or (today.month == m and today.day < d) then
        age = age - 1
    end
    
    -- Защита от отрицательного возраста (если ввели дату из будущего)
    if age < 0 then age = 0 end
    
    return ruslang_age(age)
end

-- Основная функция: Формат "1 января 2000 (20 лет)"
function p.e(frame)
    local args = frame:getParent().args
    if not args[1] and frame.args[1] then
        args = frame.args
    end
    
    local d = parse_number(args[1])
    local m = parse_number(args[2])
    local y = parse_number(args[3])
    
    -- Защита от пустых или сломанных вызовов
    if d == 0 or m == 0 or y == 0 then
        return "'''[Ошибка: неверно указана дата]'''"
    end
    
    local month_str = monthsInGenetive[m] or "неизвестного месяца"
    local age_str = GetAge(d, m, y)
    
    return string.format("%d %s %d (%s)", d, month_str, y, age_str)
end

-- Альтернативная функция: Просто количество лет (например: "20 лет")
function p.e2(frame)
    local args = frame:getParent().args
    if not args[1] and frame.args[1] then
        args = frame.args
    end
    
    local d = parse_number(args[1])
    local m = parse_number(args[2])
    local y = parse_number(args[3])
    
    if d == 0 or m == 0 or y == 0 then
        return ""
    end
    
    return GetAge(d, m, y)
end

return p
