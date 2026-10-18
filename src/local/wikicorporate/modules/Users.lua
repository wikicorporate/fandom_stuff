local p = {}

local config = {
    tags = {
        bureaucrat = { 
            icon = "fa-solid fa-code", 
            tooltip = "Бюрократ", 
            class = "custom-tag-bureaucrat"
        },
        admin = { 
            icon = "fa-solid fa-gear", 
            tooltip = "Администратор", 
            class = "custom-tag-admin" 
        }
    },
    
    users = {
        ["Swit4er"] = { 
            hideDefault = true, -- true: скрыть стандартные теги Фэндома
            tags = {"bureaucrat", "admin"}, -- Указываем ID тегов из базы выше
            mainTag = "bureaucrat" -- Выведется только данный тег (в комментариях / на стене / в таблице лидеров)
        },
        ["Имя_Участника_2"] = { 
            hideDefault = false, -- false: оставить стандартные теги (добавятся к вашим)
            tags = {"bot"} 
        },
    }
}

function p.toJSON()
    return mw.text.jsonEncode(config)
end

return p
