import os
import re
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

# Разделы, внутри которых мы НЕ объединяем файлы, но их порядок сортируем
IGNORE_SECTIONS = [
    "screenshots", 
    "скриншоты"
]

# Полный словарь переводов
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

def detach_footer(text):
    """Отделяет Навигацию и категории от тела статьи для безопасной сортировки."""
    # 1. Ищем явный заголовок Навигации
    match = re.search(r'(==\s*Навигация\s*==.*)', text, re.IGNORECASE | re.DOTALL)
    if match:
        footer = match.group(1).strip()
        body = text[:match.start()].strip()
        return body, footer
        
    # 2. Если заголовка нет, собираем шаблоны и категории с самого низа
    footer_elements = re.findall(r'^(\{\{(?:Галереи|Интервики|HazbinGallery|HelluvaGallery)\}\}|\[\[Категория:[^\]]+\]\])\s*$', text, re.MULTILINE | re.IGNORECASE)
    
    if footer_elements:
        body = re.sub(r'^(\{\{(?:Галереи|Интервики|HazbinGallery|HelluvaGallery)\}\}|\[\[Категория:[^\]]+\]\])\s*$\n?', '', text, flags=re.MULTILINE | re.IGNORECASE)
        # Автоматически оборачиваем их в красивый заголовок Навигации
        footer = "== Навигация ==\n" + "\n".join(footer_elements)
        return body.strip(), footer.strip()
        
    return text, ""

def get_sections_map(parsed, is_ru=False):
    """Разбивает статью на словарь {Название_раздела: данные_раздела}"""
    sec_map = {}
    for sec in parsed.get_sections(include_lead=False, levels=[2]):
        headings = [h for h in sec.filter_headings() if h.level == 2]
        if not headings: continue
        
        title = headings[0].title.strip()
        is_ignored = any(word in title.lower() for word in IGNORE_SECTIONS)
            
        if is_ru:
            gals = [tpl for tpl in sec.filter_templates() if tpl.name.strip().lower() in ('галерея', 'gallery')]
        else:
            gals = sec.filter_tags(matches=lambda node: node.tag.lower() == 'gallery')
            
        sec_map[title] = {
            'section': sec,
            'heading_str': str(headings[0]),
            'gals': gals,
            'ignored': is_ignored
        }
    return sec_map

def merge_single_gallery(en_gal, ru_gal):
    """Сливает две идентичные галереи, добавляя новые файлы из EN в RU."""
    ru_items = {}
    ru_filenames_ordered = [] 
    
    ru_positional = [str(p.value) for p in ru_gal.params if not p.showkey]
    ru_raw = "|".join(ru_positional)
    
    for line in ru_raw.split('\n'):
        line = line.strip()
        if not line: continue
        parts = line.split('|')
        filename = parts[0].strip()
        ru_items[filename] = line 
        ru_filenames_ordered.append(filename)
            
    new_ru_lines = []
    changed = False
    
    if en_gal.contents:
        for line in str(en_gal.contents).strip().split('\n'):
            line = line.strip()
            if not line: continue
            parts = line.split('|', 1)
            filename = parts[0].strip()
            en_caption = parts[1].strip() if len(parts) > 1 else ""
            
            if filename in ru_items:
                new_ru_lines.append(ru_items[filename])
                del ru_items[filename]
            else:
                if en_caption:
                    new_ru_lines.append(f"{filename}|{en_caption}")
                else:
                    new_ru_lines.append(f"{filename}")
                changed = True 
                
    # Эксклюзивные русские файлы возвращаем в конец
    for fname in ru_filenames_ordered:
        if fname in ru_items:
            new_ru_lines.append(ru_items[fname])
            
    if not changed:
        return None
        
    named_params = [p for p in ru_gal.params if p.showkey]
    new_template = "{{Галерея\n"
    for p in named_params:
        new_template += f"|{str(p.name).strip()}={str(p.value).strip()}\n"
        
    for line in new_ru_lines:
        new_template += f"|{line}\n"
    new_template += "}}"
    
    return new_template

def convert_en_section_to_ru(en_sec_str, ru_title, en_heading_str):
    """Конвертирует целый английский раздел в русский формат."""
    sec_text = en_sec_str.replace(en_heading_str, f"== {ru_title} ==", 1)
    
    sec_text = re.sub(r'<gallery[^>]*>', '{{Галерея|\n', sec_text, flags=re.IGNORECASE)
    sec_text = re.sub(r'</gallery>', '}}', sec_text, flags=re.IGNORECASE)
    
    lines = sec_text.split('\n')
    new_lines = []
    in_gallery = False
    for line in lines:
        if '{{Галерея' in line:
            in_gallery = True
        elif line.strip() == '}}':
            in_gallery = False
            
        if in_gallery and '|' in line and not line.startswith('{{'):
            line = re.sub(r'\|\s*alt\s*=[^|]*', '', line)
        new_lines.append(line)
        
    return "\n".join(new_lines).strip()

