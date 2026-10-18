local p = {}

-- Словарь персон для мгновенного поиска (O(1) вместо 22 проходов O(N))
local personas = {
    ["Габриэль Браун"] = "пилотный эпизод, вокал",
    ["Дэйв Кэпдевиль"] = "пилотный эпизод",
    ["Джошуа Томар"] = "пилотный эпизод",
    ["Келли Бойер"] = "вокал",
    ["Кристал Лапорте"] = "пилотный эпизод",
    ["Майкл Ковач"] = "пилотный эпизод, вокал",
    ["Мик Лауэр"] = "пилотный эпизод",
    ["Мишель Мари"] = "пилотный эпизод",
    ["Стэмпер"] = "пилотный эпизод",
    ["Элси Лавлок"] = "пилотный эпизод, вокал",
    ["Джеймс Монро Иглхарт"] = "пилотный эпизод",
    ["Дон Дэррил Ривера"] = "пилотный эпизод",
    ["Максвелл Атомс"] = "пилотный эпизод",
    ["Сет Аткинсон"] = "промо",
    ["Брок Бейкер"] = "пилотный эпизод",
    ["Морган Шиван Грин"] = "вокал",
    ["Рошель Диаманте"] = "вокал",
    ["Эллисон Каплан"] = "вокал",
    ["Майкл Джеймс Руокко"] = "пилотный эпизод",
    ["Мэгпай Рэйвэн"] = "пилотный эпизод, комиксы",
    ["Эшли Николс"] = "пилотный эпизод",
    ["Faustisse"] = "пилотный эпизод, комиксы"
}

function p.e(frame)
    -- Защита от отсутствующих аргументов и глобальных утечек
    local res = frame.args[1] or ""
    local par = frame.args[2] or ""
    
    if res == "" then return "" end

    if par == 'GALLERY' then
        -- Гибкий поиск: %s* позволяет игнорировать случайные пробелы и переносы строк вокруг HTML-сущностей
        res = res:gsub('<span>%[%[([^|%]]-)%|([^%]]-)%]%]</span>%s*&nbsp;%s*%%&bull;%s*&nbsp;%s*<span>%[%[%1/Дизайн%|%2/Дизайн%]%]</span>%s*&nbsp;%s*%%&bull;%s*&nbsp;%s*<span>%[%[%1/Мерчендайз%|%2/Мерчендайз%]%]</span>%s*&nbsp;%s*%%&bull;%s*&nbsp;%s*<span>%[%[%1/Официальное творчество%|%2/Официальное творчество%]%]</span>', 
            '<span>[[%1|%2]]</span><sup> ([[%1/Официальное творчество|<i class="fa-solid fa-paint-roller"></i>]] · [[%1/Дизайн|<i class="fa-solid fa-compass-drafting"></i>]] · [[%1/Мерчендайз|<i class="fa-solid fa-bag-shopping"></i>]])</sup>')
        
        res = res:gsub('<span>%[%[([^|%]]-)%|([^%]]-)%]%]</span>%s*&nbsp;%s*%%&bull;%s*&nbsp;%s*<span>%[%[%1/Мерчендайз%|%2/Мерчендайз%]%]</span>%s*&nbsp;%s*%%&bull;%s*&nbsp;%s*<span>%[%[%1/Официальное творчество%|%2/Официальное творчество%]%]</span>', 
            '<span>[[%1|%2]]</span><sup> ([[%1/Официальное творчество|<i class="fa-solid fa-paint-roller"></i>]] · [[%1/Мерчендайз|<i class="fa-solid fa-bag-shopping"></i>]])</sup>')
        
        res = res:gsub('<span>%[%[([^|%]]-)%|([^%]]-)%]%]</span>%s*&nbsp;%s*%%&bull;%s*&nbsp;%s*<span>%[%[%1/Дизайн%|%2/Дизайн%]%]</span>%s*&nbsp;%s*%%&bull;%s*&nbsp;%s*<span>%[%[%1/Официальное творчество%|%2/Официальное творчество%]%]</span>', 
            '<span>[[%1|%2]]</span><sup> ([[%1/Официальное творчество|<i class="fa-solid fa-paint-roller"></i>]] · [[%1/Дизайн|<i class="fa-solid fa-compass-drafting"></i>]])</sup>')
        
        res = res:gsub('<span>%[%[([^|%]]-)%|([^%]]-)%]%]</span>%s*&nbsp;%s*%%&bull;%s*&nbsp;%s*<span>%[%[%1/Дизайн%|%2/Дизайн%]%]</span>%s*&nbsp;%s*%%&bull;%s*&nbsp;%s*<span>%[%[%1/Мерчендайз%|%2/Мерчендайз%]%]</span>', 
            '<span>[[%1|%2]]</span><sup> ([[%1/Дизайн|<i class="fa-solid fa-compass-drafting"></i>]] · [[%1/Мерчендайз|<i class="fa-solid fa-bag-shopping"></i>]])</sup>')
        
        res = res:gsub('<span>%[%[([^|%]]-)%|([^%]]-)%]%]</span>%s*&nbsp;%s*%%&bull;%s*&nbsp;%s*<span>%[%[%1/Дизайн%|%2/Дизайн%]%]</span>',
            '<span>[[%1|%2]]</span><sup> ([[%1/Дизайн|<i class="fa-solid fa-compass-drafting"></i>]])</sup>')
        
        res = res:gsub('<span>%[%[([^|%]]-)%|([^%]]-)%]%]</span>%s*&nbsp;%s*%%&bull;%s*&nbsp;%s*<span>%[%[%1/Официальное творчество%|%2/Официальное творчество%]%]</span>',
            '<span>[[%1|%2]]</span><sup> ([[%1/Официальное творчество|<i class="fa-solid fa-paint-roller"></i>]])</sup>')
        
        res = res:gsub('<span>%[%[([^|%]]-)%|([^%]]-)%]%]</span>%s*&nbsp;%s*%%&bull;%s*&nbsp;%s*<span>%[%[%1/Мерчендайз%|%2/Мерчендайз%]%]</span>',
            '<span>[[%1|%2]]</span><sup> ([[%1/Мерчендайз|<i class="fa-solid fa-bag-shopping"></i>]])</sup>')
    end

    if par ~= 'NOYES' then
        -- Упрощение ссылок на подстраницы: [[Page/Subpage|Page/Subpage]] -> [[Page/Subpage|Page]]
        res = res:gsub("%[%[([^|%]]-)/([^|%]]-)%|%1/%2%]%]", "[[%1/%2|%1]]") 
    end

    if par ~= 'NO' and par ~= 'GALLERY' then
        -- Упрощение ссылок с уточнениями: [[Page (disambig)|Page (disambig)]] -> [[Page (disambig)|Page]]
        -- Использование %s+ гарантирует, что пробел перед скобкой будет сохранён корректно
        res = res:gsub("%[%[(.-)%s+%(([^|%)]+)%)%|%1%s+%(%2%)%]%]", "[[%1 (%2)|%1]]")
    end

    if par == 'PERSONAS' then
        -- Единая замена ролей. Подхватывает как [[Имя|Имя]], так и просто [[Имя]]
        res = res:gsub("%[%[([^|%]]+)(|?[^%]]*)%]%]", function(name, pipe_text)
            if (pipe_text == "" or pipe_text == "|" .. name) and personas[name] then
                return string.format("[[%s]] <sup>(%s)</sup>", name, personas[name])
            end
        end)
    end
    
    return res
end

return p
