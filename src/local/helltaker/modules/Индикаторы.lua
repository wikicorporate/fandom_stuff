local p = {}

-- Статистика (Подсчёт файлов)
local function ruslangadopt(num, word1, word2, word3)
    local count = num % 100
    if count >= 5 and count <= 20 then 
        return word3 
    end
    count = count % 10
    if count == 1 then
        return word1
    elseif count >= 2 and count <= 4 then
        return word2
    else
        return word3
    end
end

local function compile_stats()
    local title = mw.title.getCurrentTitle()
    local content = title:getContent() or ""
    
    local counts = { image = 0, video = 0, audio = 0, animation = 0, file = 0 }

    for ext in content:gmatch("%.([a-zA-Z0-9]+)") do
        ext = ext:lower()
        if ext == "png" or ext == "jpg" or ext == "jpeg" or ext == "webp" then
            counts.image = counts.image + 1
        elseif ext == "ogg" or ext == "mp3" or ext == "flac" or ext == "wav" then
            counts.audio = counts.audio + 1
        elseif ext == "gif" then
            counts.animation = counts.animation + 1
        elseif ext == "woff" or ext == "woff2" or ext == "ttf" then
            counts.file = counts.file + 1
        end
    end

    for galleryContent in content:gmatch("{{Галерея|(.-)}}") do
        local cleanGallery = galleryContent:gsub("|%s*Open%s*=%s*True", "")
        for line in cleanGallery:gmatch("[^\r\n]+") do
            local cleanLine = mw.text.trim(line:gsub("|.*", ""))
            if cleanLine ~= "" and not cleanLine:match("%.") then
                counts.video = counts.video + 1
            end
        end
    end

    for videoParam in content:gmatch("|%s*Видео%s*=%s*([^\n\r]+)") do
        if mw.text.trim(videoParam) ~= "" then
            counts.video = counts.video + 1
        end
    end

    local result = {}
    if counts.image > 0 then 
        table.insert(result, string.format('<div class="mw-indicator__icon mw-indicator__icon--image"><div class="mw-indicator__icon-tooltip">Данная страница содержит \'\'\'%d\'\'\' %s</div><i class="fa-solid fa-image"></i>%d</div>', counts.image, ruslangadopt(counts.image, "изображение.", "изображения.", "изображений."), counts.image)) 
    end
    if counts.video > 0 then 
        table.insert(result, string.format('<div class="mw-indicator__icon mw-indicator__icon--video"><div class="mw-indicator__icon-tooltip">Данная страница содержит \'\'\'%d\'\'\' %s</div><i class="fa-solid fa-play"></i>%d</div>', counts.video, ruslangadopt(counts.video, "видео.", "видео.", "видео."), counts.video)) 
    end
    if counts.audio > 0 then 
        table.insert(result, string.format('<div class="mw-indicator__icon mw-indicator__icon--audio"><div class="mw-indicator__icon-tooltip">Данная страница содержит \'\'\'%d\'\'\' %s</div><i class="fa-solid fa-headphones"></i>%d</div>', counts.audio, ruslangadopt(counts.audio, "аудиофайл.", "аудиофайла.", "аудиофайлов."), counts.audio)) 
    end
    if counts.animation > 0 then 
        table.insert(result, string.format('<div class="mw-indicator__icon mw-indicator__icon--animation"><div class="mw-indicator__icon-tooltip">Данная страница содержит \'\'\'%d\'\'\' %s</div><i class="fa-solid fa-rotate"></i>%d</div>', counts.animation, ruslangadopt(counts.animation, "анимацию.", "анимации.", "анимаций."), counts.animation)) 
    end
    if counts.file > 0 then 
        table.insert(result, string.format('<div class="mw-indicator__icon mw-indicator__icon--file"><div class="mw-indicator__icon-tooltip">Данная страница содержит \'\'\'%d\'\'\' %s</div><i class="fa-solid fa-folder"></i>%d</div>', counts.file, ruslangadopt(counts.file, "прочий файл.", "прочих файла.", "прочих файлов."), counts.file)) 
    end

    return table.concat(result)
