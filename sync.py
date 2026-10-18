import json
import os
import re
import time
from typing import Dict, List, Optional, Tuple
import mwclient
from mwclient.errors import APIError

# Поддержка всех вариантов именования секретов в GitHub Actions
USERNAME: Optional[str] = (
    os.environ.get("WIKI_USERNAME")
    or os.environ.get("FANDOM_USERNAME")
    or os.environ.get("FANDOM_BOT_USERNAME")
)
PASSWORD: Optional[str] = (
    os.environ.get("WIKI_PASSWORD")
    or os.environ.get("FANDOM_PASSWORD")
    or os.environ.get("FANDOM_BOT_PASSWORD")
)

USER_AGENT = "FandomStuffSyncBot/2.0 (https://github.com/; MediaWiki/mwclient)"

# Маппинг папок репозитория в пространства имён MediaWiki
NAMESPACE_MAP: Dict[str, str] = {
    "modules": "Module",
    "templates": "Template",
    "scripts": "MediaWiki",
    "mediawiki": "MediaWiki",
    "styles": "MediaWiki",
    "widgets": "Widget",
    "main": "",
}

# Директории с исходниками, которые не должны загружаться напрямую на вики
IGNORED_DIRS = {"cwa_source", "__pycache__"}

site_connections: Dict[str, Optional[mwclient.Site]] = {}


def parse_fandom_domain(raw_domain: str) -> Tuple[str, str]:
    """Преобразует 'ru.hazbinhotel.fandom.com' или 'hazbinhotel.fandom.com/ru' в (host, path)."""
    clean = re.sub(r"^https?://", "", raw_domain).strip("/")

    if "/" in clean:
        host, subpath = clean.split("/", 1)
        return host, f"/{subpath.strip('/')}/"

    match = re.match(r"^([a-z\-]{2,5})\.([^.]+\.fandom\.com)$", clean, re.IGNORECASE)
    if match:
        lang, host = match.group(1), match.group(2)
        return host, f"/{lang}/"

    return clean, "/"


def get_site(domain: str) -> Optional[mwclient.Site]:
    if domain not in site_connections:
        host, api_path = parse_fandom_domain(domain)
        print(f"\n🔌 Подключение к {host} (путь: {api_path})...")

        try:
            site = mwclient.Site(
                host,
                path=api_path,
                clients_useragent=USER_AGENT,
                reqs={"timeout": 30},
            )
            site.login(USERNAME, PASSWORD)
            site_connections[domain] = site
        except Exception as e:
            print(f"❌ Ошибка авторизации на {domain}: {e}")
            site_connections[domain] = None

    return site_connections[domain]


def get_page_title(folder_name: str, rel_filepath: str) -> Optional[str]:
    """Вычисляет целевое название страницы на вики по имени папки и относительному пути файла."""
    ns = NAMESPACE_MAP.get(folder_name.lower())
    if ns is None:
        return None

    if ns in ("Module", "Template", "Widget"):
        if rel_filepath.lower().endswith(".json"):
            name = rel_filepath
        else:
            name = os.path.splitext(rel_filepath)[0]
    elif ns == "MediaWiki":
        # Для LESS-файлов или чистых препроцессорных исходников не отрезаем расширение,
        # но если это стандартный .js / .css — оставляем как есть (например MediaWiki:Common.js)
        name = rel_filepath
    else:
        name = rel_filepath

    return name if ns == "" else f"{ns}:{name}"


def normalize_text(text: str) -> str:
    """Нормализует переводы строк для точного сравнения локального и удалённого файлов."""
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def upload_file(domain: str, filepath: str, page_title: str) -> None:
    site = get_site(domain)
    if not site:
        return

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            local_content = f.read()
    except UnicodeDecodeError:
        print(f"   ⚠️ Пропуск бинарного или повреждённого файла: {filepath}")
        return

    try:
        page = site.pages[page_title]
        remote_content = page.text()
    except Exception as e:
        print(f"   ❌ Ошибка чтения {page_title} на {domain}: {e}")
        return

    if normalize_text(local_content) == normalize_text(remote_content):
        print(f"   [Без изменений] {page_title} ({domain})")
        return

    print(f"   [Обновление] {page_title} -> {domain}")
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            page.save(
                local_content,
                summary="Синхронизация из монорепозитория GitHub Actions",
                bot=True,
            )
            time.sleep(3)
            break
        except APIError as e:
            if e.code in ("ratelimited", "maxlag") and attempt < max_retries:
                wait_time = 15 * attempt
                print(f"   ⏳ Лимит API ({e.code}). Ожидание {wait_time} сек. (попытка {attempt}/{max_retries})...")
                time.sleep(wait_time)
            else:
                print(f"   ❌ Ошибка API при загрузке {page_title} на {domain}: {e}")
                break
        except Exception as e:
            print(f"   ❌ Непредвиденная ошибка при загрузке {page_title} на {domain}: {e}")
            break


def process_directory(base_dir: str, target_domains: List[str]) -> None:
    if not os.path.exists(base_dir) or not target_domains:
        return

    for ns_folder in sorted(os.listdir(base_dir)):
        ns_path = os.path.join(base_dir, ns_folder)
        if not os.path.isdir(ns_path) or ns_folder.lower() not in NAMESPACE_MAP:
            continue

        for root, dirs, files in os.walk(ns_path):
            # Исключаем служебные папки исходников на месте
            dirs[:] = [d for d in sorted(dirs) if d not in IGNORED_DIRS and not d.startswith(".")]

            for filename in sorted(files):
                if filename.startswith("."):
                    continue

                filepath = os.path.join(root, filename)
                rel_path = os.path.relpath(filepath, ns_path).replace(os.sep, "/")

                page_title = get_page_title(ns_folder, rel_path)
                if not page_title:
                    continue

                for domain in target_domains:
                    upload_file(domain, filepath, page_title)


def main() -> None:
    if not USERNAME or not PASSWORD:
        print("❌ Учётные данные (WIKI_USERNAME / WIKI_PASSWORD) не найдены в переменных окружения!")
        raise SystemExit(1)

    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Ошибка чтения config.json: {e}")
        raise SystemExit(1)

    print("🚀 Начинаем синхронизацию файлов с Fandom...")

    # 1. Глобальные ресурсы (на все вики)
    process_directory("src/global", config.get("all_wikis", []))

    # 2. Локальные ресурсы конкретных вики
    local_dir = "src/local"
    if os.path.exists(local_dir):
        local_aliases = config.get("local_aliases", {})
        for folder_name in sorted(os.listdir(local_dir)):
            domain_path = os.path.join(local_dir, folder_name)
            if os.path.isdir(domain_path):
                target_domain = local_aliases.get(folder_name, folder_name)
                process_directory(domain_path, [target_domain])

    # 3. Групповые ресурсы (кластеры вики, например vivzieverse)
    shared_dir = "src/shared"
    if os.path.exists(shared_dir):
        groups_cfg = config.get("groups", {})
        for group_folder in sorted(os.listdir(shared_dir)):
            group_path = os.path.join(shared_dir, group_folder)
            if os.path.isdir(group_path):
                target_domains = groups_cfg.get(group_folder, [])
                if not target_domains:
                    print(f"⚠️ Внимание: Группа '{group_folder}' не описана в config.json!")
                    continue
                process_directory(group_path, target_domains)

    print("\n✅ Синхронизация успешно завершена!")


if __name__ == "__main__":
    main()
