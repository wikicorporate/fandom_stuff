local p = {}

-- Вспомогательная функция для очистки аргументов от мусора и пустых строк
local function clean_arg(arg)
    if not arg then return nil end
    arg = mw.text.trim(arg)
    if arg == "" then return nil end
    return arg
end

-- Генерация закрытого тега <ref name="..." group="..."/>
function p.main2(frame)
    local args = frame:getParent().args
    if not args[1] and frame.args[1] then args = frame.args end

    local name = clean_arg(args[1])
    local group = clean_arg(args[2])

    if not name then return "" end

    local ref_args = { name = name }
    local suffix = ""

    if group then
        ref_args.group = group
    else
        -- Сохраняем оригинальную категорию
        suffix = "[[Category:OldFormatte]]"
    end

    -- Нативная и быстрая генерация тега (результат: <ref name="X" group="Y" />)
    return frame:extensionTag('ref', '', ref_args) .. suffix
end

-- Генерация сноски с текстом и inline-спаном
function p.main(frame)
    local args = frame:getParent().args
    if not args[1] and frame.args[1] then args = frame.args end

    local text = clean_arg(args[1])
    if not text then return "" end

    local name = clean_arg(args[2])
    local group = clean_arg(args[3])

    -- Динамически собираем только те атрибуты, которые реально переданы
    local ref_args = {}
    if name then ref_args.name = name end
    if group then ref_args.group = group end

    -- Генерируем саму сноску: <ref name="..." group="...">текст</ref>
    local ref_tag = frame:extensionTag('ref', text, ref_args)

    -- Парсер MediaWiki сам обработает внутреннюю вики-разметку, preprocess здесь не нужен
    return string.format(
        '<span class="t-reference"><span class="reference-text">%s</span>%s</span>',
        text,
        ref_tag
    )
end

return p
