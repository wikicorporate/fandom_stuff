import re
import sys
from pathlib import Path
from typing import Callable, Dict, List, Pattern, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.wiki_client import connect_site, get_credentials, load_projects, safe_save

# Карта старых коротких алиасов из блока обратной совместимости Модуль:Медиа/Данные
LEGACY_MEDIA_ALIASES: Dict[str, str] = {
    "V": "YOUTUBE",
    "P": "YOUTUBE-PLAYLIST",
    "C": "YOUTUBE-CHANNEL",
    "T": "TWITTER",
    "X": "TWITTER",
    "F": "FACEBOOK",
    "I": "INSTAGRAM",
    "S": "SPOTIFY",
    "AM": "APPLE-MUSIC",
    "APPLEMUSIC": "APPLE-MUSIC",
    "W": "WEB-ARCHIVE",
    "WV": "WEB-ARCHIVE-VIDEO",
    "GD": "G-DOCS",
    "GOOGLEDOCS": "G-DOCS",
    "GDT": "G-TABLES",
    "GOOGLEDOCSTABLE": "G-TABLES",
    "PTRN": "PATREON",
    "IB": "IMDB",
    "TR": "TUMBLR",
    "TUMBLER": "TUMBLR",
    "TT": "TIKTOK",
    "YM": "YT-MUSIC",
    "BS": "BLUESKY",
    "DART": "DEVIANTART",
    "SCLOUD": "SOUNDCLOUD",
    "TG": "TELEGRAM",
    "STEAMCOM": "STEAM-COMMUNITY",
    "STEAMSTORE": "STEAM-STORE",
}

# Регулярное выражение для поиска старых вызовов {{Медиа|АЛИАС|...}}
LEGACY_TEMPLATE_RE = re.compile(
    r"(\{\{\s*[Мм]едиа\s*\|\s*)([a-zA-Z\-]+)(\s*(?:\||\}\}))"
)

# Полный список правил замены сырых внешних ссылок: (паттерн, имя сервиса, количество аргументов)
RAW_RULES: List[Tuple[str, str, int]] = [
    # === YOUTUBE ===
    (
        r"\[https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_\-]+)(?:[&?]t=)(\d+)s?[^\s\]]*\s+([^\]]+)\]",
        "YOUTUBE",
        3,
    ),
    (
        r"\[https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_\-]+)[^\s\]]*\s+([^\]]+)\]",
        "YOUTUBE",
        2,
    ),
    (
        r"\[https?://(?:www\.)?youtube\.com/(@[a-zA-Z0-9_\-.]+)[^\s\]]*\s+([^\]]+)\]",
        "YOUTUBE-HANDLE",
        2,
    ),
    (
        r"\[https?://(?:www\.)?youtube\.com/channel/([a-zA-Z0-9_\-]+)[^\s\]]*\s+([^\]]+)\]",
        "YOUTUBE-CHANNEL",
        2,
    ),
    (
        r"\[https?://(?:www\.)?youtube\.com/playlist\?list=([a-zA-Z0-9_\-]+)[^\s\]]*\s+([^\]]+)\]",
        "YOUTUBE-PLAYLIST",
        2,
    ),
    # === МУЗЫКАЛЬНЫЕ СЕРВИСЫ ===
    (r"\[https?://open\.spotify\.com/([^\s\]]+)\s+([^\]]+)\]", "SPOTIFY", 2),
    (r"\[https?://music\.apple\.com/([^\s\]?]+)\?i=(\d+)[^\s\]]*\s+([^\]]+)\]", "APPLE-MUSIC", 3),
    (r"\[https?://music\.apple\.com/([^\s\]?]+)\s+([^\]]+)\]", "APPLE-MUSIC", 2),
    (r"\[https?://(?:www\.)?soundcloud\.com/([^\s\]]+)\s+([^\]]+)\]", "SOUNDCLOUD", 2),
    (r"\[https?://music\.youtube\.com/watch\?v=([a-zA-Z0-9_\-]+)[^\s\]]*\s+([^\]]+)\]", "YT-MUSIC", 2),
    # === СОЦСЕТИ И БЛОГИ ===
    (r"\[https?://(?:www\.)?(?:twitter|x)\.com/([^\s\]]+)\s+([^\]]+)\]", "TWITTER", 2),
    (r"\[https?://(?:www\.)?t\.me/([^\s\]]+)\s+([^\]]+)\]", "TELEGRAM", 2),
    (r"\[https?://(?:www\.)?instagram\.com/([^\s\]]+)\s+([^\]]+)\]", "INSTAGRAM", 2),
    (r"\[https?://(?:www\.)?tiktok\.com/([^\s\]]+)\s+([^\]]+)\]", "TIKTOK", 2),
    (r"\[https?://([a-zA-Z0-9_\-]+)\.tumblr\.com/post/([^\s\]]+)\s+([^\]]+)\]", "TUMBLR", 3),
    (r"\[https?://([a-zA-Z0-9_\-]+)\.tumblr\.com/?\s+([^\]]+)\]", "TUMBLR", 2),
    (r"\[https?://(?:www\.)?facebook\.com/([^\s\]]+)\s+([^\]]+)\]", "FACEBOOK", 2),
    (r"\[https?://(?:www\.)?reddit\.com/([^\s\]]+)\s+([^\]]+)\]", "REDDIT", 2),
    (r"\[https?://bsky\.app/profile/([^\s\]]+)\s+([^\]]+)\]", "BLUESKY", 2),
    # === ТВОРЧЕСТВО, ДОКУМЕНТЫ И ИГРЫ ===
    (r"\[https?://(?:www\.)?patreon\.com/([^\s\]]+)\s+([^\]]+)\]", "PATREON", 2),
    (r"\[https?://(?:www\.)?deviantart\.com/([^\s\]]+)\s+([^\]]+)\]", "DEVIANTART", 2),
    (r"\[https?://docs\.google\.com/document/d/([^/\s\]]+)[^\s\]]*\s+([^\]]+)\]", "G-DOCS", 2),
    (
        r"\[https?://docs\.google\.com/spreadsheets/(?:u/\d+/)?d/([^/\s\]]+)[^\s\]]*\s+([^\]]+)\]",
        "G-TABLES",
        2,
    ),
    (r"\[https?://(?:www\.)?imdb\.com/name/([^/\s\]]+)[^\s\]]*\s+([^\]]+)\]", "IMDB", 2),
    (r"\[https?://(?:www\.)?imgur\.com/([^\s\]]+)\s+([^\]]+)\]", "IMGUR", 2),
    (r"\[https?://store\.steampowered\.com/([^\s\]]+)\s+([^\]]+)\]", "STEAM-STORE", 2),
    (r"\[https?://steamcommunity\.com/([^\s\]]+)\s+([^\]]+)\]", "STEAM-COMMUNITY", 2),
    # === АРХИВЫ ===
    (
        r"\[https?://web\.archive\.org/web/https?://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_\-]+)\s+([^\]]+)\](?:\s*\(архивировано\))?",
        "WEB-ARCHIVE-VIDEO",
        2,
    ),
    (
        r"\[https?://web\.archive\.org/web/((?!https?://(?:www\.)?youtube\.com/watch)[^\s\]]+)\s+([^\]]+)\](?:\s*\(архивировано\))?",
        "WEB-ARCHIVE",
        2,
    ),
]

