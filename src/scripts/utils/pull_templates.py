import os
import re
from typing import Dict, Set
import requests

MAIN_WIKIS: Dict[str, str] = {
    "hazbin": "https://hazbinhotel.fandom.com/ru/api.php",
    "zoophobia": "https://zoophobia.fandom.com/ru/api.php",
    "returnal": "https://returnal.fandom.com/ru/api.php",
    "helltaker": "https://helltaker.fandom.com/ru/api.php",
    "oneshot": "https://oneshot.fandom.com/ru/api.php",
}

CORPORATE_WIKI = ("wikicorporate", "https://wikicorporate.fandom.com/ru/api.php")
VIVZIE_GROUP = {"hazbin", "zoophobia"}

GLOBAL_TPL_DIR = os.path.join("src", "global", "templates")
SHARED_VIVZIE_DIR = os.path.join("src", "shared", "vivzieverse", "templates")


def normalize_code(text: str) -> str:
    """Нормализует переводы строк и пробелы по краям для точного сравнения кода шаблонов."""
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def sanitize_rel_path(title_without_ns: str) -> str:
    """Преобразует название шаблона (включая подстраницы через '/') в безопасный путь .wikitext."""
    clean = title_without_ns.strip().replace(":", "_")
    return f"{clean}.wikitext"


def read_existing_templates(base_dir: str) -> Dict[str, str]:
    """Читает уже существующие в репозитории шаблоны из указанной папки."""
    existing: Dict[str, str] = {}
    if not os.path.exists(base_dir):
        return existing

    for root, _, files in os.walk(base_dir):
        for file in files:
            if not file.endswith(".wikitext"):
                continue
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, base_dir).replace(os.sep, "/")
            tpl_name = rel_path[:-9]  # отрезаем '.wikitext'
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    existing[tpl_name] = normalize_code(f.read())
            except Exception:
                pass
    return existing


def fetch_wiki_templates(api_url: str) -> Dict[str, str]:
    """Скачивает все не-редиректные шаблоны (ns=10) с указанной вики."""
    session = requests.Session()
    session.headers.update({"User-Agent": "FandomTemplatePuller/1.0"})

    titles = []
    params = {
        "action": "query",
        "list": "allpages",
        "apnamespace": "10",
        "apfilterredir": "nonredirects",
        "aplimit": "max",
        "format": "json",
    }

    while True:
        res = session.get(api_url, params=params, timeout=30).json()
        for p in res.get("query", {}).get("allpages", []):
            title = p["title"]
            # Пропускаем подстраницы документации, песочниц и тестов
            if any(sub in title.lower() for sub in ("/doc", "/документация", "/песочница", "/sandbox")):
                continue
            titles.append(title)
        if "continue" in res:
            params.update(res["continue"])
        else:
            break

    templates: Dict[str, str] = {}
    for i in range(0, len(titles), 50):
        chunk = titles[i : i + 50]
        q_params = {
            "action": "query",
            "prop": "revisions",
            "titles": "|".join(chunk),
            "rvprop": "content",
            "rvslots": "main",
            "formatversion": "2",
            "format": "json",
        }
        res = session.get(api_url, params=q_params, timeout=30).json()
        for page in res.get("query", {}).get("pages", []):
            if page.get("missing"):
                continue
            clean_name = page["title"].split(":", 1)[-1]
            content = (
                page.get("revisions", [{}])[0]
                .get("slots", {})
                .get("main", {})
                .get("content", "")
            )
            norm = normalize_code(content)
            if norm:
                templates[clean_name] = norm

    return templates


