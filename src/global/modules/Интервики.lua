local p = {}

local JSON_SOURCES = {
    'MediaWiki:Custom-Интервики.json',
    'Интервики.json',
    'Interwiki.json'
}

local function load_interwiki_db()
    for _, source in ipairs(JSON_SOURCES) do
        local ok, data = pcall(mw.loadJsonData, source)
        if ok and type(data) == 'table' then
            return data
        end
    end
    return nil
end

function p.e(frame)
    local args = frame.args
    local page = args[1]
    if not page or mw.text.trim(page) == '' then
        local parent = frame:getParent()
        if parent and parent.args and parent.args[1] then
            page = parent.args[1]
        else
            page = mw.title.getCurrentTitle().text
        end
    end

    page = mw.text.trim(page or '')
    if page == '' then
        return ''
    end

    local db = load_interwiki_db()
    if not db then
        return ''
    end

    local links = db[page]
    if type(links) ~= 'table' then
        return ''
    end

    -- Сортируем языковые префиксы по алфавиту для стабильного вывода
    local langs = {}
    for lang, target in pairs(links) do
        if type(lang) == 'string' and type(target) == 'string' and mw.text.trim(target) ~= '' then
            table.insert(langs, lang)
        end
    end
    table.sort(langs)

    local res = {}
    for _, lang in ipairs(langs) do
        table.insert(res, string.format('[[%s:%s]]', lang, mw.text.trim(links[lang])))
    end

    return table.concat(res, '\n')
end

return p
