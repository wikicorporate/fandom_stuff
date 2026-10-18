import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Set

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.wiki_client import REPO_ROOT, create_http_session, load_projects


def fetch_interwikis() -> None:
    session = create_http_session()
    projects = load_projects()

    for project_name, cfg in projects.items():
        output_rel = cfg.get("interwiki_output")
        hubs: Dict[str, str] = cfg.get("hubs", {})
        domain = cfg.get("domain")
        api_path = cfg.get("path", "/ru/")

        if not output_rel or not hubs or not domain:
            continue

        output_path = REPO_ROOT / output_rel
        ru_api = f"https://{domain}{api_path}api.php"

        print(f"\n[=== Запуск сбора интервики для проекта: {project_name} ===]")

        # 1. Загружаем существующую базу
        interwiki_db: Dict[str, Dict[str, str]] = {}
        if output_path.exists():
            try:
                with open(output_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        interwiki_db = loaded
                print(f"[*] Загружена существующая база: {len(interwiki_db)} статей.")
            except Exception as e:
                print(f"[!] Ошибка чтения старой базы {output_path}: {e}")

        # 2. Собираем свежие ссылки со всех языковых хабов
        temp_db: Dict[str, Dict[str, str]] = {}
        for hub_lang, hub_url in hubs.items():
            print(f"[*] Сканирую {hub_lang.upper()} вики ({hub_url})...")
            params = {
                "action": "query",
                "generator": "allpages",
                "gaplimit": "50",
                "gapnamespace": "0",
                "gapfilterredir": "nonredirects",
                "prop": "langlinks",
                "lllimit": "max",
                "format": "json",
            }

            while True:
                response = None
                for attempt in range(1, 4):
                    try:
                        req = session.get(hub_url, params=params, timeout=60)
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

                        # Сохраняем транзитивные интервики-ссылки на другие языки
                        for link in langlinks:
                            l_code = link.get("lang")
                            l_title = (link.get("*") or "").strip()
                            if l_code and l_code != "ru" and l_title and l_code not in temp_db[ru_title]:
                                temp_db[ru_title][l_code] = l_title

                if "continue" in response:
                    params.update(response["continue"])
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
            except Exception as e:
                print(f"  [!] Ошибка при проверке пачки статей на {ru_api}: {e}")

        # 4. Переносим валидные старые записи на нормализованные/перенаправленные названия
        cleaned_db: Dict[str, Dict[str, str]] = {}
        for old_title, links in interwiki_db.items():
            norm_title = norm_map.get(old_title, old_title)
            true_title = redirect_map.get(norm_title, norm_title)
            if true_title not in valid_ru_titles:
                continue
            if true_title not in cleaned_db:
                cleaned_db[true_title] = {}
            for lang, target in links.items():
                if target and target.strip():
                    cleaned_db[true_title][lang] = target.strip()

        # 5. Накатываем свежие данные поверх старых (актуализируя переименованные статьи)
        for ru_title, links in temp_db.items():
            norm_title = norm_map.get(ru_title, ru_title)
            true_title = redirect_map.get(norm_title, norm_title)
            if true_title not in valid_ru_titles:
                continue
            if true_title not in cleaned_db:
                cleaned_db[true_title] = {}
            for lang, target in links.items():
                if target and target.strip():
                    cleaned_db[true_title][lang] = target.strip()

        # Удаляем записи без единой непустой интервики-ссылки
        cleaned_db = {k: v for k, v in cleaned_db.items() if v}

        os.makedirs(output_path.parent, exist_ok=True)
        with open(output_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(cleaned_db, f, ensure_ascii=False, indent=4, sort_keys=True)
            f.write("\n")

        print(f"[+] Успешно! База {project_name} сохранена: {len(cleaned_db)} чистых статей.")


if __name__ == "__main__":
    fetch_interwikis()
