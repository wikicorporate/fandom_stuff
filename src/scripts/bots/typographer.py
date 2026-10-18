import re
import sys
from pathlib import Path
from typing import Dict
import mwparserfromhell

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.wiki_client import connect_site, get_credentials, load_projects, safe_save

SKIP_LINK_PREFIXES = (
    "file:",
    "файл:",
    "image:",
    "изображение:",
    "category:",
    "категория:",
)

QUOTES_REGEX = re.compile(r'(^|[\s(\[-|>])"([^"\n]+)"(?=[.,!?\)\];:]|\s|-|<|$)')
DASH_REGEX = re.compile(r"(?<=\S) - (?=\S)")
MULTISPACE_REGEX = re.compile(r"[ \t]{2,}")
MEDIA_EXT_REGEX = re.compile(
    r"\.(?:jpg|jpeg|png|gif|webp|svg|ogg|mp3|flac|wav|mp4|woff|woff2|ttf)\b",
    re.IGNORECASE,
)


def _smart_quotes_repl(match: re.Match[str]) -> str:
    before, inside = match.group(1), match.group(2)
    if re.search(r"[а-яА-ЯёЁ]", inside):
        return f"{before}«{inside}»"
    return f'{before}"{inside}"'


def _format_plain_text(val: str) -> str:
    val = QUOTES_REGEX.sub(_smart_quotes_repl, val)
    lines = val.split("\n")
    new_lines = []

    for line in lines:
        if (
            MEDIA_EXT_REGEX.search(line)
            or re.match(r"^\s*(?:File|Файл|Image|Изображение):", line, re.IGNORECASE)
            or "http://" in line
            or "https://" in line
        ):
            new_lines.append(line)
        else:
            line = DASH_REGEX.sub(" — ", line)
            line = MULTISPACE_REGEX.sub(" ", line)
            new_lines.append(line)

    return "\n".join(new_lines)


def clean_typography(text: str) -> str:
    protected_blocks: Dict[str, str] = {}
    parsed = mwparserfromhell.parse(text)
    counter = 0

    def protect_node(node: object, replacement_str: str) -> None:
        nonlocal counter
        marker = f"__PROTECTED_BLOCK_{counter}__"
        protected_blocks[marker] = replacement_str
        try:
            parsed.replace(node, marker)
            counter += 1
        except ValueError:
            pass

    # 1. Защищаем комментарии, шаблоны, HTML-теги и внешние ссылки
    for node in list(parsed.filter_comments(recursive=False)):
        protect_node(node, str(node))

    for node in list(parsed.filter_templates(recursive=False)):
        protect_node(node, str(node))

    for node in list(parsed.filter_tags(recursive=False)):
        protect_node(node, str(node))

    for node in list(parsed.filter_external_links(recursive=False)):
        protect_node(node, str(node))

    # 2. Обрабатываем вики-ссылки: защищаем целевой адрес (title),
    # а в обычных ссылках [[ Статья | Видимый текст ]] форматируем только видимый текст
    for wikilink in list(parsed.filter_wikilinks(recursive=False)):
        raw_title = str(wikilink.title).strip().lstrip(":").lower()
        if raw_title.startswith(SKIP_LINK_PREFIXES):
            protect_node(wikilink, str(wikilink))
            continue

        if wikilink.text is not None:
            cleaned_label = clean_typography(str(wikilink.text))
            wikilink.text = cleaned_label

        protect_node(wikilink, str(wikilink))

    # 3. Применяем типографику к оставшемуся чистому тексту статьи
    working_text = _format_plain_text(str(parsed))

    # 4. Возвращаем защищённые блоки в обратном порядке
    for marker, original_block in reversed(list(protected_blocks.items())):
        working_text = working_text.replace(marker, original_block)

    return working_text


def main() -> None:
    username, password = get_credentials(prefer_bot=True)
    if not username or not password:
        print("[-] Ошибка: Секреты логина/пароля бота не найдены в окружении!")
        raise SystemExit(1)

    projects = load_projects()

    for project_name, config in projects.items():
        if not config.get("all_pages"):
            continue

        print(f"\n[=== Типограф: {project_name} ===]")
        site = connect_site(
            config["domain"],
            path=config.get("path", "/ru/"),
            username=username,
            password=password,
        )
        if not site:
            continue

        print(f"[*] Успешная авторизация на {project_name}")

        for page in site.allpages(namespace=0, filterredir="nonredirects"):
            lower_name = page.name.lower()
            if lower_name.endswith((".json", ".css", ".js")):
                continue

            try:
                original = page.text()
                cleaned = clean_typography(original)

                if original != cleaned:
                    print(f"[!] Исправлена типографика: {page.name}")
                    safe_save(
                        page,
                        cleaned,
                        summary="Автоматическое исправление типографики",
                        bot=True,
                        minor=True,
                        sleep_after=3.0,
                    )
            except Exception as e:
                print(f"[-] Ошибка при обработке {page.name}: {e}")


if __name__ == "__main__":
    main()
