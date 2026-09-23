import os
import re
import json
import time
import requests
import mwclient

DATA_FILE = "src/data/welcomed_users.json"

PROJECTS = {
    "Hazbin Hotel": {
        "domain": "hazbinhotel.fandom.com",
        "path": "/ru/",
        "wall_title": "Добро пожаловать на Вики!",
        "wall_message": "Приветствуем на проекте! Спасибо за {action_phrase}. Если у вас возникнут вопросы по оформлению или правилам вики, вы всегда можете задать их на этой стене."
    },
    "Zoophobia": {
        "domain": "zoophobia.fandom.com",
        "path": "/ru/",
        "wall_title": "Добро пожаловать на Zoophobia Вики!",
        "wall_message": "Приветствуем! Спасибо за {action_phrase}. Если понадобится помощь с кодом, шаблонами или содержанием статей — пишите на стену."
    },
    "Returnal": {
        "domain": "returnal.fandom.com",
        "path": "/ru/",
        "wall_title": "Добро пожаловать!",
        "wall_message": "Приветствуем исследователя Атропоса! Спасибо за {action_phrase}."
    },
    "Helltaker": {
        "domain": "helltaker.fandom.com",
        "path": "/ru/",
        "wall_title": "Добро пожаловать в Ад!",
        "wall_message": "Приветствуем на проекте! Спасибо за {action_phrase}."
    },
    "OneShot": {
        "domain": "oneshot.fandom.com",
        "path": "/ru/",
        "wall_title": "Добро пожаловать в мир OneShot!",
        "wall_message": "Приветствуем! Спасибо за {action_phrase}."
    }
}

def load_database():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {k: set(v) for k, v in data.items()}
        except Exception as e:
            print(f"[-] Не удалось прочитать базу данных: {e}")
            return {}
    return {}

def save_database(db):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    serializable = {k: sorted(list(v)) for k, v in db.items()}
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(serializable, f, ensure_ascii=False, indent=2)

def is_ip(username):
    ipv4 = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"
    ipv6 = r"^[0-9a-fA-F:]+$"
    return bool(re.match(ipv4, username) or (":" in username and re.match(ipv6, username)))

def get_wiki_id(domain, path):
    url = f"https://{domain}{path}api.php"
    params = {
        "action": "query",
        "meta": "siteinfo",
        "siprop": "wikidesc",
        "format": "json"
    }
    try:
        r = requests.get(url, params=params, timeout=10).json()
        return r.get("query", {}).get("wikidesc", {}).get("id")
    except Exception as e:
        print(f"[-] Ошибка получения wiki_id для {domain}: {e}")
        return None

def post_to_wall(session, domain, username, title, message, csrf_token):
    url = f"https://{domain}/wikia.php"
    params = {
        "controller": "WallExternal",
        "method": "postNewMessage",
        "format": "json"
    }
    data = {
        "wallOwner": username,
        "messagetitle": title,
        "body": message,
        "token": csrf_token
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest"
    }
    resp = session.post(url, params=params, data=data, headers=headers)
    return resp.status_code == 200

def create_blank_user_page(site, username):
    page = site.pages[f"Участник:{username}"]
    if not page.exists:
        page.save("\n", summary="Создание страницы участника")
        return True
    return False

def fetch_wiki_edits(site, welcomed_set, current_user):
    candidates = {}
    try:
        recent_changes = site.recentchanges(limit=100)
        for rc in recent_changes:
            u = rc.get("user")
            if not u or is_ip(u) or u.lower().endswith("bot") or u == current_user:
                continue

            if u not in welcomed_set and u not in candidates:
                title = rc.get("title", "")
                ns = rc.get("ns", 0)
                rc_type = rc.get("type", "edit")

                if ns == 0:
                    if rc_type == "new":
                        phrase = f"создание статьи [[{title}]]"
                    else:
                        phrase = f"правку в статье [[{title}]]"
                elif ns == 6:
                    phrase = f"загрузку файла [[:{title}]]"
                elif ns == 500 or "Блог участника:" in title or "User blog:" in title:
                    if rc_type == "new":
                        phrase = f"написание записи в блоге [[{title}]]"
                    else:
                        phrase = f"правку в записи блога [[{title}]]"
                elif ns == 501 or "Обсуждение блога участника:" in title or "User blog comment:" in title:
                    phrase = f"комментарий к записи в блоге [[{title}]]"
                else:
                    if rc_type == "new":
                        phrase = f"создание страницы [[{title}]]"
                    else:
                        phrase = f"правку на странице [[{title}]]"

                candidates[u] = {
                    "source": "wiki",
                    "phrase": phrase
                }
    except Exception as e:
        print(f"[-] Ошибка получения свежих правок: {e}")
    return candidates

