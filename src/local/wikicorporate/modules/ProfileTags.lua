local p = {}
function split (inputstr, sep)
        if sep == nil then
                sep = "%s"
        end
        local t={}
        for str in mw.ustring.gmatch(inputstr, "([^"..sep.."]+)") do
                table.insert(t, str)
        end
        return t
end
tags = {
	 ["Основатель"] = {"Основатель", "<i class='fa-solid fa-web-awesome'></i>"},
     ["Бюрократ"] = {"Бюрократ","<i class='fa-solid fa-code'></i>"},
     ["Администратор"] = {"Администратор","<i class='fa-solid fa-gear'></i>"},
     ["Модератор контента"] = {"Модератор контента","<i class='fa-solid fa-gear'></i>"},
     ["Модератор сообщества"] = {"Модератор сообщества","<i class='fa-solid fa-gear'></i>"},
     ["Администратор Discord"] = {"Администратор Discord","<i class='fa-solid discord'></i>"},
     ["Модератор Discord"] = {"Модератор Discord","<i class='fa-solid fa-discord'></i>"},
     ["Откатчик"] = {"Откатчик","<i class='fa-solid fa-clock-rotate-left'></i>"},
     ["Бот"] = {"Бот","<i class='fa-solid fa-robot'></i>"},
}
userdb = {
        ["Swit4er"] = "Основатель!Бюрократ!Администратор",
        ["Hwjeei"] = "Администратор"
}


function p.profiletags(frame)
    local nomi = frame.args[1]
	local res = ""
    for i,value in pairs(split(userdb[nomi],'!')) do
    	res =  res..'<div class = "user-tag">'..tags[value][2]..'<div class = "user-tag__tooltip">'..tags[value][1]..'</div></div>'
    end
    return '<div class = "user-tags">'..res..'</div>'
end

return p
