local p = {}

local function trim(s)
    if not s then return '' end
    return (mw.ustring.gsub(tostring(s), '^%s*(.-)%s*$', '%1'))
end

function p.main(frame)
    local parent = frame:getParent()
    local args = {}
    if parent then
        for k, v in pairs(parent.args) do args[k] = v end
    end
    for k, v in pairs(frame.args) do args[k] = v end

    local rawFile = trim(args[1] or args['файл'] or args['file'] or '')
    if rawFile == '' then return '' end

    rawFile = mw.ustring.gsub(rawFile, '^[Ff]ile:', '')
    rawFile = mw.ustring.gsub(rawFile, '^[Фф]айл:', '')

    local title = trim(args[2] or args['название'] or args['подпись'] or args['title'] or '')
    local fx = trim(args['эффект'] or args['фильтр'] or args['fx'] or '')
    local inline = trim(args['инлайн'] or args['inline'] or '')

    local wrap = mw.html.create(inline ~= '' and 'span' or 'div')
        :addClass('t-audio')
        :attr('data-file', rawFile)

    if title ~= '' then
        wrap:attr('data-title', title)
    end
    if fx ~= '' then
        wrap:attr('data-fx', mw.ustring.lower(fx))
    end
    if inline ~= '' then
        wrap:addClass('t-audio--inline')
    end

    -- Нативный фолбэк внутри контейнера (даёт скрипту прямую ссылку на поток без лишних API-запросов)
    wrap:wikitext(mw.ustring.format('[[Файл:%s]]', rawFile))

    return tostring(wrap)
end

return p
