import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional, Set
import mwclient
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.wiki_client import (
    REPO_ROOT,
    connect_site,
    create_http_session,
    get_credentials,
    load_projects,
    safe_save,
)

DATA_FILE = REPO_ROOT / "src/data/welcomed_users.json"

IPV4_RE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$")
IPV6_RE = re.compile(r"^[0-9a-fA-F:]+$")


def load_database() -> Dict[str, Set[str]]:
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {k: set(v) for k, v in data.items() if isinstance(v, list)}
        except Exception as e:
            print(f"[-] Не удалось прочитать базу данных {DATA_FILE}: {e}")
    return {}


def save_database(db: Dict[str, Set[str]]) -> None:
    os.makedirs(DATA_FILE.parent, exist_ok=True)
    serializable = {k: sorted(list(v)) for k, v in sorted(db.items())}
    with open(DATA_FILE, "w", encoding="utf-8", newline="\n") as f:
        json.dump(serializable, f, ensure_ascii=False, indent=2)
        f.write("\n")


def is_ip(username: str) -> bool:
    return bool(IPV4_RE.match(username) or (":" in username and IPV6_RE.match(username)))


def get_wiki_id(http_session: requests.Session, domain: str, path: str) -> Optional[str]:
    url = f"https://{domain}{path}api.php"
    params = {
        "action": "query",
        "meta": "siteinfo",
        "siprop": "wikidesc",
        "format": "json",
    }
    try:
        r = http_session.get(url, params=params, timeout=15).json()
        return r.get("query", {}).get("wikidesc", {}).get("id")
    except Exception as e:
        print(f"[-] Ошибка получения wiki_id для {domain}: {e}")
        return None


def post_to_wall(
    session: requests.Session,
    domain: str,
    username: str,
    title: str,
    message: str,
    csrf_token: str,
) -> bool:
    url = f"https://{domain}/wikia.php"
    params = {
        "controller": "WallExternal",
        "method": "postNewMessage",
        "format": "json",
    }
    data = {
        "wallOwner": username,
        "messagetitle": title,
        "body": message,
        "token": csrf_token,
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
    }
    try:
        resp = session.post(url, params=params, data=data, headers=headers, timeout=20)
        if resp.status_code != 200:
            return False
        payload = resp.json()
        if isinstance(payload, dict) and ("error" in payload or "exception" in payload):
            print(f"  [!] Ответ WallExternal содержит ошибку: {payload}")
            return False
        return True
    except Exception as e:
        print(f"  [!] Исключение при отправке на стену {username}: {e}")
        return False


def create_blank_user_page(site: mwclient.Site, username: str) -> bool:
    page = site.pages[f"Участник:{username}"]
    if not page.exists:
        return safe_save(page, "\n", summary="Создание страницы участника", bot=True, sleep_after=1.0)
    return False


def fetch_wiki_edits(
    site: mwclient.Site,
    welcomed_set: Set[str],
    current_user: str,
) -> Dict[str, Dict[str, str]]:
    candidates: Dict[str, Dict[str, str]] = {}
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
                    phrase = f"создание статьи [[{title}]]" if rc_type == "new" else f"правку в статье [[{title}]]"
                elif ns == 6:
                    phrase = f"загрузку файла [[:{title}]]"
                elif ns == 500 or "Блог участника:" in title or "User blog:" in title:
                    phrase = (
                        f"написание записи в блоге [[{title}]]"
                        if rc_type == "new"
                        else f"правку в записи блога [[{title}]]"
                    )
                elif ns == 501 or "Обсуждение блога участника:" in title or "User blog comment:" in title:
                    phrase = f"комментарий к записи в блоге [[{title}]]"
                else:
                    phrase = (
                        f"создание страницы [[{title}]]"
                        if rc_type == "new"
                        else f"правку на странице [[{title}]]"
                    )

                candidates[u] = {"source": "wiki", "phrase": phrase}
    except Exception as e:
        print(f"[-] Ошибка получения свежих правок: {e}")
    return candidates