COMPILED_RULES: List[Tuple[Pattern[str], str, int]] = [
    (re.compile(pat, re.IGNORECASE), service, arg_count)
    for pat, service, arg_count in RAW_RULES
]

PROTECTED_TAG_RE = re.compile(
    r"(<!--[\s\S]*?-->|<(?:nowiki|pre|code|syntaxhighlight)\b[^>]*>[\s\S]*?</(?:nowiki|pre|code|syntaxhighlight)>)",
    re.IGNORECASE,
)


def _make_replacer(service: str, arg_count: int) -> Callable[[re.Match[str]], str]:
    def _repl(match: re.Match[str]) -> str:
        params = [match.group(i).strip() for i in range(1, arg_count)]
        label = match.group(arg_count).strip().replace("|", "{{!}}")
        joined = "|".join(params + [label])
        return f"{{{{Медиа|{service}|{joined}}}}}"

    return _repl


def _upgrade_legacy_alias(match: re.Match[str]) -> str:
    prefix, raw_key, suffix = match.group(1), match.group(2), match.group(3)
    upper_key = raw_key.upper()
    canonical = LEGACY_MEDIA_ALIASES.get(upper_key, upper_key)
    return f"{prefix}{canonical}{suffix}"


def replace_media_links(text: str) -> str:
    protected: Dict[str, str] = {}
    counter = 0

    def _mask(match: re.Match[str]) -> str:
        nonlocal counter
        key = f"__MEDIA_PROTECTED_{counter}__"
        protected[key] = match.group(0)
        counter += 1
        return key

    working = PROTECTED_TAG_RE.sub(_mask, text)

    # 1. Заменяем сырые внешние ссылки на {{Медиа|...}}
    for pattern, service, arg_count in COMPILED_RULES:
        working = pattern.sub(_make_replacer(service, arg_count), working)

    # 2. Заменяем старые короткие алиасы в {{Медиа|V|...}} на полные названия сервисов
    working = LEGACY_TEMPLATE_RE.sub(_upgrade_legacy_alias, working)

    for key, original in reversed(list(protected.items())):
        working = working.replace(key, original)

    return working


def main() -> None:
    username, password = get_credentials(prefer_bot=True)
    if not username or not password:
        print("[-] Ошибка: Не найдены учётные данные бота в переменных окружения!")
        raise SystemExit(1)

    projects = load_projects()

    for project_name, config in projects.items():
        if not config.get("all_pages"):
            continue

        print(f"\n[=== Запуск сканирования медиа-ссылок и алиасов для: {project_name} ===]")
        site = connect_site(
            config["domain"],
            path=config.get("path", "/ru/"),
            username=username,
            password=password,
        )
        if not site:
            continue

        for page in site.allpages(namespace=0, filterredir="nonredirects"):
            title = page.name
            try:
                original_text = page.text()
            except Exception as e:
                print(f"[-] Ошибка чтения {title}: {e}")
                continue

            new_text = replace_media_links(original_text)
            if original_text != new_text:
                print(f"[!] Обновлены медиа-ссылки в статье: {title}")
                safe_save(
                    page,
                    new_text,
                    summary="Стандартизация внешних ссылок и параметров шаблона Медиа",
                    bot=True,
                    minor=True,
                    sleep_after=4.0,
                )


if __name__ == "__main__":
    main()
