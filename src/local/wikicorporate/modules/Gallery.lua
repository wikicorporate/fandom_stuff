local p = {}

function p.e(frame)
    local input = frame.args[1] or ""
    return frame:preprocess('<div class="mw-collapsible mw-collapsed mw-made-collapsible t-gallery"><gallery>\n' .. input:gsub('\\', '|') .. '</gallery></div>')
end

function p.e2(frame)
    local args = frame:getParent().args
    if not args[1] and frame.args[1] then
        args = frame.args
    end

    -- Собираем безымянные аргументы в единую строку
    local raw_parts = {}
    local max_idx = 0
    for k, _ in pairs(args) do
        if type(k) == "number" and k > max_idx then
            max_idx = k
        end
    end

    for i = 1, max_idx do
        if args[i] then
            table.insert(raw_parts, args[i])
        end
    end

    local raw_str = table.concat(raw_parts, "|")

    -- Глобальный размер через параметр шаблона
    local sizeforall = args['размер'] or args['size'] or "185px"
    
    -- Легаси: старый формат 20pxALL для обратной совместимости
    local global_match = raw_str:match("|(%d+px)ALL")
    if global_match then
        sizeforall = global_match
        raw_str = raw_str:gsub("|%d+pxALL", "")
    end

    local html = {}
    local lines = mw.text.split(raw_str, "\n")

    for _, line in ipairs(lines) do
        line = mw.text.trim(line)
        if line ~= "" and line ~= "|" then
            local parts = mw.text.split(line, "|")
            local filename = mw.text.trim(parts[1] or "")
            
            if filename ~= "" then
                local size = sizeforall
                local link = ""
                local alt = ""
                local caption = ""

                -- Разбираем параметры картинки
                for j = 2, #parts do
                    local part = mw.text.trim(parts[j])
                    
                    if part:match("^%d+px$") then
                        size = part
                    elseif part:match("LINK$") then
                        -- Легаси: старый формат ...LINK
                        link = part:gsub("LINK$", "")
                    else
                        -- Ищем двоеточие для новых форматов (link:Статья, alt:Текст)
                        local prefix_end = part:find(":")
                        local is_special = false
                        
                        if prefix_end then
                            local prefix = mw.ustring.lower(mw.text.trim(part:sub(1, prefix_end - 1)))
                            local val = mw.text.trim(part:sub(prefix_end + 1))
                            
                            if prefix == "link" or prefix == "ссылка" then
                                link = val
                                is_special = true
                            elseif prefix == "alt" or prefix == "альт" then
                                alt = val
                                is_special = true
                            end
                        end
                        
                        -- Если это не спец. параметр, значит это обычная подпись к картинке
                        if not is_special and part ~= "" then
                            caption = part
                        end
                    end
                end

                -- Сборка HTML
                table.insert(html, '<div class="t-gallery__item">')
                
                local file_link = "[[File:" .. filename .. "|" .. size
                if link ~= "" then file_link = file_link .. "|link=" .. link end
                if alt ~= "" then file_link = file_link .. "|alt=" .. alt end
                file_link = file_link .. "]]"
                
                table.insert(html, file_link)

                if caption ~= "" then
                    table.insert(html, '<div class="t-gallery__title">' .. caption .. '</div>')
                end
                
                table.insert(html, '</div>')
            end
        end
    end

    return table.concat(html)
end

return p
