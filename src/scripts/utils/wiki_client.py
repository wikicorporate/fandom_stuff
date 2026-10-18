import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import mwclient
from mwclient.errors import APIError
import requests

REPO_ROOT = Path(__file__).resolve().parents[3]
CONFIG_PATH = REPO_ROOT / "config.json"
USER_AGENT = "FandomStuffBot/2.0 (https://github.com/; MediaWiki/mwclient)"


def load_config() -> Dict[str, Any]:
    """Загружает единый config.json из корня монорепозитория."""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Конфигурационный файл не найден: {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_projects() -> Dict[str, Dict[str, Any]]:
    """Возвращает словарь проектов из config.json."""
    config = load_config()
    return config.get("projects", {})


def get_credentials(prefer_bot: bool = True) -> Tuple[Optional[str], Optional[str]]:
    """
    Возвращает (username, password) из переменных окружения.
    Если prefer_bot=True, приоритет отдаётся FANDOM_BOT_USERNAME, затем WIKI_USERNAME и FANDOM_USERNAME.
    """
    if prefer_bot:
        username = (
            os.environ.get("FANDOM_BOT_USERNAME")
            or os.environ.get("WIKI_USERNAME")
            or os.environ.get("FANDOM_USERNAME")
        )
        password = (
            os.environ.get("FANDOM_BOT_PASSWORD")
            or os.environ.get("WIKI_PASSWORD")
            or os.environ.get("FANDOM_PASSWORD")
        )
    else:
        username = (
            os.environ.get("FANDOM_USERNAME")
            or os.environ.get("WIKI_USERNAME")
            or os.environ.get("FANDOM_BOT_USERNAME")
        )
        password = (
            os.environ.get("FANDOM_PASSWORD")
            or os.environ.get("WIKI_PASSWORD")
            or os.environ.get("FANDOM_BOT_PASSWORD")
        )
    return username, password


def create_http_session() -> requests.Session:
    """Создаёт HTTP-сессию с корректным User-Agent для прямых запросов к API."""
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def connect_site(
    domain: str,
    path: str = "/ru/",
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> Optional[mwclient.Site]:
    """Подключается к вики на Fandom и выполняет авторизацию, если переданы учётные данные."""
    try:
        site = mwclient.Site(
            domain,
            path=path,
            clients_useragent=USER_AGENT,
            reqs={"timeout": 30},
        )
        if username and password:
            site.login(username, password)
        return site
    except Exception as e:
        print(f"[-] Ошибка подключения/авторизации на {domain}{path}: {e}")
        return None


def safe_save(
    page: mwclient.page.Page,
    new_text: str,
    summary: str,
    bot: bool = True,
    minor: bool = False,
    sleep_after: float = 3.0,
    max_retries: int = 3,
) -> bool:
    """Безопасное сохранение страницы с обработкой ratelimited, maxlag и сетевых ошибок."""
    for attempt in range(1, max_retries + 1):
        try:
            page.save(new_text, summary=summary, bot=bot, minor=minor)
            if sleep_after > 0:
                time.sleep(sleep_after)
            return True
        except APIError as e:
            if e.code in ("ratelimited", "maxlag") and attempt < max_retries:
                wait_time = 20 * attempt
                print(
                    f"    [!] Лимит API ({e.code}) при сохранении '{page.name}'. "
                    f"Ожидание {wait_time} сек. (попытка {attempt}/{max_retries})..."
                )
                time.sleep(wait_time)
            else:
                print(f"    [-] Ошибка API при сохранении '{page.name}': {e}")
                return False
        except Exception as e:
            if attempt < max_retries:
                wait_time = 10 * attempt
                print(
                    f"    [!] Сетевая ошибка при сохранении '{page.name}': {e}. "
                    f"Повтор через {wait_time} сек. ({attempt}/{max_retries})..."
                )
                time.sleep(wait_time)
            else:
                print(f"    [-] Не удалось сохранить '{page.name}': {e}")
                return False
    return False
