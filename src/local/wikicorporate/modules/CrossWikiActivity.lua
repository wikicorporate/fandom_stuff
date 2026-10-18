local p = {}

local config = {
    settings = {
        limit = 4000,
        days = 365,
        showBots = true,
        showMinor = true,
        autoRefresh = 60
    },
    wikis = {
        "ru.wikicorporate.fandom.com",
        "ru.hazbinhotel.fandom.com",
        "ru.zoophobia.fandom.com",
        "ru.returnal.fandom.com",
        "ru.helltaker.fandom.com",
        "ru.oneshot.fandom.com"
    }
}

function p.toJSON()
    return mw.text.jsonEncode(config)
end

return p
