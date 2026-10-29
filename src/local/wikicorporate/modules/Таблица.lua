local p = {}

local function trim(s)
    if not s then return '' end
    return (mw.ustring.gsub(tostring(s), '^%s*(.-)%s*$', '%1'))
end

-- Разбор строк вида: "Ячейка 1 || Ячейка 2 || Ячейка 3"
local function splitCells(rowText)
    local cells = {}
    for _, cell in ipairs(mw.text.split(rowText, '||', true)) do
        table.insert(cells, trim(cell))
    end
    return cells
end

function p.main(frame)
    local parent = frame:getParent()
    local args = {}
    if parent then
        for k, v in pairs(parent.args) do args[k] = v end
    end
    for k, v in pairs(frame.args) do args[k] = v end

    local mode = mw.ustring.lower(trim(args['режим'] or args['mode'] or 'cards'))
    local caption = trim(args['заголовок'] or args['caption'] or '')
    local rawHeaders = trim(args['шапка'] or args['headers'] or '')

    local headers = {}
    if rawHeaders ~= '' then
        headers = splitCells(rawHeaders)
    end

    local wrap = mw.html.create('div'):addClass('t-table-wrap')
    if mode == 'scroll' or mode == 'скролл' then
        wrap:addClass('t-table-wrap--scroll')
    else
        wrap:addClass('t-table-wrap--cards')
    end

    local tbl = wrap:tag('table'):addClass('t-table')
    if args['сортировка'] or args['sortable'] then
        tbl:addClass('sortable')
    end

    if caption ~= '' then
        tbl:tag('caption'):addClass('t-table__caption'):wikitext(caption)
    end

    if #headers > 0 then
        local thead = tbl:tag('thead'):tag('tr')
        for _, h in ipairs(headers) do
            thead:tag('th'):wikitext(h)
        end
    end

    local tbody = tbl:tag('tbody')
    for i = 1, 200 do
        local rowRaw = args[i] or args['строка' .. i] or args['row' .. i]
        if rowRaw and trim(rowRaw) ~= '' then
            local tr = tbody:tag('tr')
            local cells = splitCells(rowRaw)
            for colIdx, cellVal in ipairs(cells) do
                local td = tr:tag('td')
                if headers[colIdx] and headers[colIdx] ~= '' then
                    -- Очищаем вики-разметку из заголовка для чистого текста в data-label
                    local cleanLabel = mw.ustring.gsub(headers[colIdx], '%[%[([^|%]]+|)?([^%]]+)%]%]', '%2')
                    cleanLabel = mw.ustring.gsub(cleanLabel, '<[^>]+>', '')
                    td:attr('data-label', trim(cleanLabel))
                end
                td:wikitext(cellVal)
            end
        end
    end

    return tostring(wrap)
end

return p
