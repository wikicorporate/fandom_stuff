import argparse
import difflib
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import mwclient
import mwparserfromhell

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.wiki_client import connect_site, get_credentials, safe_save

EN_DOMAIN = "hazbinhotel.fandom.com"
EN_PATH = "/"

RU_DOMAIN = "hazbinhotel.fandom.com"
RU_PATH = "/ru/"

CATEGORIES_TO_CHECK = [
    "Категория:Галереи Отеля Хазбин",
    "Категория:Галереи Адского Босса",
]

# Разделы, которые полностью сохраняются из русской версии вместе со своей структурой
PRESERVE_RU_SECTIONS = {
    "Скриншоты",
    "Анимация",
    "Раскадровки",
    "Черновики",
}

HEADERS_MAP = {
    "Screenshots": "Скриншоты",
    "Animations": "Анимация",
    "Official Artwork": "Официальное творчество",
    "Merchandise": "Мерчендайз",
    "Concept Art": "Концепт-арты",
    "Miscellaneous": "Разное",
    "Promotional": "Промо-арты",
    "Promotional Artwork": "Промо-арты",
    "Promotional artwork": "Промо-арты",
    "Promotional Art": "Промо-арты",
    "Design": "Дизайн",
    "Designs": "Дизайн",
    "Comics": "Комиксы",
    "Others": "Прочее",
    "Other": "Другое",
    "Clothing": "Одежда",
    "Outfits": "Одежда",
    "Apparel": "Одежда",
    "Official art": "Официальные арты",
    "Staff Artwork": "Официальные арты",
    "Signed prints": "Подписанные принты",
    "Signed Prints": "Подписанные принты",
    "Signing prints": "Подписанные принты",
    "Signing Prints": "Подписанные принты",
    "T-shirts, hoodies, and sweaters": "Футболки, толстовки и свитеры",
    "T-Shirts, Hoodies, and Sweaters": "Футболки, толстовки и свитеры",
    "T-Shirts, Sweatshirts, and Hoodies": "Футболки, толстовки и свитеры",
    "Hoodies, T-Shirts and Sweaters": "Толстовки, футболки и свитеры",
    "Pins": "Значки",
    "Keychains": "Брелоки",
    "Figures": "Фигурки",
    "Standees": "Стенды",
    "Acrylic Standees": "Акриловые статуэтки",
    "Plushies": "Плюшевые игрушки",
    "Posters": "Постеры",
    "Posters and prints": "Постеры",
    "Posters and Prints": "Постеры",
    "Cards": "Коллекционные карты",
    "Promo Cards": "Коллекционные карты",
    "Trading Cards": "Коллекционные карты",
    "Pajama Pants": "Пижамные штаны",
    "Loungewear Pants": "Пижамные штаны",
    "Pajama Pants and Shorts": "Пижамные штаны и шорты",
    "Pajama Pants, and Shorts": "Пижамные штаны и шорты",
    "Socks": "Носки",
    "Notebooks and Sketchbooks": "Блокноты и скетчбуки",
    "Lanyards": "Ремни",
    "Jewelry": "Браслеты",
    "Nintendo Switch Cases": "Чехлы для Nintendo Switch",
    "Puzzles and Games": "Пазлы и игры",
    "Playmats": "Игровые коврики",
    "Playmates": "Игровые коврики",
    "Mugs and Glasses": "Кружки и стаканы",
    "Mugs & Glasses": "Кружки и стаканы",
    "Mugs and Cups": "Кружки и чашки",
    "Mugs": "Кружки",
    "Backpacks": "Рюкзаки",
    "Backpacks and Bags": "Рюкзаки и сумки",
    "Bags": "Сумки",
    "Banners": "Баннеры",
    "Wallets": "Кошельки",
    "Stickers": "Стикеры",
    "Model Sheets": "Модели",
    "Storyboards": "Раскадровки",
    "Beatboards": "Черновики",
    "Titlecards": "Заставки эпизодов",
    "Episode Artwork": "Арты в эпизоде",
    "Voxtagram Posts": "Посты в [[Вокстаграм]]е",
    "Voxtagram posts": "Посты в [[Вокстаграм]]е",
    "[[Voxtagram]] Posts": "Посты в [[Вокстаграм]]е",
    "[[Voxtagram]] posts": "Посты в [[Вокстаграм]]е",
    "Livestreams": "Трансляции",
    "YouTooz": "Фигурки YouTooz",
    "Youtooz": "Фигурки YouTooz",
    "Pinboards": "Доски для булавок",
    "Skateboards": "Скейтборды",
    "Hats and Beanies": "Головные уборы",
    "Hats": "Головные уборы",
    "Hats and Outerwear": "Головные уборы и верхняя одежда",
    "Scarves": "Шарфы",
    "Slipmat": "Слипматы",
    "Games": "Игры",
    "Pilot": "Пилотные эпизоды",
    "Season 1": "Первый сезон",
    "Season 2": "Второй сезон",
    "Helluva Shorts": "Короткометражные эпизоды",
}

