import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Set
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.wiki_client import REPO_ROOT, create_http_session, load_projects

MAIN_PAGE_TITLE = "Заглавная страница"


def merge_db(target: Dict[str, Dict[str, str]], source: Dict[str, Any]) -> None:
    """Аккуратно вливает словарь интервики source в target без потери существующих ключей."""
    if not isinstance(source, dict):
        return
    for page_title, links in source.items():
        if not isinstance(links, dict):
            continue
        if page_title not in target:
            target[page_title] = {}
        for lang, val in links.items():
            if isinstance(lang, str) and isinstance(val, str):
                if page_title == MAIN_PAGE_TITLE or val.strip():
                    target[page_title][lang] = val.strip()


def fetch_remote_existing_db(session: requests.Session, ru_api: str) -> Dict[str, Dict[str, str]]:
    """
    Подгружает существующую базу напрямую с русской вики (как из новой MediaWiki:Custom-Интервики.json,
    так и из старой Интервики.json в основном пространстве), чтобы при миграции не потерять ни одной статьи.
    """
    remote_db: Dict[str, Dict[str, str]] = {}
    params = {
        "action": "query",
        "prop": "revisions",
        "titles": "Интервики.json|MediaWiki:Custom-Интервики.json",
        "rvprop": "content",
        "rvslots": "main",
        "format": "json",
        "formatversion": "2",
    }
    try:
        res = session.get(ru_api, params=params, timeout=30).json()
        for page in res.get("query", {}).get("pages", []):
            if page.get("missing"):
                continue
            revs = page.get("revisions", [])
            if revs:
                content = revs[0].get("slots", {}).get("main", {}).get("content", "")
                if content:
                    try:
                        parsed = json.loads(content)
                        merge_db(remote_db, parsed)
                    except Exception:
                        pass
    except Exception as e:
        print(f"  [!] Не удалось прочитать резервную базу с {ru_api}: {e}")
    return remote_db