def fetch_discussion_activity(
    http_session: requests.Session,
    wiki_id: Optional[str],
    domain: str,
    welcomed_set: Set[str],
    current_user: str,
) -> Dict[str, Dict[str, str]]:
    candidates: Dict[str, Dict[str, str]] = {}
    if not wiki_id:
        return candidates

    url = f"https://services.fandom.com/discussion/{wiki_id}/posts"
    params = {"limit": 50, "page": 0, "responseGroup": "small"}
    headers = {"Accept": "application/json"}

    try:
        resp = http_session.get(url, params=params, headers=headers, timeout=15)
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
                    phrase = (
                        f"ответ на комментарий к статье [{full_url} {title_display}]"
                        if is_reply
                        else f"комментарий к статье [{full_url} {title_display}]"
                    )
                elif container_type in ("BLOG", "BLOG_POST") or "blog" in forum_name:
                    title_display = raw_title if raw_title else "этой записи"
                    phrase = (
                        f"ответ на комментарий в блоге [{full_url} {title_display}]"
                        if is_reply
                        else f"комментарий к записи в блоге [{full_url} {title_display}]"
                    )
                else:
                    title_display = raw_title if raw_title else "эту тему"
                    phrase = (
                        f"ответ в теме [{full_url} {title_display}] в обсуждениях"
                        if is_reply
                        else f"публикацию темы [{full_url} {title_display}] в обсуждениях"
                    )

                candidates[u] = {"source": "discussion", "phrase": phrase}
    except Exception as e:
        print(f"[-] Ошибка получения активности Discussions: {e}")

    return candidates


def main() -> None:
    user, password = get_credentials(prefer_bot=True)
    if not user or not password:
        print("[-] Ошибка: Учётные данные бота не заданы в переменных окружения.")
        raise SystemExit(1)

    clean_current_user = user.split("@")[0]
    db = load_database()
    http_session = create_http_session()
    projects = load_projects()

    total_welcomed = 0
    db_changed = False

    for project_name, config in projects.items():
        wall_title = config.get("wall_title")
        wall_message = config.get("wall_message")
        if not wall_title or not wall_message:
            continue

        print(f"\n[=== Проверка проекта: {project_name} ===]")
        domain = config["domain"]
        path = config.get("path", "/ru/")

        if project_name not in db:
            db[project_name] = set()
            db_changed = True

        site = connect_site(domain, path=path, username=user, password=password)
        if not site:
            continue

        print(f"[+] Успешная авторизация под аккаунтом: {clean_current_user}")

        raw_session = site.connection
        token_res = site.api("query", meta="tokens")
        csrf_token = token_res.get("query", {}).get("tokens", {}).get("csrftoken")
        if not csrf_token:
            print(f"[-] Не удалось получить CSRF-токен на {project_name}")
            continue

        wiki_id = get_wiki_id(http_session, domain, path)
        if wiki_id:
            print(f"[*] Определён ID вики: {wiki_id}")
        else:
            print("[-] Не удалось определить ID вики, обсуждения будут пропущены.")

        candidates = fetch_wiki_edits(site, db[project_name], clean_current_user)
        disc_candidates = fetch_discussion_activity(
            http_session, wiki_id, domain, db[project_name], clean_current_user
        )

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
                    formatted_message = wall_message.format(action_phrase=phrase)

                    wall_ok = post_to_wall(
                        raw_session,
                        domain,
                        target_user,
                        wall_title,
                        formatted_message,
                        csrf_token,
                    )

                    if wall_ok:
                        print(f"  [+] Сообщение отправлено на стену {target_user}")
                        db[project_name].add(target_user)
                        db_changed = True
                        total_welcomed += 1
                        time.sleep(5)
                    else:
                        print(f"  [-] Ошибка при отправке на стену {target_user} (будет повторено позже)")
                else:
                    # Участник уже опытный — запоминаем, чтобы не проверять повторно
                    db[project_name].add(target_user)
                    db_changed = True
            except Exception as e:
                print(f"[-] Ошибка при обработке {target_user}: {e}")

    if db_changed:
        save_database(db)
        print(f"\n[+] База данных обновлена. Отправлено новых приветствий: {total_welcomed}.")
    else:
        print("\n[*] Новых участников для приветствия не обнаружено.")


if __name__ == "__main__":
    main()
