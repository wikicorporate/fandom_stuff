local p = {}

local medals = mw.loadData('Module:MedalList')
local users = mw.loadData('Module:UsersMedals')

function GetUserMedalsMassive(userid, medalstable, userstable)
	massive = {}
	i = 1
	for _,value in ipairs(userstable[userid][2]) do
		massive[i] = value
		i = i + 1
	end
	return massive
end

function getdesc(userid, userstable) return userstable[userid][3] end
function getimage(userid, userstable) return userstable[userid][4] end

function generatepage(medalstable, userstable)
	stra = ""
	for _,value in ipairs(userstable) do
		stra = stra.."<div class=userboard__user>"..getimage(_,userstable).."\n== "..value[1].." ==\n\n"..getdesc(_,userstable).."</div>".."<div class=userboard__medals>"
		for __,value2 in pairs(GetUserMedalsMassive(_, medalstable, userstable)) do
			stra = stra.."<div class=userboard__medal>"..medalstable[value2][2].."<div class=userboard__medal-tooltip> \n=== "..medalstable[value2][1].." === \n"..medalstable[value2][3].."</div></div>".."\n\n"
		end
		stra = stra.."</div>".."\n"
	end
	return stra
end

function p.e(frame)
	return generatepage(medals, users)
end

return p
