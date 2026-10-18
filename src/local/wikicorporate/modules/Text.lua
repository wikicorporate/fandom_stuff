local p = {}
local bold = "<span class='text--bold'>"
local main = "<span class='text--main'>"
local yellow = "<span class='text--response'>"
local red = "<span class='text--danger'>"
local orange = "<span class='text--message'>"

function p.e(frame)
	text = frame.args[1]
	text = texta:gsub("<n0>", bold):gsub("<n1>", main):gsub("<n2>", yellow):gsub("<n3>", red):gsub("<n4>", orange):gsub("</>", "</span>")
	return text
end

return p
