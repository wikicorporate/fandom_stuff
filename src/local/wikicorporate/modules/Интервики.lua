local p = {}
local db = mw.loadJsonData('Interwiki.json')

function p.e(frame)
	page = frame.args[1]
	res = ''
	for i,v in pairs(db[page]) do
		res = res ..'\n\n[['..i..':'..v..']]'
	end
	return res
end

return p
