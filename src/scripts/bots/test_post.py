import os
import requests
import mwclient

DOMAIN = "hazbinhotel.fandom.com"
PATH = "/ru/"
TEST_USER = "Swit4er"  # или никнейм тестового аккаунта

user = os.environ.get("WIKI_USERNAME")
password = os.environ.get("WIKI_PASSWORD")

site = mwclient.Site(DOMAIN, path=PATH)
site.login(user, password)
print("[+] Авторизация успешна.")

# Получение CSRF токена
token_res = site.api("query", meta="tokens")
csrf_token = token_res.get("query", {}).get("tokens", {}).get("csrftoken")

# Тест отправки на стену
url = f"https://{DOMAIN}/wikia.php"
params = {
    "controller": "WallExternal",
    "method": "postNewMessage",
    "format": "json"
}
data = {
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