def fetch_interwikis() -> None:
    session = create_http_session()
    projects = load_projects()

    for project_name, cfg in projects.items():
        output_rel = cfg.get("interwiki_output")
        legacy_rel = cfg.get("legacy_interwiki_output")
        hubs: Dict[str, str] = cfg.get("hubs", {})
        domain = cfg.get("domain")
        api_path = cfg.get("path", "/ru/")

        if not output_rel or not hubs or not domain:
            continue

        output_path = REPO_ROOT / output_rel
        legacy_path = (REPO_ROOT / legacy_rel) if legacy_rel else None
        ru_api = f"https://{domain}{api_path}api.php"

        print(f"\n[=== Запуск сбора интервики для проекта: {project_name} ===]")

        # 1. Загружаем существующую базу из локальных файлов И с живой вики
        interwiki_db: Dict[str, Dict[str, str]] = {}

        for local_candidate in (legacy_path, output_path):
            if local_candidate and local_candidate.exists():
                try:
                    with open(local_candidate, "r", encoding="utf-8") as f:
                        merge_db(interwiki_db, json.load(f))
                except Exception as e:
                    print(f"[!] Ошибка чтения локального файла {local_candidate}: {e}")

        remote_existing = fetch_remote_existing_db(session, ru_api)
        merge_db(interwiki_db, remote_existing)
        print(f"[*] Загружена объединённая стартовая база: {len(interwiki_db)} статей.")

        # 2. Собираем свежие ссылки со всех языковых хабов (с чистой пагинацией без залипания llcontinue)
        temp_db: Dict[str, Dict[str, str]] = {}
        for hub_lang, hub_url in hubs.items():
            print(f"[*] Сканирую {hub_lang.upper()} вики ({hub_url})...")
            base_params = {
                "action": "query",
                "generator": "allpages",
                "gaplimit": "30",
                "gapnamespace": "0",
                "gapfilterredir": "nonredirects",
                "prop": "langlinks",
                "lllimit": "max",
                "format": "json",
            }
            continue_params: Dict[str, Any] = {}

            while True:
                req_params = {**base_params, **continue_params}
                response = None

                for attempt in range(1, 4):
                    try:
                        req = session.get(hub_url, params=req_params, timeout=60)
                        req.raise_for_status()
                        data = req.json()
                        if "error" in data:
                            print(f"  [!] Ошибка API ({hub_lang}): {data['error'].get('info', 'Unknown')}")
                            break
                        response = data
                        break
                    except Exception as e:
                        if attempt < 3:
                            time.sleep(3 * attempt)
                        else:
                            print(f"  [!] Сбой сети при запросе к {hub_url}: {e}")

                if not response:
                    break

                pages = response.get("query", {}).get("pages", {})

                # Сначала собираем все языковые ссылки по page_id в рамках текущего ответа
                for _, page_data in pages.items():
                    langlinks = page_data.get("langlinks", [])
                    if not langlinks:
                        continue

                    hub_title = page_data.get("title", "").strip()
                    if not hub_title:
                        continue

                    ru_title = None
                    for link in langlinks:
                        if link.get("lang") == "ru":
                            ru_title = (link.get("*") or "").strip()
                            break

                    if ru_title:
                        if ru_title not in temp_db:
                            temp_db[ru_title] = {}
                        temp_db[ru_title][hub_lang] = hub_title

                        for link in langlinks:
                            l_code = link.get("lang")
                            l_title = (link.get("*") or "").strip()
                            if l_code and l_code != "ru" and l_title and l_code not in temp_db[ru_title]:
                                temp_db[ru_title][l_code] = l_title

                # Заменяем continue_params целиком (чтобы отработавший llcontinue не оставался в запросе!)
                if "continue" in response:
                    continue_params = response["continue"]
                else:
                    break

        # 3. Сверка с русской вики: нормализация, редиректы и проверка существования статей
        print("[*] Сверка с русской вики (поиск редиректов и удаление несуществующих статей)...")
        ru_titles = sorted(set(list(temp_db.keys()) + list(interwiki_db.keys())))

        norm_map: Dict[str, str] = {}
        redirect_map: Dict[str, str] = {}
        valid_ru_titles: Set[str] = set()

        for i in range(0, len(ru_titles), 50):
            chunk = ru_titles[i : i + 50]
            post_data = {
                "action": "query",
                "titles": "|".join(chunk),
                "redirects": "1",
                "format": "json",
            }
            chunk_ok = False
            for attempt in range(1, 4):
                try:
                    res = session.post(ru_api, data=post_data, timeout=30).json()
                    query_data = res.get("query", {})

                    for norm in query_data.get("normalized", []):
                        norm_map[norm["from"]] = norm["to"]

                    for redir in query_data.get("redirects", []):
                        redirect_map[redir["from"]] = redir["to"]

                    for page_id, page_info in query_data.get("pages", {}).items():
                        if int(page_id) > 0 and "missing" not in page_info:
                            valid_ru_titles.add(page_info["title"])

                    chunk_ok = True
                    break
                except Exception as e:
                    if attempt < 3:
                        time.sleep(2 * attempt)
                    else:
                        print(f"  [!] Ошибка при проверке пачки статей на {ru_api}: {e}")

            # Fail-safe: если пачка не проверилась из-за сбоя сети, сохраняем статьи, чтобы не удалить живые данные
            if not chunk_ok:
                valid_ru_titles.update(chunk)

        # 4. Переносим валидные старые записи
        cleaned_db: Dict[str, Dict[str, str]] = {}
        for old_title, links in interwiki_db.items():
            norm_title = norm_map.get(old_title, old_title)
            true_title = redirect_map.get(norm_title, norm_title)
            if true_title != MAIN_PAGE_TITLE and true_title not in valid_ru_titles:
                continue
            if true_title not in cleaned_db:
                cleaned_db[true_title] = {}
            for lang, target in links.items():
                if true_title == MAIN_PAGE_TITLE:
                    cleaned_db[true_title][lang] = ""
                elif target and target.strip():
                    cleaned_db[true_title][lang] = target.strip()

        # 5. Накатываем свежие данные поверх старых
        for ru_title, links in temp_db.items():
            norm_title = norm_map.get(ru_title, ru_title)
            true_title = redirect_map.get(norm_title, norm_title)
            if true_title != MAIN_PAGE_TITLE and true_title not in valid_ru_titles:
                continue
            if true_title not in cleaned_db:
                cleaned_db[true_title] = {}
            for lang, target in links.items():
                if true_title == MAIN_PAGE_TITLE:
                    cleaned_db[true_title][lang] = ""
                elif target and target.strip():
                    cleaned_db[true_title][lang] = target.strip()

        # 6. Защита Заглавной страницы
        if MAIN_PAGE_TITLE not in cleaned_db:
            cleaned_db[MAIN_PAGE_TITLE] = {}
        for hub_lang in hubs.keys():
            cleaned_db[MAIN_PAGE_TITLE][hub_lang] = ""

        cleaned_db = {
            k: v for k, v in cleaned_db.items() if v or k == MAIN_PAGE_TITLE
        }

        os.makedirs(output_path.parent, exist_ok=True)
        with open(output_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(cleaned_db, f, ensure_ascii=False, indent=4, sort_keys=True)
            f.write("\n")

        if legacy_path and legacy_path.exists() and legacy_path != output_path:
            try:
                legacy_path.unlink()
                print(f"[*] Удалён устаревший файл: {legacy_path.relative_to(REPO_ROOT)}")
            except OSError:
                pass

        print(
            f"[+] Успешно! База {project_name} сохранена в {output_path.relative_to(REPO_ROOT)}: "
            f"{len(cleaned_db)} статей (Заглавная страница защищена: {len(cleaned_db[MAIN_PAGE_TITLE])} яз.)."
        )


if __name__ == "__main__":
    fetch_interwikis()