end

-- Индикаторы и плашки
local function navigator_special_lux_function(text, text2)
    return {
        "<i class='fa-solid fa-compass'></i>Навигатор", 
        "mw-indicator__nameplate--navigation", 
        "Эта статья " .. tostring(text or "") .. ". Также посмотрите " .. tostring(text2 or "")
    }
end

local Nameplate = {
    ["Незавершённая статья"] = {"<i class='fa-solid fa-screwdriver-wrench'></i> Незавершённая статья", "mw-indicator__nameplate--unfinished", "Это [[:Категория:Незавершённые статьи|незавершённая статья]].</span> Она содержит неполную информацию. Вы можете помочь '''{{SITENAME}}''', [{{SERVER}}{{localurl:{{NAMESPACE}}:{{PAGENAME}}|action=edit}} дополнив её].</span>[[Категория:Незавершённые статьи]]"},
    ["Неоднозначность"] = {"<i class='fa-solid fa-question'></i>Неоднозначность", "mw-indicator__nameplate--disambig", "'''Это список значений {{PAGENAME}}'''. Здесь представлен список ссылок на страницы с одинаковым названием. Пожалуйста, перейдите на нужную вам страницу по одной из следующих ссылок или воспользуйтесь [[Служебная:Search|поиском]]</span>, если вам необходима страница, которой нет в списке. Если [[Служебная:Whatlinkshere/{{FULLPAGENAME}}|другая ссылка]]</span> ведёт сюда, вам следует вернуться назад.[[Категория:Неоднозначность]]"},
    ["Спойлеры"] = {"<i class='fa-solid fa-triangle-exclamation'></i>Спойлеры", "mw-indicator__nameplate--spoiler", "Данная статья содержит информацию из недавно вышедшего эпизода. Если вы не смотрели его и не хотите испортить впечатления от просмотра, то настоятельно рекомендуем ''покинуть страницу''. [[Категория:Спойлеры]]"},
}

local Icon = {
    ["А"] = {"[[File:Bot.png]]", "class1", "Тултип"}
}

local function get_nameplate(key, frame)
    if key == "Навигатор" then
        return navigator_special_lux_function(frame.args[3], frame.args[4])
    end
    return Nameplate[key] or {'<i class="fa-solid fa-xmark"></i>', '', 'Неизвестная плашка!'}
end

local function get_icon(key)
    return Icon[key] or {'<i class="fa-solid fa-xmark"></i>', '', 'Неизвестная иконка!'}
end

-- Основная функция
function p.e(frame)
    local str_nameplates = frame.args[1]
    local str_icons = frame.args[2]
    local html = {}
    
    if str_nameplates and str_nameplates ~= "" then
        table.insert(html, '<div class="mw-indicator__nameplates">')
        local parts = mw.text.split(str_nameplates, "%.")
        for _, value in ipairs(parts) do
            local np = get_nameplate(mw.text.trim(value), frame)
            table.insert(html, string.format('<div class="mw-indicator__nameplate %s"><div class="mw-indicator__nameplate-tooltip">%s</div>%s</div>', np[2], frame:preprocess(np[3]), np[1]))
        end
        table.insert(html, '</div>')
    end

    local icons_html = {}
    if str_icons and str_icons ~= "" then
        local parts = mw.text.split(str_icons, "%.")
        for _, value in ipairs(parts) do
            local ic = get_icon(mw.text.trim(value))
            table.insert(icons_html, string.format('<div class="mw-indicator__icon %s"><div class="mw-indicator__icon-tooltip">%s</div>%s</div>', ic[2], frame:preprocess(ic[3]), ic[1]))
        end
    end
    
    table.insert(icons_html, compile_stats())

    if #icons_html > 0 then
        table.insert(html, string.format('<div class="mw-indicator__icons">%s</div>', table.concat(icons_html)))
    end

    return table.concat(html)
end

return p
