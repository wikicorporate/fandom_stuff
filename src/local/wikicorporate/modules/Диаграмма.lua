local p = {}

function split (inputstr, sep)
    if sep == nil then
        sep = "%s"
    end
    local t={}
    for str in string.gmatch(inputstr, "([^"..sep.."]+)") do
        table.insert(t, str)
    end
    return t
end

function tablelength(T)
  local count = 0
  for _ in pairs(T) do count = count + 1 end
  return count
end

function prepareValue(ARGS)
	local preparedString = string.gsub(ARGS,"%%","");
	preparedString = string.gsub(preparedString,",",".")
	preparedString = string.gsub(preparedString," ","")
	return tonumber(preparedString)
end

function generateBack(Colors, Nums)
	Colorsarray = split(Colors, '.')
	Numsarray = split(Nums, '.')
	backcolor = ""
	for i, val in ipairs(Numsarray) do
		if prepareValue(val) >= 50 or i == tablelength(Numsarray) then backcolor = Colorsarray[i]; break end
	end
	return backcolor
end

function GeneratePie(Colors, Nums)
	Colorsarray = split(Colors, '.')
	Numsarray = split(Nums, '.')
	resstring = '<div class="diagram-main"><div class="pie-background" style="background-color: ' ..generateBack(Colors, Nums)..'"></div><div style="transform: rotate(270deg)" class="pie-piece"><div class="pie" style="background-color: '.. Colorsarray[1] ..'; transform: rotate('.. tostring(Numsarray[1]*-3.6).."deg" ..')"></div></div>'
	for i, val in ipairs(Colorsarray) do
		if i > 1 then
			rot1 = ""
			j = 1
			rot1num = 0
			while j < i do
				rot1num = rot1num + prepareValue(Numsarray[j])
				j = j + 1
			end
			rot1 =  tostring(270-(3.6*(rot1num))).."deg"
			rot2 =  tostring(prepareValue(Numsarray[i])*-3.6).."deg"
			resstring = resstring..'<div style="transform: rotate('.. rot1 ..')" class="pie-piece"><div class="pie" style="background-color: '.. val ..'; transform: rotate(' .. rot2 ..')"></div></div>'
		end
	end
	return resstring..'</div>'
end
-- Функция для вызова через шаблон ({{#invoke:}})
function p.e(frame) -- 
	local Colors = frame.args[1]
	local Nums = frame.args[2]
	return GeneratePie(Colors,Nums)
end

return p
