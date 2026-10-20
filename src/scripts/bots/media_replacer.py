import re
import sys
from pathlib import Path
from typing import Callable, Dict, List, Pattern, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.wiki_client import connect_site, get_credentials, load_projects, safe_save

# Каноничные правила замены внешних ссылок: (паттерн, ключ в Модуль:Медиа/Данные, число аргументов)
RAW_RULES: List[Tuple[str, str, int]] = [
    # === 1. АРХИВЫ (проверяются первыми, так как внутри URL содержатся другие домены) ===
    (
        r"\[https?://web\.archive\.org/web/(\d+)/https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_\-]+)[^\s\]]*\s+([^\]]+)\](?:\s*\(архивировано\))?",
        "WEB-ARCHIVE-VIDEO",
        3,
    ),
    (
        r"\[https?://web\.archive\.org/web/(?:\*/)?https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_\-]+)[^\s\]]*\s+([^\]]+)\](?:\s*\(архивировано\))?",
        "WEB-ARCHIVE-VIDEO",
        2,
    ),
    (
        r"\[https?://web\.archive\.org/web/((?!(?:\d+/|\*/)?https?://(?:www\.)?(?:youtube\.com/watch|youtu\.be/))[^\s\]]+)\s+([^\]]+)\](?:\s*\(архивировано\))?",
        "WEB-ARCHIVE",
        2,
    ),
    (
        r"\[https?://archive\.(?:ph|is|today|fo|li|md|vn)/([^\s\]]+)\s+([^\]]+)\](?:\s*\(архивировано\))?",
        "ARCHIVE-TODAY",
        2,
    ),

    # === 2. ВИДЕО И СТРИМИНГ ===
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
        r"\[https?://(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_\-]+)[^\s\]]*\s+([^\]]+)\]",
        "YOUTUBE-SHORTS",
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
    (
        r"\[https?://(?:www\.)?twitch\.tv/videos/(\d+)[^\s\]]*\s+([^\]]+)\]",
        "TWITCH-VIDEO",
        2,
    ),
    (
        r"\[https?://(?:www\.)?twitch\.tv/((?!videos/)[^\s\]]+)\s+([^\]]+)\]",
        "TWITCH",
        2,
    ),
    (
        r"\[https?://(?:www\.)?vimeo\.com/([^\s\]]+)\s+([^\]]+)\]",
        "VIMEO",
        2,
    ),
    (
        r"\[https?://(?:www\.)?primevideo\.com/detail/([^\s\]]+)\s+([^\]]+)\]",
        "PRIME-VIDEO",
        2,
    ),

    # === 3. МУЗЫКА И ТЕКСТЫ ПЕСЕН ===
    (
        r"\[https?://music\.youtube\.com/watch\?v=([a-zA-Z0-9_\-]+)[^\s\]]*\s+([^\]]+)\]",
        "YT-MUSIC",
        2,
    ),
    (
        r"\[https?://music\.apple\.com/([^\s\]?]+)\?i=(\d+)[^\s\]]*\s+([^\]]+)\]",
        "APPLE-MUSIC",
        3,
    ),
    (
        r"\[https?://music\.apple\.com/([^\s\]]+)\s+([^\]]+)\]",
        "APPLE-MUSIC",
        2,
    ),
    (
        r"\[https?://open\.spotify\.com/([^\s\]]+)\s+([^\]]+)\]",
        "SPOTIFY",
        2,
    ),
    (
        r"\[https?://(?:www\.)?soundcloud\.com/([^\s\]]+)\s+([^\]]+)\]",
        "SOUNDCLOUD",
        2,
    ),
    (
        r"\[https?://([a-zA-Z0-9_\-]+)\.bandcamp\.com/([^\s\]]+)\s+([^\]]+)\]",
        "BANDCAMP",
        3,
    ),
    (
        r"\[https?://([a-zA-Z0-9_\-]+)\.bandcamp\.com/?\s+([^\]]+)\]",
        "BANDCAMP",
        2,
    ),
    (
        r"\[https?://(?:www\.)?deezer\.com/([^\s\]]+)\s+([^\]]+)\]",
        "DEEZER",
        2,
    ),
    (
        r"\[https?://music\.yandex\.(?:ru|com)/([^\s\]]+)\s+([^\]]+)\]",
        "YANDEX-MUSIC",
        2,
    ),
    (
        r"\[https?://(?:www\.)?genius\.com/([^\s\]]+)\s+([^\]]+)\]",
        "GENIUS",
        2,
    ),

    # === 4. СОЦСЕТИ, МЕССЕНДЖЕРЫ И ВИЗИТКИ ===
    (
        r"\[https?://(?:www\.)?(?:twitter|x)\.com/([^\s\]]+)\s+([^\]]+)\]",
        "TWITTER",
        2,
    ),
    (
        r"\[https?://bsky\.app/profile/([^\s\]]+)\s+([^\]]+)\]",
        "BLUESKY",
        2,
    ),
    (
        r"\[https?://(?:www\.)?threads\.(?:net|com)/([^\s\]]+)\s+([^\]]+)\]",
        "THREADS",
        2,
    ),
    (
        r"\[https?://(?:www\.)?t\.me/([^\s\]]+)\s+([^\]]+)\]",
        "TELEGRAM",
        2,
    ),
    (
        r"\[https?://(?:www\.)?vk\.com/([^\s\]]+)\s+([^\]]+)\]",
        "VK",
        2,
    ),
    (
        r"\[https?://(?:www\.)?(?:discord\.gg|discord(?:app)?\.com/invite)/([^\s\]]+)\s+([^\]]+)\]",
        "DISCORD",
        2,
    ),
    (
        r"\[https?://(?:www\.)?instagram\.com/([^\s\]]+)\s+([^\]]+)\]",
        "INSTAGRAM",
        2,
    ),
    (
        r"\[https?://(?:www\.)?tiktok\.com/([^\s\]]+)\s+([^\]]+)\]",
        "TIKTOK",
        2,
    ),
    (
        r"\[https?://([a-zA-Z0-9_\-]+)\.tumblr\.com/post/([^\s\]]+)\s+([^\]]+)\]",
        "TUMBLR",
        3,
    ),
    (
        r"\[https?://([a-zA-Z0-9_\-]+)\.tumblr\.com/?\s+([^\]]+)\]",
        "TUMBLR",
        2,
    ),
    (
        r"\[https?://(?:www\.)?facebook\.com/([^\s\]]+)\s+([^\]]+)\]",
        "FACEBOOK",
        2,
    ),
    (
        r"\[https?://(?:www\.)?reddit\.com/([^\s\]]+)\s+([^\]]+)\]",
        "REDDIT",
        2,
    ),
    (
        r"\[https?://(?:www\.)?linktr\.ee/([^\s\]]+)\s+([^\]]+)\]",
        "LINKTREE",
        2,
    ),
    (
        r"\[https?://([a-zA-Z0-9_\-]+)\.carrd\.co/?\s+([^\]]+)\]",
        "CARRD",
        2,
    ),

    # === 5. АРТ, КРАУДФАНДИНГ И МЕРЧ ===
    (
        r"\[https?://(?:www\.)?artstation\.com/([^\s\]]+)\s+([^\]]+)\]",
        "ARTSTATION",
        2,
    ),
    (
        r"\[https?://(?:www\.)?deviantart\.com/([^\s\]]+)\s+([^\]]+)\]",
        "DEVIANTART",
        2,
    ),
    (
        r"\[https?://(?!www\.)([a-zA-Z0-9_\-]+)\.newgrounds\.com/([^\s\]]+)\s+([^\]]+)\]",
        "NEWGROUNDS",
        3,
    ),
    (
        r"\[https?://(?:www\.)?newgrounds\.com/([^\s\]]+)\s+([^\]]+)\]",
        "NEWGROUNDS",
        2,
    ),
    (
        r"\[https?://(?:www\.)?pixiv\.net/([^\s\]]+)\s+([^\]]+)\]",
        "PIXIV",
        2,
    ),
    (
        r"\[https?://(?:[a-z]{2}\.|www\.)?pinterest\.com/([^\s\]]+)\s+([^\]]+)\]",
        "PINTEREST",
        2,
    ),
    (
        r"\[https?://(?:www\.)?imgur\.com/([^\s\]]+)\s+([^\]]+)\]",
        "IMGUR",
        2,
    ),
    (
        r"\[https?://(?:www\.)?patreon\.com/([^\s\]]+)\s+([^\]]+)\]",
        "PATREON",
        2,
    ),
    (
        r"\[https?://(?:www\.)?ko-fi\.com/([^\s\]]+)\s+([^\]]+)\]",
        "KO-FI",
        2,
    ),
    (
        r"\[https?://(?:www\.)?boosty\.to/([^\s\]]+)\s+([^\]]+)\]",
        "BOOSTY",
        2,
    ),
    (
        r"\[https?://(?:www\.)?kickstarter\.com/projects/([^\s\]]+)\s+([^\]]+)\]",
        "KICKSTARTER",
        2,
    ),
    (
        r"\[https?://(?:www\.)?sharkrobot\.com/([^\s\]]+)\s+([^\]]+)\]",
        "SHARKROBOT",
        2,
    ),
    (
        r"\[https?://shop\.a24films\.com/([^\s\]]+)\s+([^\]]+)\]",
        "A24-SHOP",
        2,
    ),

    # === 6. КИНОБАЗЫ И АГРЕГАТОРЫ ===
    (
        r"\[https?://(?:www\.)?imdb\.com/name/([^/\s\]]+)[^\s\]]*\s+([^\]]+)\]",
        "IMDB",
        2,
    ),
    (
        r"\[https?://(?:www\.)?imdb\.com/title/([^/\s\]]+)[^\s\]]*\s+([^\]]+)\]",
        "IMDB-TITLE",
        2,
    ),
    (
        r"\[https?://(?:www\.)?rottentomatoes\.com/([^\s\]]+)\s+([^\]]+)\]",
        "ROTTEN-TOMATOES",
        2,
    ),
    (
        r"\[https?://(?:www\.)?metacritic\.com/([^\s\]]+)\s+([^\]]+)\]",
        "METACRITIC",
        2,
    ),

    # === 7. ИГРОВЫЕ ПЛАТФОРМЫ И МАГАЗИНЫ ===
    (
        r"\[https?://store\.steampowered\.com/([^\s\]]+)\s+([^\]]+)\]",
        "STEAM-STORE",
        2,
    ),
    (
        r"\[https?://steamcommunity\.com/([^\s\]]+)\s+([^\]]+)\]",
        "STEAM-COMMUNITY",
        2,
    ),
    (
        r"\[https?://steamdb\.info/([^\s\]]+)\s+([^\]]+)\]",
        "STEAMDB",
        2,
    ),
    (
        r"\[https?://([a-zA-Z0-9_\-]+)\.itch\.io/([^\s\]]+)\s+([^\]]+)\]",
        "ITCH-IO",
        3,
    ),
    (
        r"\[https?://([a-zA-Z0-9_\-]+)\.itch\.io/?\s+([^\]]+)\]",
        "ITCH-IO",
        2,
    ),
    (
        r"\[https?://store\.playstation\.com/([^\s\]]+)\s+([^\]]+)\]",
        "PLAYSTATION",
        2,
    ),
    (
        r"\[https?://store\.epicgames\.com/([^\s\]]+)\s+([^\]]+)\]",
        "EPIC-GAMES",
        2,
    ),
    (
        r"\[https?://(?:www\.)?gog\.com/([^\s\]]+)\s+([^\]]+)\]",
        "GOG",
        2,
    ),
    (
        r"\[https?://(?:www\.)?nintendo\.com/([^\s\]]+)\s+([^\]]+)\]",
        "NINTENDO",
        2,
    ),
    (
        r"\[https?://(?:www\.)?xbox\.com/([^\s\]]+)\s+([^\]]+)\]",
        "XBOX",
        2,
    ),

    # === 8. ДОКУМЕНТЫ, КОД И ПОИСК ===
    (
        r"\[https?://docs\.google\.com/document/d/([^/\s\]]+)[^\s\]]*\s+([^\]]+)\]",
        "G-DOCS",
        2,
    ),
    (
        r"\[https?://docs\.google\.com/spreadsheets/(?:u/\d+/)?d/([^/\s\]]+)[^\s\]]*\s+([^\]]+)\]",
        "G-TABLES",
        2,
    ),
    (
        r"\[https?://drive\.google\.com/([^\s\]]+)\s+([^\]]+)\]",
        "G-DRIVE",
        2,
    ),
    (
        r"\[https?://(?:www\.)?github\.com/([^\s\]]+)\s+([^\]]+)\]",
        "GITHUB",
        2,
    ),
    (
        r"\[https?://(?:www\.)?google\.com/search\?q=([^\s&\]]+)[^\s\]]*\s+([^\]]+)\]",
        "GOOGLE",
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
        params = [match.group(i).strip().rstrip("/") for i in range(1, arg_count)]
        label = match.group(arg_count).strip().replace("|", "{{!}}")
        joined = "|".join(params + [label])
        return f"{{{{Медиа|{service}|{joined}}}}}"

    return _repl


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

    for pattern, service, arg_count in COMPILED_RULES:
        working = pattern.sub(_make_replacer(service, arg_count), working)

    for key, original in reversed(list(protected.items())):
        working = working.replace(key, original)

    return working


def main() -> None:
    username, password = get_credentials(prefer_bot=False)
    if not username or not password:
        print("[-] Ошибка: Не найдены учётные данные в переменных окружения!")
        raise SystemExit(1)

    projects = load_projects()

    for project_name, config in projects.items():
        if not config.get("all_pages"):
            continue

        print(f"\n[=== Запуск сканирования внешних медиа-ссылок для: {project_name} ===]")
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
                print(f"[!] Сконвертированы медиа-ссылки в статье: {title}")
                safe_save(
                    page,
                    new_text,
                    summary="Автоматическая замена внешних ссылок на шаблон Медиа",
                    bot=True,
                    minor=True,
                    sleep_after=4.0,
                )


if __name__ == "__main__":
    main()
