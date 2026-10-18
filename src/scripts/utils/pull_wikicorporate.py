from pathlib import Path
import mwclient

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = REPO_ROOT / "src/local/wikicorporate/scripts"
MODULES_DIR = REPO_ROOT / "src/local/wikicorporate/modules"
DUMP_FILE = REPO_ROOT / "wikicorporate_dump.txt"

USER_AGENT = "FandomStuffPullBot/2.0 (https://github.com/wikicorporate/fandom_stuff; MediaWiki/mwclient)"


def pull_all() -> None:
    print("[*] Подключение к ru.wikicorporate.fandom.com...")
    site = mwclient.Site(
        "wikicorporate.fandom.com",
        path="/ru/",
        clients_useragent=USER_AGENT,
        reqs={"timeout": 30},
    )

    dump_chunks = []
    js_count = 0
    lua_count = 0

    # 1. Выгружаем все JS-скрипты из пространства MediaWiki (namespace = 8)
    print("\n[*] Сканирование пространства MediaWiki: (JS-скрипты)...")
    for page in site.allpages(namespace=8, filterredir="nonredirects"):
        rel_name = page.name.split(":", 1)[-1]
        if not rel_name.endswith(".js"):
            continue

        content = page.text().strip()
        file_path = SCRIPTS_DIR / rel_name
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content + "\n")

        dump_chunks.append(
            f"================================================\n"
            f"FILE: src/local/wikicorporate/scripts/{rel_name}\n"
            f"================================================\n"
            f"{content}\n\n"
        )
        js_count += 1
        print(f"  [+] JS: MediaWiki:{rel_name} -> {file_path.relative_to(REPO_ROOT)}")

    # 2. Выгружаем все Lua-модули из пространства Модуль (namespace = 828)
    print("\n[*] Сканирование пространства Модуль: (Lua-модули)...")
    for page in site.allpages(namespace=828, filterredir="nonredirects"):
        rel_name = page.name.split(":", 1)[-1]
        if rel_name.endswith("/doc"):
            continue

        content = page.text().strip()
        file_name = rel_name if rel_name.endswith(".json") else f"{rel_name}.lua"
        file_path = MODULES_DIR / file_name
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content + "\n")

        dump_chunks.append(
            f"================================================\n"
            f"FILE: src/local/wikicorporate/modules/{file_name}\n"
            f"================================================\n"
            f"{content}\n\n"
        )
        lua_count += 1
        print(f"  [+] Lua: Модуль:{rel_name} -> {file_path.relative_to(REPO_ROOT)}")

    with open(DUMP_FILE, "w", encoding="utf-8", newline="\n") as df:
        df.write("\n".join(dump_chunks))

    print(f"\n[✅] Готово! Выгружено JS-скриптов: {js_count}, Lua-модулей: {lua_count}")
    print(f"[📄] Сформирован единый дамп: {DUMP_FILE.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    pull_all()
