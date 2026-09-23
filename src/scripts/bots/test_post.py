import os
import sys
import requests
import mwclient

DOMAIN = "hazbinhotel.fandom.com"
PATH = "/ru/"
TEST_USER = os.environ.get("TEST_USER", "Swit4er")

user = os.environ.get("WIKI_USERNAME")
password = os.environ.get("WIKI_PASSWORD")

# 1. Проверка наличия секретов
if not user or not password:
    print("[-] Ошибка: Секреты WIKI_USERNAME или WIKI_PASSWORD не найдены в окружении!")
    sys.exit(1)

site = mwclient.Site(DOMAIN, path=PATH)

try:
    site.login(user, password)
    print(f"[+] Авторизация успешна под аккаунтом: {user}")
except Exception as e:
    print(f"[-] Ошибка входа в аккаунт: {e}")
    sys.exit(1)

# 2. Получение User ID целевого пользователя
user_query = site.api("query", list="users", ususers=TEST_USER)
users_data = user_query.get("query", {}).get("users", [])

if not users_data or "userid" not in users_data[0]:
    print(f"[-] Не удалось найти пользователя {TEST_USER} или его ID.")
    sys.exit(1)

user_id = users_data[0]["userid"]
print(f"[*] Найден ID пользователя {TEST_USER}: {user_id}")

# 3. Получение CSRF токена
token_res = site.api("query", meta="tokens")
csrf_token = token_res.get("query", {}).get("tokens", {}).get("csrftoken")

# 4. Отправка сообщения на стену
url = f"https://{DOMAIN}{PATH}wikia.php"
params = {
    "controller": "Wall",
    "method": "postNewMessage",
    "format": "json"
}
data = {
    "wallOwnerId": user_id,
    "wallOwner": TEST_USER,
    "messagetitle": "Тестовое приветствие",
    "body": "Проверка работы автоматического скрипта приветствий.",
    "token": csrf_token
}
headers = {
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest"
}

resp = site.connection.post(url, params=params, data=data, headers=headers)
print(f"[*] Статус отправки на стену: {resp.status_code}")
print(f"[*] Ответ сервера: {resp.text}")
