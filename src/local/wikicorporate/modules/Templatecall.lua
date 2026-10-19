local p = {}

local templates = {
    'Заголовок',
    'GameSlider',
}

function p.render(frame)
    local ret = {}
    for _, v in ipairs(templates) do
        table.insert(ret, frame:expandTemplate{ title = v })
    end
    return table.concat(ret)
end

return p
