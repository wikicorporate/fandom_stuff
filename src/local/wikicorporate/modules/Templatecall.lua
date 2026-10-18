local templates = {
	'Заголовок',
	'GameSlider',
}
local p = {}

function p.render(frame)
    ret = ''
    for i,v in ipairs(templates) do
    	ret = ret .. frame:expandTemplate{title = v}
    end
    return ret
end

return p