def merge_and_sort_galleries(en_text, ru_text):
    # 1. Отделяем безопасный подвал от тела статьи
    ru_body, ru_footer = detach_footer(ru_text)
    
    en_parsed = mwparserfromhell.parse(en_text)
    ru_parsed = mwparserfromhell.parse(ru_body)
    
    en_map = get_sections_map(en_parsed, is_ru=False)
    ru_map = get_sections_map(ru_parsed, is_ru=True)
    
    changed = False
    final_sections = []
    used_ru_titles = set()
    new_sequence_raw = []
    
    # 2. Вытаскиваем "Голову" (Вступление, Табвью)
    lead_nodes = []
    for node in ru_parsed.nodes:
        if isinstance(node, mwparserfromhell.nodes.heading.Heading) and node.level == 2:
            break
        lead_nodes.append(str(node))
    lead_text = "".join(lead_nodes).strip()
    
    # 3. Собираем тело статьи строго по английскому порядку
    for en_title, en_data in en_map.items():
        ru_title = HEADERS_MAP.get(en_title) or HEADERS_MAP.get(en_title.title(), en_title)
        
        # Если раздел уже есть на русской вики
        if ru_title in ru_map:
            ru_data = ru_map[ru_title]
            used_ru_titles.add(ru_title)
            new_sequence_raw.append(ru_title)
            
            # Мержим галереи (если они не в черном списке и совпадают по количеству)
            if not en_data['ignored'] and not ru_data['ignored']:
                if len(en_data['gals']) == len(ru_data['gals']) and len(en_data['gals']) > 0:
                    sec_parsed = ru_data['section']
                    for en_gal, ru_gal in zip(en_data['gals'], ru_data['gals']):
                        new_template = merge_single_gallery(en_gal, ru_gal)
                        if new_template:
                            sec_parsed.replace(ru_gal, new_template)
                            changed = True
                    final_sections.append(str(sec_parsed).strip())
                else:
                    final_sections.append(str(ru_data['section']).strip())
            else:
                # Черный список (Скриншоты и т.д.): переносим как есть, но на нужное место
                final_sections.append(str(ru_data['section']).strip())
                
        # Если раздела на русской вики нет
        else:
            if not en_data['ignored'] and len(en_data['gals']) > 0:
                print(f"    [+] Добавлен новый раздел: {en_title} -> {ru_title}")
                new_sec_text = convert_en_section_to_ru(str(en_data['section']), ru_title, en_data['heading_str'])
                final_sections.append(new_sec_text)
                new_sequence_raw.append(ru_title)
                changed = True
                
    # 4. Добавляем уникальные русские разделы (которых нет на англовики) в самый низ списка
    for ru_title, ru_data in ru_map.items():
        if ru_title not in used_ru_titles:
            final_sections.append(str(ru_data['section']).strip())
            new_sequence_raw.append(ru_title)
            
    # 5. Проверяем, изменился ли порядок сортировки существующих разделов
    old_sequence = list(ru_map.keys())
    reordered_existing = [x for x in new_sequence_raw if x in old_sequence]
    
    if reordered_existing != old_sequence:
        print("    [!] Обнаружено несовпадение порядка разделов. Структура отсортирована!")
        changed = True
        
    if not changed:
        return None
        
    # 6. Собираем всё воедино: Голова + Отсортированное тело + Навигация
    final_text = lead_text + "\n\n" + "\n\n".join(final_sections)
    if ru_footer:
        final_text += "\n\n" + ru_footer
        
    # Очищаем от лишних пустых строк
    final_text = re.sub(r'\n{3,}', '\n\n', final_text)
    return final_text.strip()

def main():
    username = os.environ.get('WIKI_USERNAME')
    password = os.environ.get('WIKI_PASSWORD')
    
    if not username or not password:
        print("[-] Ошибка: Не найдены BotPasswords в секретах GitHub!")
        return

    print("[i] Подключение к API Фэндома...")
    en_site = mwclient.Site(EN_DOMAIN, path=EN_PATH)
    ru_site = mwclient.Site(RU_DOMAIN, path=RU_PATH)
    ru_site.login(username, password)
    
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
            
            # --- ПЕРЕВОД TODO-ЗАГОЛОВКОВ ---
            def resolve_todo(match):
                en_name = match.group(1).strip()
                ru_name = HEADERS_MAP.get(en_name) or HEADERS_MAP.get(en_name.title(), en_name)
                return f"== {ru_name} =="
                
            ru_text_cleaned = re.sub(r'^==\s*TODO:\s*([^=]+?)\s*==$', resolve_todo, ru_text, flags=re.MULTILINE | re.IGNORECASE)
            todos_resolved = (ru_text != ru_text_cleaned)
            # -------------------------------
            
            if "{{галерея" not in ru_text_cleaned.lower() and "{{gallery" not in ru_text_cleaned.lower():
                continue
                
            new_ru_text = merge_and_sort_galleries(en_text, ru_text_cleaned)
            
            # Обработка ситуаций, если изменились только TODO-заголовки
            if new_ru_text is None:
                if todos_resolved:
                    new_ru_text = ru_text_cleaned
                else:
                    continue
                
            if new_ru_text == ru_text:
                continue
                
            print(f"  [+] Сохраняю изменения в статье {ru_title}...")
            ru_page.save(new_ru_text, summary="🤖 Автоматическая синхронизация (перевод заголовков, сортировка структуры и обновление файлов)")

if __name__ == "__main__":
    main()