def fetch_discussion_activity(wiki_id, domain, welcomed_set, current_user):
    candidates = {}
    if not wiki_id:
        return candidates

    url = f"https://services.fandom.com/discussion/{wiki_id}/posts"
    params = {"limit": 50, "page": 0, "responseGroup": "small"}
    headers = {"Accept": "application/json"}

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        if resp.status_code != 200:
            return candidates

        data = resp.json()
        threads = data.get("_embedded", {}).get("doc:posts", [])

        for item in threads:
            created_by = item.get("createdBy", {})
            u = created_by.get("name")
            if not u or is_ip(u) or u.lower().endswith("bot") or u == current_user:
                continue

            if u not in welcomed_set and u not in candidates:
                thread_id = item.get("threadId")
                full_url = f"https://{domain}/ru/f/p/{thread_id}"
                
                is_reply = item.get("isReply", False)
                container_type = str(item.get("containerType", "")).upper()
                forum_name = str(item.get("forumName", "")).lower()
                raw_title = item.get("title")

                if container_type in ("ARTICLE", "ARTICLE_COMMENT") or "article" in forum_name:
                    title_display = raw_title if raw_title else "этой статье"
                    if is_reply:
                        phrase = f"ответ на комментарий к статье [{full_url} {title_display}]"
                    else:
                        phrase = f"комментарий к статье [{full_url} {title_display}]"
                elif container_type in ("BLOG", "BLOG_POST") or "blog" in forum_name:
                    title_display = raw_title if raw_title else "этой записи"
                    if is_reply:
                        phrase = f"ответ на комментарий в блоге [{full_url} {title_display}]"
                    else:
                        phrase = f"комментарий к записи в блоге [{full_url} {title_display}]"
                else:
                    title_display = raw_title if raw_title else "эту тему"
                    if is_reply:
                        phrase = f"ответ в теме [{full_url} {title_display}] в обсуждениях"
                    else:
                        phrase = f"публикацию темы [{full_url} {title_display}] в обсуждениях"

                candidates[u] = {
                    "source": "discussion",
                    "phrase": phrase
                }
    except Exception as e:
        print(f"[-] Ошибка получения активности Discussions: {e}")

    return candidates

def main():
    user = os.environ.get("WIKI_USERNAME")
    password = os.environ.get("WIKI_PASSWORD")
    
    if not user or not password:
        print("[-] Ошибка: Переменные WIKI_USERNAME или WIKI_PASSWORD не заданы.")
        return

    clean_current_user = user.split("@")[0]
    db = load_database()
    total_welcomed = 0

    for project_name, config in PROJECTS.items():
        print(f"\n[=== Проверка проекта: {project_name} ===]")
        domain = config["domain"]
        path = config["path"]
        
        if project_name not in db:
            db[project_name] = set()

        site = mwclient.Site(domain, path=path)
        try:
            site.login(user, password)
            print(f"[+] Успешная авторизация под аккаунтом: {user}")
        except Exception as e:
            print(f"[-] Ошибка авторизации на {project_name}: {e}")
            continue

        raw_session = site.connection
        token_res = site.api("query", meta="tokens")
        csrf_token = token_res.get("query", {}).get("tokens", {}).get("csrftoken")

        wiki_id = get_wiki_id(domain, path)
        if wiki_id:
            print(f"[*] Определен ID вики: {wiki_id}")
        else:
            print("[-] Не удалось определить ID вики, обсуждения будут пропущены.")

        candidates = fetch_wiki_edits(site, db[project_name], clean_current_user)
        disc_candidates = fetch_discussion_activity(wiki_id, domain, db[project_name], clean_current_user)

        for u, data in disc_candidates.items():
            if u not in candidates:
                candidates[u] = data

        print(f"[*] Найдено новых участников для проверки: {len(candidates)}")

        for target_user, action_data in candidates.items():
            try:
                user_info = site.api("query", list="users", ususers=target_user, usprop="editcount")
                u_data = user_info.get("query", {}).get("users", [{}])[0]
                edit_count = u_data.get("editcount", 0)

                if edit_count <= 5:
                    phrase = action_data["phrase"]
                    print(f"[*] Приветствуем: {target_user} (действие: {phrase})")

                    create_blank_user_page(site, target_user)

                    formatted_message = config["wall_message"].format(
                        action_phrase=phrase
                    )

                    wall_ok = post_to_wall(
                        raw_session,
                        domain,
                        target_user,
                        config["wall_title"],
                        formatted_message,
                        csrf_token
                    )

                    if wall_ok:
                        print(f"  [+] Сообщение отправлено на стену {target_user}")
                    else:
                        print(f"  [-] Ошибка при отправке на стену {target_user}")

                    db[project_name].add(target_user)
                    total_welcomed += 1
                    time.sleep(5)
                else:
                    db[project_name].add(target_user)

            except Exception as e:
                print(f"[-] Ошибка при обработке {target_user}: {e}")

    if total_welcomed > 0:
        save_database(db)
        print(f"\n[+] Всего отправлено приветствий: {total_welcomed}. База данных обновлена.")
    else:
        print("\n[*] Новых участников для приветствия не обнаружено.")

if __name__ == "__main__":
    main()
