local p = {}

function count(base, pattern)
    return select(2, string.gsub(base, pattern, ""))
end

function parser(args)
	if count(args, '* ') > 4 then return true else return false end
end

function p.e(frame)
	res = ""
	if parser(frame.args[1]) == true then 
		res = '<div class="mw-collapsible mw-collapsed">\n' .. frame.args[1] .. '</div>'
	else 
		res =  frame.args[1]
	end
	return res
end

return p
