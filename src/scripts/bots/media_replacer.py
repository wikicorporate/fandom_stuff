import os
import re
import time
import mwclient
from mwclient.errors import APIError

# Настройки проектов
PROJECTS = {
    "Hazbin Hotel": {
        "domain": "hazbinhotel.fandom.com",
        "path": "/ru/",
        "all_pages": True  # Флаг полного сканирования вики
    },
    "Zoophobia": {
        "domain": "zoophobia.fandom.com",
        "path": "/ru/",
        "all_pages": True
    },
    "Returnal": {
        "domain": "returnal.fandom.com",
        "path": "/ru/",
        "all_pages": True
    },
    "Helltaker": {
        "domain": "helltaker.fandom.com",
        "path": "/ru/",
        "all_pages": True
    },
    "OneShot": {
        "domain": "oneshot.fandom.com",
        "path": "/ru/",
        "all_pages": True
    }
}

# Полный список правил замены (от сложных к простым)
REPLACEMENTS = [
    # === YOUTUBE ===
    (r'\[https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_\-]+)(?:[&?]t=)(\d+)s?\s+([^\]]+)\]', r'{{Медиа|YOUTUBE|\1|\2|\3}}'),
    (r'\[https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_\-]+)[^\s\]]*\s+([^\]]+)\]', r'{{Медиа|YOUTUBE|\1|\2}}'),
    (r'\[https?://(?:www\.)?youtube\.com/(@[a-zA-Z0-9_\-]+)[^\s\]]*\s+([^\]]+)\]', r'{{Медиа|YOUTUBE-HANDLE|\1|\2}}'),
    (r'\[https?://(?:www\.)?youtube\.com/channel/([a-zA-Z0-9_\-]+)[^\s\]]*\s+([^\]]+)\]', r'{{Медиа|YOUTUBE-CHANNEL|\1|\2}}'),
    (r'\[https?://(?:www\.)?youtube\.com/playlist\?list=([a-zA-Z0-9_\-]+)[^\s\]]*\s+([^\]]+)\]', r'{{Медиа|YOUTUBE-PLAYLIST|\1|\2}}'),

    # === МУЗЫКАЛЬНЫЕ СЕРВИСЫ ===
    (r'\[https?://open\.spotify\.com/([^\s\]]+)\s+([^\]]+)\]', r'{{Медиа|SPOTIFY|\1|\2}}'),
    (r'\[https?://music\.apple\.com/([^\s\]?]+)\?i=(\d+)\s+([^\]]+)\]', r'{{Медиа|APPLE-MUSIC|\1|\2|\3}}'),
    (r'\[https?://music\.apple\.com/([^\s\]?]+)\s+([^\]]+)\]', r'{{Медиа|APPLE-MUSIC|\1|\2}}'),
    (r'\[https?://(?:www\.)?soundcloud\.com/([^\s\]]+)\s+([^\]]+)\]', r'{{Медиа|SOUNDCLOUD|\1|\2}}'),
    (r'\[https?://music\.youtube\.com/watch\?v=([a-zA-Z0-9_\-]+)[^\s\]]*\s+([^\]]+)\]', r'{{Медиа|YT-MUSIC|\1|\2}}'),

    # === СОЦСЕТИ И БЛОГИ ===
    (r'\[https?://(?:www\.)?(?:twitter|x)\.com/([^\s\]]+)\s+([^\]]+)\]', r'{{Медиа|TWITTER|\1|\2}}'),
    (r'\[https?://(?:www\.)?t\.me/([^\s\]]+)\s+([^\]]+)\]', r'{{Медиа|TELEGRAM|\1|\2}}'),
    (r'\[https?://(?:www\.)?instagram\.com/([^\s\]]+)\s+([^\]]+)\]', r'{{Медиа|INSTAGRAM|\1|\2}}'),
    (r'\[https?://(?:www\.)?tiktok\.com/([^\s\]]+)\s+([^\]]+)\]', r'{{Медиа|TIKTOK|\1|\2}}'),
    (r'\[https?://([a-zA-Z0-9_\-]+)\.tumblr\.com/post/([^\s\]]+)\s+([^\]]+)\]', r'{{Медиа|TUMBLR|\1|\2|\3}}'),
    (r'\[https?://([a-zA-Z0-9_\-]+)\.tumblr\.com/?\s+([^\]]+)\]', r'{{Медиа|TUMBLR|\1|\2}}'),
    (r'\[https?://(?:www\.)?facebook\.com/([^\s\]]+)\s+([^\]]+)\]', r'{{Медиа|FACEBOOK|\1|\2}}'),
    (r'\[https?://(?:www\.)?reddit\.com/([^\s\]]+)\s+([^\]]+)\]', r'{{Медиа|REDDIT|\1|\2}}'),
    (r'\[https?://bsky\.app/profile/([^\s\]]+)\s+([^\]]+)\]', r'{{Медиа|BLUESKY|\1|\2}}'),

    # === ТВОРЧЕСТВО, ДОКУМЕНТЫ И ИГРЫ ===
    (r'\[https?://(?:www\.)?patreon\.com/([^\s\]]+)\s+([^\]]+)\]', r'{{Медиа|PATREON|\1|\2}}'),
    (r'\[https?://(?:www\.)?deviantart\.com/([^\s\]]+)\s+([^\]]+)\]', r'{{Медиа|DEVIANTART|\1|\2}}'),
    (r'\[https?://docs\.google\.com/document/d/([^\/\s\]]+)[^\s\]]*\s+([^\]]+)\]', r'{{Медиа|G-DOCS|\1|\2}}'),
    (r'\[https?://docs\.google\.com/spreadsheets/(?:u/\d+/)?d/([^\/\s\]]+)[^\s\]]*\s+([^\]]+)\]', r'{{Медиа|G-TABLES|\1|\2}}'),
    (r'\[https?://(?:www\.)?imdb\.com/name/([^\/\s\]]+)[^\s\]]*\s+([^\]]+)\]', r'{{Медиа|IMDB|\1|\2}}'),
    (r'\[https?://(?:www\.)?imgur\.com/([^\s\]]+)\s+([^\]]+)\]', r'{{Медиа|IMGUR|\1|\2}}'),
    (r'\[https?://store\.steampowered\.com/([^\s\]]+)\s+([^\]]+)\]', r'{{Медиа|STEAM-STORE|\1|\2}}'),
    (r'\[https?://steamcommunity\.com/([^\s\]]+)\s+([^\]]+)\]', r'{{Медиа|STEAM-COMMUNITY|\1|\2}}'),

    # === АРХИВЫ ===
    (r'\[https?://web\.archive\.org/web/((?!https?://www\.youtube\.com/watch)[^\s\]]+)\s+([^\]]+)\](?:\s*\(архивировано\))?', r'{{Медиа|WEB-ARCHIVE|\1|\2}}'),
    (r'\[https?://web\.archive\.org/web/https?://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_\-]+)\s+([^\]]+)\](?:\s*\(архивировано\))?', r'{{Медиа|WEB-ARCHIVE-VIDEO|\1|\2}}')
]