HEADERS_MAP_LOWER = {k.lower(): v for k, v in HEADERS_MAP.items()}

EN_JUNK_TEMPLATES = {
    "hazbingallery",
    "helluvagallery",
    "main",
    "gallerytabber",
    "character gallery navbox",
}


def clean_fname(name: str) -> str:
    """Вырезает префиксы File:, Файл: перед вставкой в галерею."""
    return re.sub(r"^(?:File|Файл|Image|Изображение)\s*:\s*", "", name, flags=re.IGNORECASE).strip()


def normalize_file_key(name: str) -> str:
    """Нормализует имя файла для сопоставления между RU и EN галереями."""
    cleaned = clean_fname(name).replace("_", " ").strip()
    if not cleaned:
        return ""
    return cleaned[0].upper() + cleaned[1:]


def clean_header_title(title: str) -> str:
    """Очищает заголовок от разметки и ссылок для поиска в словаре."""
    t = re.sub(r"'''?", "", title)
    t = re.sub(r"</?[^>]+>", "", t)
    t = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", t)
    return t.strip()


def translate_header_name(raw_title: str) -> str:
    clean_title = clean_header_title(raw_title)
    if clean_title in HEADERS_MAP:
        return HEADERS_MAP[clean_title]
    if clean_title.lower() in HEADERS_MAP_LOWER:
        return HEADERS_MAP_LOWER[clean_title.lower()]
    return f"TODO: {clean_title}"


def extract_ru_captions(ru_text: str) -> Dict[str, str]:
    """
    Извлекает все существующие подписи и параметры к файлам из русских шаблонов {{Галерея|...}},
    чтобы не затирать русский перевод при синхронизации с английской вики.
    """
    captions: Dict[str, str] = {}
    parsed = mwparserfromhell.parse(ru_text)

    for tpl in parsed.filter_templates():
        tpl_name = str(tpl.name).strip().lower()
        if tpl_name not in ("галерея", "gallery"):
            continue

        # Собираем все позиционные параметры обратно в текст строк галереи
        raw_lines = "|".join(str(p.value) for p in tpl.params if not p.showkey).split("\n")
        for line in raw_lines:
            line = line.strip()
            if not line or line == "|":
                continue
            parts = line.split("|", 1)
            fkey = normalize_file_key(parts[0])
            if fkey and len(parts) > 1:
                cap = parts[1].strip()
                if cap:
                    captions[fkey] = cap

    return captions


def clean_en_junk(text: str) -> str:
    """Безопасно удаляет английские навигационные шаблоны (включая вложенные), категории и интервики."""
    parsed = mwparserfromhell.parse(text)
    for tpl in list(parsed.filter_templates(recursive=True)):
        t_name = str(tpl.name).strip().lower()
        if t_name in EN_JUNK_TEMPLATES:
            try:
                parsed.remove(tpl)
            except ValueError:
                pass

    cleaned = str(parsed)
    cleaned = re.sub(r"\[\[\s*Category\s*:[^\]]+\]\]\n?", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\[\[[a-z\-]{2,10}:[^\]]+\]\]\n?", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def translate_headings(text: str) -> str:
    """Переводит все уровни заголовков (==, ===, ====) с помощью словаря."""
    def repl(match: re.Match[str]) -> str:
        level = match.group(1)
        ru_title = translate_header_name(match.group(2))
        return f"{level} {ru_title} {level}"

    return re.sub(r"^(={2,6})\s*(.*?)\s*\1$", repl, text, flags=re.MULTILINE)