def save_template(base_dir: str, tpl_name: str, code: str) -> str:
    rel_path = sanitize_rel_path(tpl_name)
    full_path = os.path.join(base_dir, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(code + "\n")
    return full_path


def remove_if_exists(base_dir: str, tpl_name: str) -> None:
    full_path = os.path.join(base_dir, sanitize_rel_path(tpl_name))
    if os.path.exists(full_path):
        try:
            os.remove(full_path)
        except OSError:
            pass


def main() -> None:
    existing_global = read_existing_templates(GLOBAL_TPL_DIR)
    existing_vivzie = read_existing_templates(SHARED_VIVZIE_DIR)

    print(f"[*] Уже в репозитории: global={len(existing_global)}, vivzieverse={len(existing_vivzie)}")

    # 1. Собираем шаблоны с 5 боевых проектов
    wiki_data: Dict[str, Dict[str, str]] = {}
    all_tpl_names: Set[str] = set()

    for alias, api_url in MAIN_WIKIS.items():
        print(f"[*] Скачиваю шаблоны с {alias} ({api_url})...")
        tpls = fetch_wiki_templates(api_url)
        wiki_data[alias] = tpls
        all_tpl_names.update(tpls.keys())
        print(f"    Найдено шаблонов: {len(tpls)}")

    # 2. Классифицируем и сохраняем шаблоны без дубликатов
    stats = {"global_skipped": 0, "global_saved": 0, "shared_saved": 0, "local_saved": 0}

    for tpl_name in sorted(all_tpl_names):
        present_on = { alias: wiki_data[alias][tpl_name] for alias in MAIN_WIKIS if tpl_name in wiki_data[alias] }
        unique_codes = set(present_on.values())
        present_aliases = set(present_on.keys())

        # ПРАВИЛО А: Шаблон уже лежит в src/global/templates/
        if tpl_name in existing_global:
            global_code = existing_global[tpl_name]
            for alias, code in present_on.items():
                local_dir = os.path.join("src", "local", alias, "templates")
                if code == global_code:
                    remove_if_exists(local_dir, tpl_name)
                    stats["global_skipped"] += 1
                else:
                    # Если на конкретной вики шаблон кастомизирован и отличается от глобального
                    save_template(local_dir, tpl_name, code)
                    stats["local_saved"] += 1
            continue

        # ПРАВИЛО Б: Шаблон одинаковый минимум на 3 проектах (или на всех проектах, где он есть, вне одной группы)
        if len(unique_codes) == 1 and (len(present_aliases) >= 3 or (len(present_aliases) == 2 and present_aliases != VIVZIE_GROUP)):
            code = next(iter(unique_codes))
            save_template(GLOBAL_TPL_DIR, tpl_name, code)
            existing_global[tpl_name] = code
            for alias in present_aliases:
                remove_if_exists(os.path.join("src", "local", alias, "templates"), tpl_name)
            stats["global_saved"] += 1
            print(f"  [GLOBAL] Шаблон '{tpl_name}' вынесен в src/global/templates/ (совпадает на: {', '.join(sorted(present_aliases))})")
            continue

        # ПРАВИЛО В: Шаблон уже в src/shared/vivzieverse/templates/ или одинаков на hazbin + zoophobia
        if tpl_name in existing_vivzie or (present_aliases == VIVZIE_GROUP and len(unique_codes) == 1):
            shared_code = existing_vivzie.get(tpl_name) or next(iter(unique_codes))
            save_template(SHARED_VIVZIE_DIR, tpl_name, shared_code)
            existing_vivzie[tpl_name] = shared_code
            for alias in VIVZIE_GROUP:
                if alias in present_on and present_on[alias] == shared_code:
                    remove_if_exists(os.path.join("src", "local", alias, "templates"), tpl_name)
                elif alias in present_on:
                    save_template(os.path.join("src", "local", alias, "templates"), tpl_name, present_on[alias])
                    stats["local_saved"] += 1
            stats["shared_saved"] += 1
            print(f"  [SHARED:vivzieverse] Шаблон '{tpl_name}' сохранён в src/shared/vivzieverse/templates/")
            continue

        # ПРАВИЛО Г: Локальные шаблоны конкретных проектов
        for alias, code in present_on.items():
            local_dir = os.path.join("src", "local", alias, "templates")
            save_template(local_dir, tpl_name, code)
            stats["local_saved"] += 1

    # 3. Отдельно скачиваем шаблоны с wikicorporate (пропуская те, что уже есть в global)
    corp_alias, corp_url = CORPORATE_WIKI
    print(f"\n[*] Скачиваю шаблоны с {corp_alias} ({corp_url})...")
    corp_tpls = fetch_wiki_templates(corp_url)
    corp_local_dir = os.path.join("src", "local", corp_alias, "templates")
    for tpl_name, code in sorted(corp_tpls.items()):
        if tpl_name in existing_global and existing_global[tpl_name] == code:
            remove_if_exists(corp_local_dir, tpl_name)
            continue
        save_template(corp_local_dir, tpl_name, code)
        stats["local_saved"] += 1

    print(
        f"\n✅ Выгрузка шаблонов завершена!\n"
        f"   • Совпало с существующими в global (дубликаты пропущены): {stats['global_skipped']}\n"
        f"   • Вынесено новых в src/global/templates/: {stats['global_saved']}\n"
        f"   • Вынесено в src/shared/vivzieverse/templates/: {stats['shared_saved']}\n"
        f"   • Сохранено локальных шаблонов в src/local/*/templates/: {stats['local_saved']}"
    )


if __name__ == "__main__":
    main()