def replace_media_links(text):
    new_text = text
    for pattern, replacement in REPLACEMENTS:
        new_text = re.sub(pattern, replacement, new_text, flags=re.IGNORECASE)
    return new_text

def main():
    username = os.environ.get('WIKI_USERNAME')
    password = os.environ.get('WIKI_PASSWORD')
    
    if not username or not password:
        print("[-] Ошибка: Не найдены BotPasswords в секретах GitHub!")
        return

    for project_name, config in PROJECTS.items():
        if not config.get("all_pages"):
            continue
            
        print(f"\n[=== Запуск глобального сканирования для: {project_name} ===]")
        site = mwclient.Site(config["domain"], path=config["path"])
        
        try:
            site.login(username, password)
        except Exception as e:
            print(f"[-] Ошибка авторизации: {e}")
            continue
        
        # site.allpages(namespace=0) перебирает только обычные статьи
        for page in site.allpages(namespace=0):
            title = page.name
            
            original_text = page.text()
            new_text = replace_media_links(original_text)
            
            if original_text != new_text:
                print(f"[!] Форматирую ссылки в статье: {title}")
                
                # Блок безопасного сохранения с защитой от API лимитов
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        page.save(new_text, summary="Стандартизация внешних ссылок")
                        time.sleep(5)  # Базовая пауза для обхода антиспама
                        break  # Успешно сохранили — выходим из цикла попыток
                        
                    except APIError as e:
                        if e.code == 'ratelimited':
                            wait_time = 30 * (attempt + 1)
                            print(f"    [!] Лимит API (ratelimited). Ждём {wait_time} секунд...")
                            time.sleep(wait_time)
                        else:
                            print(f"    [-] Ошибка API при сохранении {title}: {e}")
                            break
                    except Exception as e:
                        print(f"    [-] Неизвестная ошибка при сохранении {title}: {e}")
                        break
                else:
                    print(f"    [-] Не удалось сохранить {title} после {max_retries} попыток.")

if __name__ == "__main__":
    main()
