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
        },
        bot = {
            icon = "fa-solid fa-robot",
            tooltip = "Бот",
            class = "custom-tag-bot"
        }
    },

    users = {
        ["Swit4er"] = {
            hideDefault = true,
            tags = {"bureaucrat", "admin"},
            mainTag = "bureaucrat"
        },
        ["Имя_Участника_2"] = {
            hideDefault = false,
            tags = {"bot"}
        }
    }
}

function p.toJSON()
    return mw.text.jsonEncode(config)
end

return p
