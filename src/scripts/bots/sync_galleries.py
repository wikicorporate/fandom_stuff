import os
import re
import time
import mwclient
import mwparserfromhell

EN_DOMAIN = 'hazbinhotel.fandom.com'
EN_PATH = '/'

RU_DOMAIN = 'hazbinhotel.fandom.com'
RU_PATH = '/ru/'

CATEGORIES_TO_CHECK = [
    "Категория:Галереи Отеля Хазбин",
    "Категория:Галереи Адского Босса" 
]

# Разделы, которые мы НЕ трогаем и оставляем из русской версии (для будущих хабов)
PRESERVE_RU_SECTIONS = [
    "Скриншоты",
    "Анимация",
    "Раскадровки",
    "Черновики"
]

HEADERS_MAP = {
    "Screenshots": "Скриншоты", "Animations": "Анимация", "Official Artwork": "Официальное творчество",
    "Merchandise": "Мерчендайз", "Concept Art": "Концепт-арты", "Miscellaneous": "Разное",
    "Promotional": "Промо-арты", "Promotional Artwork": "Промо-арты", "Promotional artwork": "Промо-арты",
    "Design": "Дизайн", "Designs": "Дизайн", "Comics": "Комиксы", "Others": "Прочее", "Other": "Другое",
    "Clothing": "Одежда", "Outfits": "Одежда", "Official art": "Официальные арты", "Staff Artwork": "Официальные арты",
    "Signed prints": "Подписанные принты", "Signed Prints": "Подписанные принты", "Signing prints": "Подписанные принты",
    "Signing Prints": "Подписанные принты", "T-shirts, hoodies, and sweaters": "Футболки, толстовки и свитеры",
    "T-Shirts, Hoodies, and Sweaters": "Футболки, толстовки и свитеры", "Pins": "Значки", "Keychains": "Брелоки",
    "Figures": "Фигурки", "Standees": "Стенды", "Acrylic Standees": "Акриловые статуэтки", "Plushies": "Плюшевые игрушки",
    "Posters": "Постеры", "Posters and prints": "Постеры", "Posters and Prints": "Постеры",
    "Cards": "Коллекционные карты", "Promo Cards": "Коллекционные карты", "Pajama Pants": "Пижамные штаны",
    "Loungewear Pants": "Пижамные штаны", "Socks": "Носки", "Notebooks and Sketchbooks": "Блокноты и скетчбуки",
    "Lanyards": "Ремни", "Jewelry": "Браслеты", "Nintendo Switch Cases": "Чехлы для Nintendo Switch",
    "Puzzles and Games": "Пазлы и игры", "Playmats": "Игровые коврики", "Mugs and Glasses": "Кружки и стаканы",
    "Backpacks": "Рюкзаки", "Backpacks and Bags": "Рюкзаки и сумки", "Wallets": "Кошельки", "Stickers": "Стикеры",
    "Model Sheets": "Модели", "Storyboards": "Раскадровки", "Beatboards": "Черновики", "Titlecards": "Заставки эпизодов",
    "Voxtagram Posts": "Посты в [[Вокстаграм]]е", "Voxtagram posts": "Посты в [[Вокстаграм]]е",
    "[[Voxtagram]] Posts": "Посты в [[Вокстаграм]]е", "[[Voxtagram]] posts": "Посты в [[Вокстаграм]]е",
    "Livestreams": "Трансляции", "YouTooz": "Фигурки YouTooz", "Youtooz": "Фигурки YouTooz",
    "Pinboards": "Доски для булавок", "Skateboards": "Скейтборды", "Hats and Beanies": "Головные уборы",
    "Scarves": "Шарфы", "Pilot": "Пилотные эпизоды", "Season 1": "Первый сезон", "Season 2": "Второй сезон",
    "Helluva Shorts": "Короткометражные эпизоды",
    "Apparel": "Одежда", "Bags": "Сумки", "Banners": "Баннеры", "Episode Artwork": "Арты в эпизоде",
    "Games": "Игры", "Hats": "Головные уборы", "Hats and Outerwear": "Головные уборы и верхняя одежда",
    "Hoodies, T-Shirts and Sweaters": "Толстовки, футболки и свитеры", "Mugs": "Кружки",
    "Mugs & Glasses": "Кружки и стаканы", "Mugs and Cups": "Кружки и чашки",
    "Pajama Pants and Shorts": "Пижамные штаны и шорты", "Pajama Pants, and Shorts": "Пижамные штаны и шорты",
    "Playmates": "Игровые коврики", "Promotional Art": "Промо-арты", "Slipmat": "Слипматы",
    "T-Shirts, Sweatshirts, and Hoodies": "Футболки, толстовки и свитеры", "Trading Cards": "Коллекционные карты"
}

