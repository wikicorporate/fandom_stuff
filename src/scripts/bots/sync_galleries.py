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

IGNORE_SECTIONS = [
    "screenshots", 
    "скриншоты",
    "animations",
    "анимация"
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
    return re.sub(r'^(?:File|Файл|Image|Изображение):\s*', '', name, flags=re.IGNORECASE).strip()

def clean_header_title(title):
    t = re.sub(r"'''?", "", title)
    t = re.sub(r'</?[^>]+>', '', t)
    t = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]+)\]\]', r'\1', t)
    return t.strip()

def detach_footer(text):
    match = re.search(r'(==\s*Навигация\s*==.*)', text, re.IGNORECASE | re.DOTALL)
    if match:
        footer = match.group(1).strip()
        body = text[:match.start()].strip()
        return body, footer
        
    footer_elements = re.findall(r'^(\{\{(?:Галереи|Интервики|HazbinGallery|HelluvaGallery)\}\}|\[\[Категория:[^\]]+\]\])\s*$', text, re.MULTILINE | re.IGNORECASE)
    
    if footer_elements:
        body = re.sub(r'^(\{\{(?:Галереи|Интервики|HazbinGallery|HelluvaGallery)\}\}|\[\[Категория:[^\]]+\]\])\s*$\n?', '', text, flags=re.MULTILINE | re.IGNORECASE)
        footer = "== Навигация ==\n" + "\n".join(footer_elements)
        return body.strip(), footer.strip()
        
    return text, ""

def get_sections_map(parsed, is_ru=False):
    sec_map = {}
    for sec in parsed.get_sections(include_lead=False, levels=[2]):
        headings = [h for h in sec.filter_headings() if h.level == 2]
        if not headings: continue
        
        raw_title = headings[0].title.strip()
        clean_title = clean_header_title(raw_title)
        is_ignored = any(word in clean_title.lower() for word in IGNORE_SECTIONS)
            
        if is_ru:
            gals = [tpl for tpl in sec.filter_templates() if tpl.name.strip().lower() in ('галерея', 'gallery')]
        else:
            gals = sec.filter_tags(matches=lambda node: node.tag.lower() == 'gallery')
            
        sec_map[clean_title] = {
            'section': sec,
            'heading_str': str(headings[0]),
            'gals': gals,
            'ignored': is_ignored
        }
    return sec_map

def create_new_ru_section(ru_title, en_gals):
    lines = [f"== {ru_title} =="]
    for gal in en_gals:
        lines.append("{{Галерея")
        if gal.contents:
            for line in str(gal.contents).strip().split('\n'):
                line = line.strip()
                if not line: continue
                line = re.sub(r'\|\s*alt\s*=[^|]*', '', line)
                parts = line.split('|', 1)
                fname = clean_fname(parts[0])
                if len(parts) > 1:
                    lines.append(f"|{fname}|{parts[1].strip()}")
                else:
                    lines.append(f"|{fname}")
        lines.append("}}")
    return "\n".join(lines)

def merge_single_gallery(en_gal, ru_gal):
    ru_items = {}
    ru_filenames_ordered = [] 
    
    ru_positional = [str(p.value) for p in ru_gal.params if not p.showkey]
    ru_raw = "|".join(ru_positional)
    
    for line in ru_raw.split('\n'):
        line = line.strip()
        if not line: continue
        parts = line.split('|', 1)
        fname = clean_fname(parts[0])
        ru_items[fname] = line 
        ru_filenames_ordered.append(fname)
            
    new_ru_lines = []
    changed = False
    
    if en_gal.contents:
        for line in str(en_gal.contents).strip().split('\n'):
            line = line.strip()
            if not line: continue
            
            line = re.sub(r'\|\s*alt\s*=[^|]*', '', line)
            parts = line.split('|', 1)
            fname = clean_fname(parts[0])
            en_caption = parts[1].strip() if len(parts) > 1 else ""
            
            if fname in ru_items:
                new_ru_lines.append(ru_items[fname])
                del ru_items[fname]
            else:
                if en_caption:
                    new_ru_lines.append(f"{fname}|{en_caption}")
                else:
                    new_ru_lines.append(f"{fname}")
                changed = True 
                
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

def merge_and_sort_galleries(en_text, ru_text):
    ru_body, ru_footer = detach_footer(ru_text)
    
    en_parsed = mwparserfromhell.parse(en_text)
    ru_parsed = mwparserfromhell.parse(ru_body)
    
    en_map = get_sections_map(en_parsed, is_ru=False)
    ru_map = get_sections_map(ru_parsed, is_ru=True)
    
    changed = False
    final_sections = []
    used_ru_titles = set()
    new_sequence_raw = []
    
    lead_nodes = []
    for node in ru_parsed.nodes:
        if isinstance(node, mwparserfromhell.nodes.heading.Heading) and node.level == 2:
            break
        lead_nodes.append(str(node))
    lead_text = "".join(lead_nodes).strip()
    
    for en_title, en_data in en_map.items():
        ru_title = HEADERS_MAP.get(en_title) or HEADERS_MAP.get(en_title.title(), f"TODO: {en_title}")
        
        if ru_title in ru_map:
            ru_data = ru_map[ru_title]
            used_ru_titles.add(ru_title)
            new_sequence_raw.append(ru_title)
            
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
                final_sections.append(str(ru_data['section']).strip())
                
        else:
            if not en_data['ignored'] and len(en_data['gals']) > 0:
                print(f"    [+] Добавлен новый раздел: {en_title} -> {ru_title}")
                new_sec_text = create_new_ru_section(ru_title, en_data['gals'])
                final_sections.append(new_sec_text)
                new_sequence_raw.append(ru_title)
                changed = True
                
    for ru_title, ru_data in ru_map.items():
        if ru_title not in used_ru_titles:
            final_sections.append(str(ru_data['section']).strip())
            new_sequence_raw.append(ru_title)
            
    old_sequence = list(ru_map.keys())
    reordered_existing = [x for x in new_sequence_raw if x in old_sequence]
    
    if reordered_existing != old_sequence:
        print("    [!] Обнаружено несовпадение порядка разделов. Структура отсортирована!")
        changed = True
        
    if not changed:
        return None
        
    final_text = lead_text + "\n\n" + "\n\n".join(final_sections)
    if ru_footer:
        final_text += "\n\n" + ru_footer
        
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
    
    # ПРАВИЛЬНАЯ АВТОРИЗАЦИЯ ДЛЯ MWCLIENT
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
            
            def resolve_todo(match):
                en_name = match.group(1).strip()
                clean_en = clean_header_title(en_name)
                ru_name = HEADERS_MAP.get(clean_en) or HEADERS_MAP.get(clean_en.title(), f"TODO: {clean_en}")
                return f"== {ru_name} =="
                
            ru_text_cleaned = re.sub(r'^==\s*TODO:\s*([^=]+?)\s*==$', resolve_todo, ru_text, flags=re.MULTILINE | re.IGNORECASE)
            todos_resolved = (ru_text != ru_text_cleaned)
            
            if "{{галерея" not in ru_text_cleaned.lower() and "{{gallery" not in ru_text_cleaned.lower():
                continue
                
            new_ru_text = merge_and_sort_galleries(en_text, ru_text_cleaned)
            
            if new_ru_text is None:
                if todos_resolved:
                    new_ru_text = ru_text_cleaned
                else:
                    continue
                
            if new_ru_text == ru_text:
                continue
                
            print(f"  [+] Сохраняю изменения в статье {ru_title}...")
            
            for attempt in range(3):
                try:
                    ru_page.save(new_ru_text, summary="Дополнение галерей")
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
