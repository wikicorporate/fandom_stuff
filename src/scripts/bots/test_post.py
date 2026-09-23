import os
import sys
import json
import requests

DOMAIN = "hazbinhotel.fandom.com"
PATH = "/ru/"
TEST_USER = os.environ.get("TEST_USER", "Swit4er")

user = os.environ.get("MAIN_ACCOUNT_USER")
password = os.environ.get("MAIN_ACCOUNT_PASSWORD")

if not user or not password:
    print("[-] Ошибка: Переменные MAIN_ACCOUNT_USER или MAIN_ACCOUNT_PASSWORD не заданы.")
    sys.exit(1)

session = requests.Session()

# 1. Авторизация через центральный сервис Fandom Helios
print(f"[*] Авторизация через Helios под аккаунтом: {user}...")
auth_url = "https://services.fandom.com/auth/token"
auth_data = {
    "username": user,
    "password": password
}
auth_headers = {
    "Content-Type": "application/x-www-form-urlencoded"
}

auth_resp = session.post(auth_url, data=auth_data, headers=auth_headers)
if auth_resp.status_code != 200:
    print(f"[-] Ошибка авторизации Helios ({auth_resp.status_code}): {auth_resp.text}")
    sys.exit(1)

auth_json = auth_resp.json()
access_token = auth_json.get("access_token")
if not access_token:
    print("[-] Токен доступа не получен из ответа Helios.")
    sys.exit(1)

# Устанавливаем cookie access_token для домена fandom.com
session.cookies.set("access_token", access_token, domain=".fandom.com")
print("[+] Успешная авторизация в Helios, сессионный токен установлен.")

# 2. Получение User ID целевого пользователя и CSRF-токена через api.php
api_url = f"https://{DOMAIN}{PATH}api.php"

# Поиск ID пользователя
u_params = {
    "action": "query",
    "list": "users",
    "ususers": TEST_USER,
    "format": "json"
}
u_resp = session.get(api_url, params=u_params).json()
users_data = u_resp.get("query", {}).get("users", [])
if not users_data or "userid" not in users_data[0]:
    print(f"[-] Не удалось найти пользователя {TEST_USER} или его ID.")
    sys.exit(1)

user_id = users_data[0]["userid"]
print(f"[*] Найден ID пользователя {TEST_USER}: {user_id}")

# Получение CSRF-токена
token_params = {
    "action": "query",
    "meta": "tokens",
    "format": "json"
}
t_resp = session.get(api_url, params=token_params).json()
csrf_token = t_resp.get("query", {}).get("tokens", {}).get("csrftoken")
print("[*] CSRF-токен получен.")

# 3. Формирование структуры сообщения
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

# 4. Отправка темы на стену
wall_url = f"https://{DOMAIN}{PATH}wikia.php"
wall_params = {
    "controller": r"Fandom\MessageWall\MessageWall",
    "method": "createThread",
    "format": "json"
}

wall_data = {
    "token": csrf_token,
    "wallOwnerId": user_id,
    "title": msg_title,
    "rawContent": msg_text,
    "jsonModel": json.dumps(json_model, ensure_ascii=False),
    "attachments": json.dumps(attachments)
}

wall_headers = {
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest"
}

resp = session.post(wall_url, params=wall_params, data=wall_data, headers=wall_headers)
print(f"[*] Статус отправки на стену: {resp.status_code}")
print(f"[*] Ответ сервера: {resp.text}")
