import sys
from pathlib import Path
from typing import Dict, Tuple
import mwclient
import mwparserfromhell

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.wiki_client import connect_site, get_credentials, load_projects, safe_save


def normalize_mw_title(raw_title: str) -> Tuple[str, str]:
    """
    Разделяет заголовок вики-ссылки на (Нормализованное_Имя_Статьи, Якорь).
    Учитывает пробелы, подчёркивания и регистр первой буквы по правилам MediaWiki.
    """
    cleaned = raw_title.strip()
    if "#" in cleaned:
        base, anchor = cleaned.split("#", 1)
        anchor_part = f"#{anchor.strip()}"
    else:
        base, anchor_part = cleaned, ""

    base = base.lstrip(":").replace("_", " ").strip()
    if not base:
        return "", anchor_part

    normalized = base[0].upper() + base[1:]
    return normalized, anchor_part


def fetch_redirect_map(site: mwclient.Site) -> Dict[str, str]:
    """Собирает полную карту перенаправлений основного пространства за минимальное число API-запросов."""
    redirect_map: Dict[str, str] = {}
    params = {
        "generator": "allpages",
        "gapnamespace": 0,
        "gapfilterredir": "redirects",
        "gaplimit": "max",
        "redirects": "1",
    }

    while True:
        res = site.api("query", **params)
        query_data = res.get("query", {})
        for redir in query_data.get("redirects", []):
            src = redir.get("from")
            dst = redir.get("to")
            frag = redir.get("tofragment")
            if src and dst:
                redirect_map[src] = f"{dst}#{frag}" if frag else dst

        if "continue" in res:
            params.update(res["continue"])
        else:
            break

    return redirect_map


def main() -> None:
    username, password = get_credentials(prefer_bot=True)
    if not username or not password:
        print("[-] Ошибка: Секреты логина/пароля бота не найдены в окружении!")
        raise SystemExit(1)

    projects = load_projects()

    for project_name, config in projects.items():
        if not config.get("all_pages"):
            continue

        print(f"\n[=== Резолвер редиректов: {project_name} ===]")
        site = connect_site(
            config["domain"],
            path=config.get("path", "/ru/"),
            username=username,
            password=password,
        )
        if not site:
            continue

        print("[+] Успешная авторизация. Составление карты перенаправлений...")
        try:
            redirect_map = fetch_redirect_map(site)
        except Exception as e:
            print(f"[-] Ошибка при получении карты редиректов на {project_name}: {e}")
            continue

        print(f"[+] Найдено редиректов: {len(redirect_map)}")
        if not redirect_map:
            continue

        print("[*] Сканирование статей на наличие ссылок-редиректов...")
        for page in site.allpages(namespace=0, filterredir="nonredirects"):
            try:
                text = page.text()
            except Exception as e:
                print(f"[-] Ошибка чтения статьи {page.name}: {e}")
                continue

            parsed = mwparserfromhell.parse(text)
            changed = False

            for wikilink in parsed.filter_wikilinks():
                raw_link_title = str(wikilink.title).strip()
                if not raw_link_title or raw_link_title.startswith("#"):
                    continue

                norm_title, anchor = normalize_mw_title(raw_link_title)
                if norm_title in redirect_map:
                    real_target = redirect_map[norm_title]
                    # Если у ссылки был собственный якорь, а редирект ведёт на статью целиком — сохраняем якорь
                    if anchor and "#" not in real_target:
                        final_target = f"{real_target}{anchor}"
                    else:
                        final_target = real_target

                    if not wikilink.text:
                        display_label = raw_link_title.replace("_", " ").strip()
                        if display_label != final_target:
                            wikilink.text = display_label

                    wikilink.title = final_target
                    changed = True

            if changed:
                new_text = str(parsed)
                if new_text != text:
                    print(f"[!] Обновлены ссылки в статье: {page.name}")
                    safe_save(
                        page,
                        new_text,
                        summary="Автоматическая замена перенаправлений на прямые ссылки",
                        bot=True,
                        minor=True,
                        sleep_after=3.0,
                    )


if __name__ == "__main__":
    main()
