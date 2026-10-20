import argparse
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Set
import mwclient
from mwclient.errors import APIError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.wiki_client import connect_site, get_credentials, load_projects

TRUSTED_GROUPS: Set[str] = {
    "sysop",
    "bureaucrat",
    "content-moderator",
    "rollback",
    "bot",
    "autopatrolled",
    "staff",
    "soap",
    "wiki-representative",
    "wiki-specialist",
}


def get_patrol_token(site: mwclient.Site) -> Optional[str]:
    """Получает токен патрулирования (patroltoken) через MediaWiki API."""
    try:
        res = site.api("query", meta="tokens", type="patrol")
        return res.get("query", {}).get("tokens", {}).get("patroltoken")
    except Exception as e:
        print(f"  [-] Не удалось получить токен патрулирования: {e}")
        return None


def fetch_unpatrolled_changes(site: mwclient.Site, limit: int = 500) -> List[Dict]:
    """Возвращает список всех неотпатрулированных правок, новых страниц и загрузок файлов."""
    changes: List[Dict] = []
    params = {
        "list": "recentchanges",
        "rcshow": "!patrolled",
        "rctype": "edit|new|log",
        "rcprop": "ids|title|user|type|loginfo|timestamp",
        "rclimit": min(limit, 500),
    }

    try:
        while len(changes) < limit:
            res = site.api("query", **params)
            batch = res.get("query", {}).get("recentchanges", [])
            if not batch:
                break

            changes.extend(batch)

            if "continue" in res and len(changes) < limit:
                params.update(res["continue"])
            else:
                break
    except APIError as e:
        print(f"  [-] Ошибка API при получении списка неотпатрулированных правок ({e.code}): {e.info}")
    except Exception as e:
        print(f"  [-] Сбой при получении свежих правок: {e}")

    return changes[:limit]


def filter_trusted_users(site: mwclient.Site, changes: List[Dict]) -> Set[str]:
    """Возвращает множество участников из списка правок, имеющих доверенные флаги."""
    unique_users = sorted({c.get("user") for c in changes if c.get("user")})
    trusted_users: Set[str] = set()

    for i in range(0, len(unique_users), 50):
        chunk = unique_users[i : i + 50]
        try:
            res = site.api("query", list="users", ususers="|".join(chunk), usprop="groups")
            for u_info in res.get("query", {}).get("users", []):
                groups = set(u_info.get("groups", []))
                if not groups.isdisjoint(TRUSTED_GROUPS):
                    trusted_users.add(u_info.get("name", ""))
        except Exception:
            pass

    return trusted_users


def patrol_entry(site: mwclient.Site, rcid: int, title: str, patrol_token: str) -> bool:
    """Отправляет запрос на патрулирование конкретной записи rcid с обработкой лимитов API."""
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            site.api("patrol", rcid=rcid, token=patrol_token)
            return True
        except APIError as e:
            if e.code in ("ratelimited", "maxlag") and attempt < max_retries:
                wait_time = 15 * attempt
                print(
                    f"    [!] Лимит API ({e.code}) на '{title}' (rcid={rcid}). "
                    f"Ждём {wait_time} сек. (попытка {attempt}/{max_retries})..."
                )
                time.sleep(wait_time)
            else:
                print(f"    [-] Ошибка API при патрулировании '{title}' (rcid={rcid}): {e.code} — {e.info}")
                return False
        except Exception as e:
            print(f"    [-] Ошибка сети при патрулировании '{title}' (rcid={rcid}): {e}")
            return False
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Автоматическое патрулирование правок и файлов на вики.")
    parser.add_argument(
        "--mode",
        choices=["all", "trusted_only"],
        default="all",
        help="Режим: 'all' — патрулировать все правки и файлы; 'trusted_only' — только от доверенных групп.",
    )
    parser.add_argument(
        "--project",
        type=str,
        default="",
        help="Название конкретного проекта из config.json (пусто = проверить все вики).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=500,
        help="Максимальное число правок для патрулирования на одной вики за прогон.",
    )
    args = parser.parse_args()

    # Используем личный аккаунт администратора (prefer_bot=False)
    username, password = get_credentials(prefer_bot=False)
    if not username or not password:
        print("[-] Ошибка: Секреты FANDOM_USERNAME / FANDOM_PASSWORD не найдены в окружении!")
        raise SystemExit(1)

    clean_user = username.split("@")[0]
    projects = load_projects()
    total_patrolled = 0

    for project_name, cfg in projects.items():
        if args.project and args.project.lower() not in (
            project_name.lower(),
            cfg.get("alias", "").lower(),
        ):
            continue

        domain = cfg.get("domain")
        api_path = cfg.get("path", "/ru/")
        if not domain:
            continue

        print(f"\n[=== Автопатрулирование: {project_name} ({domain}{api_path}) ===]")
        site = connect_site(domain, path=api_path, username=username, password=password)
        if not site:
            continue

        print(f"[+] Авторизован как: {clean_user} | Режим: {args.mode}")

        patrol_token = get_patrol_token(site)
        if not patrol_token:
            continue

        unpatrolled = fetch_unpatrolled_changes(site, limit=args.limit)
        if not unpatrolled:
            print("[=] Нет неотпатрулированных правок или файлов.")
            continue

        print(f"[*] Найдено неотпатрулированных действий: {len(unpatrolled)}")

        trusted_users: Set[str] = set()
        if args.mode == "trusted_only":
            trusted_users = filter_trusted_users(site, unpatrolled)

        patrolled_on_wiki = 0
        for item in unpatrolled:
            rcid = item.get("rcid")
            title = item.get("title", "Без названия")
            user = item.get("user", "")
            rc_type = item.get("type", "edit")

            if not rcid:
                continue

            if args.mode == "trusted_only" and user not in trusted_users:
                continue

            if patrol_entry(site, rcid, title, patrol_token):
                patrolled_on_wiki += 1
                total_patrolled += 1
                action_label = "файл/лог" if rc_type == "log" else ("новая стр." if rc_type == "new" else "правка")
                print(f"  [+] Отпатрулировано ({action_label}): {title} (автор: {user}, rcid: {rcid})")
                time.sleep(0.4)

        print(f"[+] Итог по {project_name}: отпатрулировано {patrolled_on_wiki} из {len(unpatrolled)}.")

    print(f"\n[✅] Автопатрулирование завершено! Всего отпатрулировано: {total_patrolled}.")


if __name__ == "__main__":
    main()