def convert_galleries(text: str, ru_captions: Dict[str, str]) -> str:
    """
    Конвертирует <gallery> в {{Галерея|...}}, сохраняя существующие русские подписи
    для уже переведённых файлов.
    """
    def gal_repl(match: re.Match[str]) -> str:
        inner = match.group(1).strip()
        lines = inner.split("\n")
        res = ["{{Галерея|"]

        for line in lines:
            line = line.strip()
            if not line or line.startswith("<!--"):
                continue

            line = re.sub(r"\|\s*alt\s*=[^|]*", "", line, flags=re.IGNORECASE)
            parts = line.split("|", 1)
            fname = clean_fname(parts[0])
            if not fname:
                continue

            fkey = normalize_file_key(fname)
            if fkey in ru_captions:
                res.append(f"{fname}|{ru_captions[fkey]}")
            elif len(parts) > 1 and parts[1].strip():
                res.append(f"{fname}|{parts[1].strip()}")
            else:
                res.append(fname)

        res.append("}}")
        return "\n".join(res)

    return re.sub(r"<gallery[^>]*>(.*?)</gallery>", gal_repl, text, flags=re.IGNORECASE | re.DOTALL)


def extract_ru_structure(ru_text: str) -> Tuple[str, Dict[str, str], str]:
    """Вытаскивает шапку, защищённые разделы и подвал из русской статьи."""
    parsed = mwparserfromhell.parse(ru_text)

    lead_nodes = []
    for node in parsed.nodes:
        if isinstance(node, mwparserfromhell.nodes.heading.Heading) and node.level == 2:
            break
        lead_nodes.append(str(node))
    lead = "".join(lead_nodes).strip()

    preserved: Dict[str, str] = {}
    for sec in parsed.get_sections(include_lead=False, levels=[2]):
        headings = [h for h in sec.filter_headings() if h.level == 2]
        if headings:
            title = headings[0].title.strip()
            if title in PRESERVE_RU_SECTIONS:
                preserved[title] = str(sec).strip()

    footer_match = re.search(r"(==\s*Навигация\s*==[\s\S]*)", ru_text, re.IGNORECASE)
    if footer_match:
        footer = footer_match.group(1).strip()
    else:
        footer_pattern = (
            r"^(\{\{(?:Галереи|Интервики|HazbinGallery|HelluvaGallery|Character gallery navbox)\}\}"
            r"|\[\[Категория:[^\]]+\]\]|\[\[[a-z\-]{2,10}:[^\]]+\]\])\s*$"
        )
        footer_elements = re.findall(footer_pattern, ru_text, re.MULTILINE | re.IGNORECASE)
        footer = "== Навигация ==\n" + "\n".join(footer_elements) if footer_elements else ""

    return lead, preserved, footer


def process_article(en_text: str, ru_text: str) -> str:
    lead, preserved_ru, footer = extract_ru_structure(ru_text)
    ru_captions = extract_ru_captions(ru_text)

    en_parsed = mwparserfromhell.parse(en_text)
    new_sections: List[str] = []
    used_preserved: Set[str] = set()

    for sec in en_parsed.get_sections(include_lead=False, levels=[2]):
        headings = [h for h in sec.filter_headings() if h.level == 2]
        if not headings:
            continue

        raw_en_title = headings[0].title.strip()
        ru_title = translate_header_name(raw_en_title)

        if ru_title in PRESERVE_RU_SECTIONS:
            if ru_title in preserved_ru:
                new_sections.append(preserved_ru[ru_title])
                used_preserved.add(ru_title)
            continue

        sec_text = str(sec)
        sec_text = clean_en_junk(sec_text)
        sec_text = translate_headings(sec_text)
        sec_text = convert_galleries(sec_text, ru_captions)

        if sec_text.strip():
            new_sections.append(sec_text.strip())

    # Сохраняем защищённые разделы из RU, даже если их не было на EN
    for title, content in preserved_ru.items():
        if title not in used_preserved:
            new_sections.append(content)

    parts = [p for p in ([lead] + new_sections + ([footer] if footer else [])) if p]
    final_text = "\n\n".join(parts)
    final_text = re.sub(r"\n{3,}", "\n\n", final_text)
    return final_text.strip()


