local p = {}

local function trim(s)
    if not s then return '' end
    return (mw.ustring.gsub(tostring(s), '^%s*(.-)%s*$', '%1'))
end

local function cleanFileName(raw)
    local s = trim(raw)
    s = mw.ustring.gsub(s, '^%[%[', '')
    s = mw.ustring.gsub(s, '%]%]$', '')
    s = mw.ustring.gsub(s, '^[Ff]ile:', '')
    s = mw.ustring.gsub(s, '^[Фф]айл:', '')
    local pipe = mw.ustring.find(s, '|', 1, true)
    if pipe then
        s = trim(mw.ustring.sub(s, 1, pipe - 1))
    end
    return s
end

local function parseImages(rawImg)
    local items = {}
    local cleanRaw = trim(rawImg)
    if cleanRaw == '' then return items end

    if mw.ustring.find(cleanRaw, '<gallery', 1, true) then
        local inner = mw.ustring.match(cleanRaw, '<gallery[^>]*>([%s%S]-)</gallery>') or ''
        for line in mw.text.gsplit(inner, '\n', true) do
            local lineTrim = trim(line)
            if lineTrim ~= '' then
                local parts = mw.text.split(lineTrim, '|', true)
                local file = cleanFileName(parts[1])
                local label = trim(parts[2] or '')
                if file ~= '' then
                    table.insert(items, { file = file, label = label ~= '' and label or tostring(#items + 1) })
                end
            end
        end
        return items
    end

    local chunks = mw.text.split(cleanRaw, '[;\n]+')
    for _, chunk in ipairs(chunks) do
        local c = trim(chunk)
        if c ~= '' then
            local parts = mw.text.split(c, '|', true)
            local file = cleanFileName(parts[1])
            local label = trim(parts[2] or '')
            if file ~= '' then
                table.insert(items, { file = file, label = label ~= '' and label or tostring(#items + 1) })
            end
        end
    end
    return items
end

local function getArg(args, keys)
    if type(keys) == 'string' then
        local v = args[keys]
        return (v and trim(v) ~= '') and trim(v) or nil
    end
    if type(keys) == 'table' then
        for _, k in ipairs(keys) do
            local v = args[k]
            if v and trim(v) ~= '' then
                return trim(v)
            end
        end
    end
    return nil
end

-- Рендер медиа-блока: чередование .t-infobox__tab + .t-infobox__panel для работы чистого CSS (+)
local function renderMedia(container, args)
    local rawImg = getArg(args, { 'изображение', 'image', 'портрет', 'файл' })
    if not rawImg then return end

    local size = getArg(args, { 'размер', 'image_size', 'width' }) or '300px'
    local caption = getArg(args, { 'подпись', 'caption', 'описание_изображения' })
    local images = parseImages(rawImg)
    if #images == 0 then return end

    local mediaBox = container:tag('div'):addClass('t-infobox__media')
    if #images > 1 then
        mediaBox:addClass('has-tabs')
    end

    for _, item in ipairs(images) do
        if #images > 1 then
            mediaBox:tag('span')
                :addClass('t-infobox__tab')
                :attr('tabindex', '0')
                :wikitext(item.label)
        end

        mediaBox:tag('div')
            :addClass('t-infobox__panel')
            :attr('tabindex', '0')
            :wikitext(mw.ustring.format('[[Файл:%s|%s|class=t-infobox__img]]', item.file, size))
    end

    if caption then
        mediaBox:tag('div'):addClass('t-infobox__caption'):wikitext(caption)
    end
end

local function renderSchemaSections(box, args, schema)
    for _, sec in ipairs(schema.sections or {}) do
        local secRows = {}
        local gridItems = {}

        if sec.grid then
            for _, g in ipairs(sec.grid) do
                local val = getArg(args, g.param)
                if val then
                    table.insert(gridItems, { label = g.label, value = val })
                end
            end
        end

        for _, field in ipairs(sec.fields or {}) do
            local val = getArg(args, field.param)
            if val then
                table.insert(secRows, { label = field.label, value = val, full = field.full })
            end
        end

        if #gridItems > 0 or #secRows > 0 then
            local secWrap = box:tag('section'):addClass('t-infobox__group')
            if sec.collapsed then
                secWrap:addClass('is-collapsed')
            end

            if sec.title and sec.title ~= '' then
                secWrap:tag('div')
                    :addClass('t-infobox__section')
                    :attr('tabindex', '0')
                    :wikitext(sec.title)
            end

            local bodyWrap = secWrap:tag('div'):addClass('t-infobox__body'):tag('div'):addClass('t-infobox__body-inner')

            if #gridItems > 0 then
                local gridEl = bodyWrap:tag('div'):addClass('t-infobox__grid')
                for _, g in ipairs(gridItems) do
                    local cell = gridEl:tag('div'):addClass('t-infobox__cell')
                    if g.label and g.label ~= '' then
                        cell:tag('div'):addClass('t-infobox__cell-label'):wikitext(g.label)
                    end
                    cell:tag('div'):addClass('t-infobox__cell-value'):wikitext(g.value)
                end
            end

            for _, r in ipairs(secRows) do
                local rowEl = bodyWrap:tag('div'):addClass('t-infobox__row')
                if r.full or not r.label or r.label == '' then
                    rowEl:addClass('t-infobox__row--full')
                    rowEl:tag('div'):addClass('t-infobox__value'):wikitext(r.value)
                else
                    rowEl:tag('div'):addClass('t-infobox__label'):wikitext(r.label)
                    rowEl:tag('div'):addClass('t-infobox__value'):wikitext(r.value)
                end
            end
        end
    end
end

local function renderDirectRows(box, args)
    local currentBody = box

    for i = 1, 60 do
        local secTitle = getArg(args, { 'секция' .. i, 'section' .. i, 'заголовок' .. i })
        if secTitle then
            local secWrap = box:tag('section'):addClass('t-infobox__group')
            if getArg(args, { 'свёрнуто' .. i, 'collapsed' .. i }) then
                secWrap:addClass('is-collapsed')
            end
            secWrap:tag('div')
                :addClass('t-infobox__section')
                :attr('tabindex', '0')
                :wikitext(secTitle)
            currentBody = secWrap:tag('div'):addClass('t-infobox__body'):tag('div'):addClass('t-infobox__body-inner')
        end

        local val = getArg(args, { 'данные' .. i, 'data' .. i, 'значение' .. i })
        if val then
            local lbl = getArg(args, { 'метка' .. i, 'label' .. i })
            local rowEl = currentBody:tag('div'):addClass('t-infobox__row')
            if lbl then
                rowEl:tag('div'):addClass('t-infobox__label'):wikitext(lbl)
                rowEl:tag('div'):addClass('t-infobox__value'):wikitext(val)
            else
                rowEl:addClass('t-infobox__row--full')
                rowEl:tag('div'):addClass('t-infobox__value'):wikitext(val)
            end
        end
    end
end

function p.main(frame)
    local parent = frame:getParent()
    local args = {}

    if parent then
        for k, v in pairs(parent.args) do args[k] = v end
    end
    for k, v in pairs(frame.args) do args[k] = v end

    local box = mw.html.create('aside'):addClass('t-infobox')

    local themeName = getArg(args, { 'тема', 'theme', 'тип' })
    if themeName then
        box:attr('data-ib-theme', mw.ustring.lower(themeName))
    end

    local customBg = getArg(args, { 'цвет', 'bg', 'color-p' })
    local customAccent = getArg(args, { 'акцент', 'border', 'color-s' })
    local styles = {}
    if customBg then table.insert(styles, '--ib-p:' .. customBg) end
    if customAccent then table.insert(styles, '--ib-s:' .. customAccent) end
    if #styles > 0 then
        box:attr('style', table.concat(styles, ';'))
    end

    local title = getArg(args, { 'заголовок', 'название', 'имя', 'title', 'name' }) or mw.title.getCurrentTitle().text
    box:tag('div'):addClass('t-infobox__title'):wikitext(title)

    local subtitle = getArg(args, { 'подзаголовок', 'оригинал', 'subtitle' })
    if subtitle then
        box:tag('div'):addClass('t-infobox__subtitle'):wikitext(subtitle)
    end

    renderMedia(box, args)

    local schemaName = getArg(args, { 'схема', 'schema' })
    local schemaData = nil
    if schemaName then
        local ok, loaded = pcall(mw.loadJsonData, 'MediaWiki:Custom-Infoboxes.json')
        if ok and type(loaded) == 'table' then
            schemaData = loaded[schemaName]
        end
    end

    if schemaData then
        renderSchemaSections(box, args, schemaData)
    else
        renderDirectRows(box, args)
    end

    return tostring(box)
end

return p