def clean_fname(name):
    """Вырезает префиксы File:, Файл: перед вставкой в галерею."""
    return re.sub(r'^(?:File|Файл|Image|Изображение):\s*', '', name, flags=re.IGNORECASE).strip()

def clean_header_title(title):
    """Счищает жирный шрифт и ссылки из заголовков для поиска в словаре."""
    t = re.sub(r"'''?", "", title)
    t = re.sub(r'</?[^>]+>', '', t)
    t = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]+)\]\]', r'\1', t)
    return t.strip()

def clean_en_junk(text):
    """Удаляет английские шаблоны, категории и интервики."""
    text = re.sub(r'\{\{(HazbinGallery|HelluvaGallery|Main|GalleryTabber|Character gallery navbox)[^}]*\}\}\n?', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\[\[Category:[^\]]+\]\]\n?', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\[\[[a-z-]{2,10}:[^\]]+\]\]\n?', '', text, flags=re.IGNORECASE)
    return text.strip()

def translate_headings(text):
    """Переводит все уровни заголовков (==, ===, ====) с помощью словаря."""
    def repl(match):
        level = match.group(1)
        title = match.group(2).strip()
        clean_title = clean_header_title(title)
        
        ru_title = HEADERS_MAP.get(clean_title) or HEADERS_MAP.get(clean_title.title(), f"TODO: {clean_title}")
        return f"{level} {ru_title} {level}"
        
    return re.sub(r'^(={2,6})\s*(.*?)\s*\1$', repl, text, flags=re.MULTILINE)

def convert_galleries(text):
    """Конвертирует <gallery> в {{Галерея|...}}, убирает alt= и пустые строки."""
    def gal_repl(match):
        inner = match.group(1).strip()
        lines = inner.split('\n')
        res = ["{{Галерея|"]
        
        for line in lines:
            line = line.strip()
            if not line: continue
            
            line = re.sub(r'\|\s*alt\s*=[^|]*', '', line)
            parts = line.split('|', 1)
            fname = clean_fname(parts[0])
            
            if not fname:
                continue
                
            if len(parts) > 1:
                caption = parts[1].strip()
                if caption:
                    res.append(f"{fname}|{caption}")
                else:
                    res.append(fname)
            else:
                res.append(fname)
                
        res.append("}}")
        return '\n'.join(res)
        
    return re.sub(r'<gallery[^>]*>(.*?)</gallery>', gal_repl, text, flags=re.IGNORECASE | re.DOTALL)

def extract_ru_structure(ru_text):
    """Вытаскивает шапку, защищенные разделы и подвал из русской статьи."""
    parsed = mwparserfromhell.parse(ru_text)
    
    # Извлекаем шапку
    lead_nodes = []
    for node in parsed.nodes:
        if isinstance(node, mwparserfromhell.nodes.heading.Heading) and node.level == 2:
            break
        lead_nodes.append(str(node))
    lead = "".join(lead_nodes).strip()
    
    # Извлекаем защищенные разделы
    preserved = {}
    for sec in parsed.get_sections(include_lead=False, levels=[2]):
        headings = [h for h in sec.filter_headings() if h.level == 2]
        if headings:
            title = headings[0].title.strip()
            if title in PRESERVE_RU_SECTIONS:
                preserved[title] = str(sec).strip()
                
    # Извлекаем подвал
    footer_match = re.search(r'(==\s*Навигация\s*==.*)', ru_text, re.IGNORECASE | re.DOTALL)
    if footer_match:
        footer = footer_match.group(1).strip()
    else:
        footer_pattern = r'^(\{\{(?:Галереи|Интервики|HazbinGallery|HelluvaGallery|Character gallery navbox)\}\}|\[\[Категория:[^\]]+\]\]|\[\[[a-z-]{2,10}:[^\]]+\]\])\s*$'
        footer_elements = re.findall(footer_pattern, ru_text, re.MULTILINE | re.IGNORECASE)
        if footer_elements:
            footer = "== Навигация ==\n" + "\n".join(footer_elements)
        else:
            footer = ""
            
    return lead, preserved, footer

