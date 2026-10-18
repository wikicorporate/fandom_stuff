import calendar
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Set
import mwclient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.wiki_client import connect_site, get_credentials, safe_save

PREFIX_MAP = {
    "HH-": "Категория:Изображения Отеля Хазбин",
    "HB-": "Категория:Изображения Адского Босса",
}

CATEGORY_REGEX = re.compile(r"\[\[\s*(?:Категория|Category)\s*:", re.IGNORECASE)


def categorize_simple(site: mwclient.Site, page: mwclient.page.Page) -> None:
    filename = page.name.split(":", 1)[-1].strip()
    prefix = filename[:3].upper()

    if prefix not in PREFIX_MAP:
        return

    try:
        text = page.text()
    except Exception as e:
        print(f"[-] Ошибка чтения страницы файла {filename}: {e}")
        return

    # ПРОВЕРКА 1: Есть ли уже какая-либо категория у файла
    if CATEGORY_REGEX.search(text):
        print(f"[*] Пропуск (уже есть категория): {filename}")
        return

    # ПРОВЕРКА 2: Находится ли файл в общем хранилище (Shared Repository)
    try:
        res = site.api("query", prop="imageinfo", titles=page.name)
        pages = res.get("query", {}).get("pages", {})
        for _, pdata in pages.items():
            repo = pdata.get("imagerepository")
            if repo != "local":
                print(f"[*] Пропуск (файл из хранилища '{repo}'): {filename}")
                return
    except Exception as e:
        print(f"[-] Ошибка проверки репозитория для {filename}: {e}")
        return

    category_tag = f"[[{PREFIX_MAP[prefix]}]]"
    stripped = text.strip()
    new_text = f"{stripped}\n\n{category_tag}" if stripped else category_tag

    if safe_save(page, new_text, summary="Категоризация новых и восстановленных файлов", bot=True):
        print(f"[+] Добавлена категория для {filename}")


def main() -> None:
    username, password = get_credentials(prefer_bot=True)
    if not username or not password:
        print("[-] Ошибка: Секреты логина/пароля бота не найдены в окружении!")
        raise SystemExit(1)

    print("[=== Запуск Категоризатора файлов ===]")
    site = connect_site("hazbinhotel.fandom.com", path="/ru/", username=username, password=password)
    if not site:
        raise SystemExit(1)

    processed_files: Set[str] = set()

    # ЭТАП 1: Проверка лога загрузок за последние 24 часа
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
    print(f"\n[*] ЭТАП 1: Проверка файлов, загруженных после: {cutoff_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")

    try:
        uploads = site.logevents(type="upload")
        for upload in uploads:
            ts_struct = upload.get("timestamp")
            if not ts_struct:
                continue
            event_time = datetime.fromtimestamp(calendar.timegm(ts_struct), tz=timezone.utc)

            if event_time < cutoff_time:
                print("[+] Достигнут предел в 24 часа. Загрузки проверены.")
                break

            title = upload.get("title")
            if title and title not in processed_files:
                processed_files.add(title)
                categorize_simple(site, site.pages[title])
    except Exception as e:
        print(f"[-] Ошибка при получении лога загрузок: {e}")

    # ЭТАП 2: Проверка служебной страницы "Некатегоризованные файлы"
    print("\n[*] ЭТАП 2: Сканирование служебной страницы 'Некатегоризованные файлы'...")
    try:
        qpoffset = 0
        while True:
            response = site.api(
                "query",
                list="querypage",
                qppage="Uncategorizedimages",
                qplimit="max",
                qpoffset=qpoffset,
            )
            results = response.get("query", {}).get("querypage", {}).get("results", [])
            if not results:
                break

            for item in results:
                title = item.get("title")
                if title and title not in processed_files:
                    processed_files.add(title)
                    categorize_simple(site, site.pages[title])

            if "continue" in response and "qpoffset" in response["continue"]:
                qpoffset = response["continue"]["qpoffset"]
            else:
                break

        print("[+] Сканирование некатегоризованных файлов завершено.")
    except Exception as e:
        print(f"[-] Ошибка при получении списка некатегоризованных файлов: {e}")


if __name__ == "__main__":
    main()
