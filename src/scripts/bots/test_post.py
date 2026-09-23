import os
import sys
import json
import requests
import mwclient

DOMAIN = "hazbinhotel.fandom.com"
PATH = "/ru/"
TEST_USER = os.environ.get("TEST_USER", "Swit4er")

user = os.environ.get("MAIN_ACCOUNT_USER")
password = os.environ.get("MAIN_ACCOUNT_PASSWORD")

if not user or not password:
    print("[-] Ошибка: Переменные MAIN_ACCOUNT_USER или MAIN_ACCOUNT_PASSWORD не заданы.")
    sys.exit(1)

site = mwclient.Site(DOMAIN, path=PATH)

try:
    site.login(user, password)
    print(f"[+] Авторизация успешна под аккаунтом: {user}")
except Exception as e:
    print(f"[-] Ошибка входа в аккаунт: {e}")
    sys.exit(1)

# 1. Получаем User ID целевого пользователя
user_query = site.api("query", list="users", ususers=TEST_USER)
users_data = user_query.get("query", {}).get("users", [])

if not users_data or "userid" not in users_data[0]:
    print(f"[-] Не удалось найти пользователя {TEST_USER} или его ID.")
    sys.exit(1)

user_id = users_data[0]["userid"]
print(f"[*] Найден ID пользователя {TEST_USER}: {user_id}")

# 2. Получаем CSRF-токен
token_res = site.api("query", meta="tokens")
csrf_token = token_res.get("query", {}).get("tokens", {}).get("csrftoken")

# 3. Формируем тело сообщения
msg_title = "Тестовое приветствие"
msg_text = "Проверка работы автоматического скрипта приветствий."

json_model = {
    "type": "doc",
    "content": [
        {
            "type": "paragraph",
            "content": [
                {
                    "type": "text",
                    "text": msg_text
                }
            ]
        }
    ]
}

attachments = {
    "contentImages": [],
    "openGraphs": [],
    "atMentions": []
}

# 4. Отправляем запрос через точный UCP-контроллер
url = f"https://{DOMAIN}{PATH}wikia.php"
params = {
    "controller": r"Fandom\MessageWall\MessageWall",
    "method": "createThread",
    "format": "json"
}

data = {
    "token": csrf_token,
    "wallOwnerId": user_id,
    "title": msg_title,
    "rawContent": msg_text,
    "jsonModel": json.dumps(json_model, ensure_ascii=False),
    "attachments": json.dumps(attachments)
}

headers = {
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest"
}

resp = site.connection.post(url, params=params, data=data, headers=headers)
print(f"[*] Статус отправки на стену: {resp.status_code}")
print(f"[*] Ответ сервера: {resp.text}")