def process_article(en_text, ru_text):
    lead, preserved_ru, footer = extract_ru_structure(ru_text)
    
    en_parsed = mwparserfromhell.parse(en_text)
    new_sections = []
    
    # Обрабатываем разделы с английской вики
    for sec in en_parsed.get_sections(include_lead=False, levels=[2]):
        headings = [h for h in sec.filter_headings() if h.level == 2]
        if not headings: continue
        
        raw_en_title = headings[0].title.strip()
        clean_en_title = clean_header_title(raw_en_title)
        ru_title = HEADERS_MAP.get(clean_en_title) or HEADERS_MAP.get(clean_en_title.title(), f"TODO: {clean_en_title}")
        
        # Если раздел защищён, вставляем его русскую версию
        if ru_title in PRESERVE_RU_SECTIONS:
            if ru_title in preserved_ru:
                new_sections.append(preserved_ru[ru_title])
            continue
            
        # Иначе собираем чистый раздел из английского кода
        sec_text = str(sec)
        sec_text = clean_en_junk(sec_text)
        sec_text = translate_headings(sec_text)
        sec_text = convert_galleries(sec_text)
        
        if sec_text.strip():
            new_sections.append(sec_text.strip())
            
    # Добавляем защищенные разделы, которые были на RU, но которых нет на EN (на всякий случай)
    for title, content in preserved_ru.items():
        if title not in str(new_sections):
            new_sections.append(content)
            
    final_text = lead + "\n\n" + "\n\n".join(new_sections)
    if footer:
        final_text += "\n\n" + footer
        
    final_text = re.sub(r'\n{3,}', '\n\n', final_text)
    return final_text.strip()

def main():
    username = os.environ.get('WIKI_USERNAME')
    password = os.environ.get('WIKI_PASSWORD')
    
    if not username or not password:
        print("[-] Ошибка: Не найдены BotPasswords в секретах GitHub!")
        return

    print("[i] Подключение к API Фэндома...")
    ru_site = mwclient.Site(RU_DOMAIN, path=RU_PATH)
    en_site = mwclient.Site(EN_DOMAIN, path=EN_PATH)
    
    try:
        ru_site.login(username, password)
        print("[+] Успешная авторизация бота на русской вики.")
    except Exception as e:
        print(f"[-] Ошибка авторизации: {e}")
        return
    
    for cat_name in CATEGORIES_TO_CHECK:
        print(f"\n[=== Сканирование: {cat_name} ===]")
        category = ru_site.pages[cat_name]
        
        for ru_page in category:
            if ru_page.namespace != 0: 
                continue
                
            ru_title = ru_page.name
            
            en_title = None
            for prefix, title in ru_page.langlinks():
                if prefix == 'en':
                    en_title = title
                    break
            
            if not en_title:
                continue
                
            print(f"[*] Обработка: {ru_title} (Связано с EN: {en_title})")
            
            en_page = en_site.pages[en_title]
            if not en_page.exists:
                continue
                
            ru_text = ru_page.text()
            en_text = en_page.text()
            
            if "{{галерея" not in ru_text.lower() and "{{gallery" not in ru_text.lower():
                continue
                
            new_ru_text = process_article(en_text, ru_text)
            
            if new_ru_text == ru_text:
                continue
                
            print(f"  [+] Сохраняю изменения в статье {ru_title}...")
            
            for attempt in range(3):
                try:
                    ru_page.save(new_ru_text, summary="Техническая синхронизация: полная реконструкция структуры галереи из оригинала")
                    time.sleep(3)
                    break
                except mwclient.errors.APIError as e:
                    if e.code == 'ratelimited':
                        print(f"    [!] Сработал антиспам (ratelimited). Ждём 15 секунд... (Попытка {attempt + 1}/3)")
                        time.sleep(15)
                    else:
                        print(f"    [-] Ошибка API при сохранении: {e}")
                        break
                except Exception as e:
                    print(f"    [-] Неизвестная ошибка при сохранении: {e}")
                    break

if __name__ == "__main__":
    main()
