local p = {}

local medals = mw.loadData('Module:MedalList')
local users = mw.loadData('Module:UsersMedals')

local function generatepage(medalstable, userstable)
    local out = {}

    for key, value in pairs(userstable) do
        local username, medal_ids, desc, image

        -- Поддержка обоих форматов записи в Module:UsersMedals:
        -- 1) ["Ник"] = { {1, 3}, "Описание", "Картинка" }
        -- 2) { "Ник", {1, 3}, "Описание", "Картинка" }
        if type(key) == "string" then
            username = key
            medal_ids = value[1]
            desc = value[2] or ""
            image = value[3] or ""
        else
            username = value[1] or ""
            medal_ids = value[2]
            desc = value[3] or ""
            image = value[4] or ""
        end

        table.insert(
            out,
            string.format(
                '<div class="userboard__user">%s\n== %s ==\n\n%s</div><div class="userboard__medals">',
                image,
                username,
                desc
            )
        )

        if medal_ids then
            for _, medal_idx in ipairs(medal_ids) do
                local medal = medalstable[medal_idx]
                if medal then
                    table.insert(
                        out,
                        string.format(
                            '<div class="userboard__medal">%s<div class="userboard__medal-tooltip">\n=== %s ===\n%s</div></div>\n\n',
                            medal[2] or "",
                            medal[1] or "",
                            medal[3] or ""
                        )
                    )
                end
            end
        end

        table.insert(out, '</div>\n')
    end

    return table.concat(out)
end

function p.e()
    return generatepage(medals, users)
end

return p