def run_sync(dry_run: bool = True, target_page: Optional[str] = None, limit: int = 0) -> None:
    username, password = get_credentials(prefer_bot=True)
    if not dry_run and (not username or not password):
        print("[-] Ошибка: Для боевого режима необходимы учётные данные бота в окружении!")
        raise SystemExit(1)

    print(f"[i] Подключение к API Фэндома (режим: {'DRY-RUN / ТЕСТ' if dry_run else 'БОЕВОЙ'})...")
    ru_site = connect_site(
        RU_DOMAIN,
        path=RU_PATH,
        username=username if not dry_run else None,
        password=password if not dry_run else None,
    )
    en_site = connect_site(EN_DOMAIN, path=EN_PATH)
    if not ru_site or not en_site:
        raise SystemExit(1)

    pages_to_process = []
    if target_page:
        pages_to_process.append(ru_site.pages[target_page])
    else:
        for cat_name in CATEGORIES_TO_CHECK:
            print(f"[*] Сбор страниц из категории: {cat_name}")
            for p in ru_site.pages[cat_name]:
                if p.namespace == 0:
                    pages_to_process.append(p)

    processed_count = 0
    for ru_page in pages_to_process:
        if limit > 0 and processed_count >= limit:
            break

        ru_title = ru_page.name
        en_title = None
        for prefix, title in ru_page.langlinks():
            if prefix == "en":
                en_title = title
                break

        if not en_title:
            continue

        en_page = en_site.pages[en_title]
        if not en_page.exists:
            continue

        ru_text = ru_page.text()
        en_text = en_page.text()

        if "{{галерея" not in ru_text.lower() and "{{gallery" not in ru_text.lower():
            continue

        new_ru_text = process_article(en_text, ru_text)
        processed_count += 1

        if new_ru_text.strip() == ru_text.strip():
            print(f"[=] Без изменений: {ru_title}")
            continue

        print(f"\n[!] Обнаружены изменения: {ru_title} (EN: {en_title})")
        if dry_run:
            diff = difflib.unified_diff(
                ru_text.splitlines(),
                new_ru_text.splitlines(),
                fromfile=f"RU (текущая): {ru_title}",
                tofile=f"RU (новая): {ru_title}",
                lineterm="",
                n=2,
            )
            diff_lines = list(diff)
            print("\n".join(diff_lines[:80]))
            if len(diff_lines) > 80:
                print(f"... (показаны первые 80 из {len(diff_lines)} строк diff)")
        else:
            if safe_save(
                ru_page,
                new_ru_text,
                summary="Техническая синхронизация: обновление структуры галереи",
                bot=True,
                sleep_after=3.0,
            ):
                print(f"  [+] Сохранено: {ru_title}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Синхронизация галерей Hazbin/Helluva с EN-вики.")
    parser.add_argument("--dry-run", action="store_true", help="Тестовый прогон без сохранения на вики (вывод diff).")
    parser.add_argument("--enable", action="store_true", help="Явный запуск в боевом режиме с сохранением правок.")
    parser.add_argument("--page", type=str, default=None, help="Проверить только одну конкретную страницу (например 'Аластор/Галерея').")
    parser.add_argument("--limit", type=int, default=0, help="Ограничить число обрабатываемых статей.")
    args = parser.parse_args()

    if not args.dry_run and not args.enable:
        print("[!] Скрипт синхронизации галерей временно отключён по умолчанию.")
        print("    Для безопасного теста запустите: python src/scripts/bots/sync_galleries.py --dry-run --page \"Аластор/Галерея\"")
        return

    run_sync(dry_run=not args.enable, target_page=args.page, limit=args.limit)


if __name__ == "__main__":
    main()
