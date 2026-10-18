local p = {}

function p.toJSON(frame)
    local dict = {
        ["Recent Images"] = "Новые изображения",
        ["Message History"] = "История сообщения",
        ["Comment History"] = "История комментария",
        ["Reply History"] = "История ответа",
        ["Map Reports"] = "Ошибки",
        ["Show community navigation"] = "Показать навигацию сообщества",
        ["Hide community navigation"] = "Скрыть навигацию сообщества"
    }
    
    return mw.text.jsonEncode(dict)
end

return p
