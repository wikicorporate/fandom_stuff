import os
import re
import requests

WIKIS = {
    "wikicorporate": "https://wikicorporate.fandom.com/ru/api.php",
    "hazbin": "https://hazbinhotel.fandom.com/ru/api.php",
    "zoophobia": "https://zoophobia.fandom.com/ru/api.php",
    "returnal": "https://returnal.fandom.com/ru/api.php",
    "helltaker": "https://helltaker.fandom.com/ru/api.php",
    "oneshot": "https://oneshot.fandom.com/ru/api.php",
}

MAX_DUMP_CHARS = 55000  # Безопасный лимит размера одного текстового файла для отправки в чат


def has_meaningful_css(content: str) -> bool:
    """
    Проверяет, есть ли в файле реальный CSS-код (правила, переменные или @import).
    Отсекает полностью пустые страницы и страницы, состоящие только из комментариев /* ... */.
    """
    if not content:
        return False
    without_comments = re.sub(r"/\*[\s\S]*?\*/", "", content)
    return bool(without_comments.strip())


def fetch_all_css_pages(api_url: str) -> dict[str, str]:
    session = requests.Session()
    session.headers.update({"User-Agent": "FandomCSSDumper/1.1"})

    # 1. Получаем список всех .css страниц в пространстве MediaWiki (ns=8)
    titles: list[str] = []
    params = {
        "action": "query",
        "list": "allpages",
        "apnamespace": "8",
        "aplimit": "max",
        "format": "json",
    }

    while True:
        res = session.get(api_url, params=params, timeout=30).json()
        for p in res.get("query", {}).get("allpages", []):
            title = p["title"]
            if title.lower().endswith(".css"):
                titles.append(title)
        if "continue" in res:
            params.update(res["continue"])
        else:
            break

    # 2. Скачиваем содержимое найденных CSS-страниц пачками по 50 штук
    css_files: dict[str, str] = {}
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

            if not has_meaningful_css(content):
                print(f"  [~] Пропущен пустой/закомментированный файл: MediaWiki:{clean_name}")
                continue

            css_files[clean_name] = content.strip()

    return css_files


def main() -> None:
    os.makedirs("css_dumps", exist_ok=True)

    for alias, api_url in WIKIS.items():
        print(f"\n[*] Сканирую CSS на {alias} ({api_url})...")
        css_map = fetch_all_css_pages(api_url)
        if not css_map:
            print(f"  [-] Непустые CSS-файлы на {alias} не найдены.")
            continue

        # Сохраняем в src/local/<alias>/styles/
        styles_dir = os.path.join("src", "local", alias, "styles")
        os.makedirs(styles_dir, exist_ok=True)

        part = 1
        current_dump = ""

        for name, code in sorted(css_map.items()):
            file_path = os.path.join(styles_dir, name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(code + "\n")
            print(f"  [+] Сохранён файл: {file_path}")

            block = (
                f"================================================\n"
                f"FILE: src/local/{alias}/styles/{name}\n"
                f"================================================\n"
                f"{code}\n\n"
            )

            if len(current_dump) + len(block) > MAX_DUMP_CHARS and current_dump:
                dump_name = f"css_dumps/{alias}_styles_part{part}.txt"
                with open(dump_name, "w", encoding="utf-8", newline="\n") as df:
                    df.write(current_dump)
                print(f"  [📦] Сформирован дамп для чата: {dump_name} ({len(current_dump)} симв.)")
                part += 1
                current_dump = block
            else:
                current_dump += block

        if current_dump:
            suffix = f"_part{part}" if part > 1 else ""
            dump_name = f"css_dumps/{alias}_styles{suffix}.txt"
            with open(dump_name, "w", encoding="utf-8", newline="\n") as df:
                df.write(current_dump)
            print(f"  [📦] Сформирован дамп для чата: {dump_name} ({len(current_dump)} симв.)")

    print("\n✅ Выгрузка всех таблиц стилей завершена!")


if __name__ == "__main__":
    main()
