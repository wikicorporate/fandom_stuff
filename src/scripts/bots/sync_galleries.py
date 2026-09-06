import os
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

# ЧЁРНЫЙ СПИСОК РАЗДЕЛОВ (на английском и русском)
# Если галерея находится внутри раздела с таким названием, бот её проигнорирует.
IGNORE_SECTIONS = [
    "screenshots", 
    "скриншоты"
]

def get_valid_galleries(parsed, is_ru=False):
    """Извлекает галереи только из разрешённых разделов статьи."""
    valid_galleries = []
    
    # Разбиваем статью на блоки по заголовкам 2 уровня (== Заголовок ==)
    # include_lead=True захватывает вступление (до первого заголовка)
    sections = parsed.get_sections(include_lead=True, levels=[2])
    
    for sec in sections:
        # Проверяем название раздела
        headings = sec.filter_headings(levels=[2])
        if headings:
            section_title = headings[0].title.strip().lower()
            # Если название раздела есть в чёрном списке — пропускаем его целиком
            if any(word in section_title for word in IGNORE_SECTIONS):
                continue
        
        # Если раздел разрешён, собираем из него галереи
        if is_ru:
            gals = [tpl for tpl in sec.filter_templates() if tpl.name.strip().lower() in ('галерея', 'gallery')]
            valid_galleries.extend(gals)
        else:
            gals = sec.filter_tags(matches=lambda node: node.tag.lower() == 'gallery')
            valid_galleries.extend(gals)
            
    return valid_galleries

def merge_galleries(en_text, ru_text):
    en_parsed = mwparserfromhell.parse(en_text)
    ru_parsed = mwparserfromhell.parse(ru_text)
    
    # Получаем только те галереи, которые лежат в правильных разделах
    en_galleries = get_valid_galleries(en_parsed, is_ru=False)
    ru_galleries = get_valid_galleries(ru_parsed, is_ru=True)
    
    # Если в разрешённых разделах количество галерей не совпадает — пропускаем
    if not en_galleries or len(en_galleries) != len(ru_galleries):
        return None
        
    for en_gal, ru_gal in zip(en_galleries, ru_galleries):
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
                        
        # Возвращаем эксклюзивные русские файлы
        for fname in ru_filenames_ordered:
            if fname in ru_items:
                new_ru_lines.append(ru_items[fname])
                
        # Пересборка русского шаблона
        named_params = [p for p in ru_gal.params if p.showkey]
        
        new_template = "{{Галерея\n"
        for p in named_params:
            new_template += f"|{str(p.name).strip()}={str(p.value).strip()}\n"
            
        for line in new_ru_lines:
            new_template += f"|{line}\n"
        new_template += "}}"
        
        ru_parsed.replace(ru_gal, new_template)
        
    return str(ru_parsed)

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
            
            if "{{галерея" not in ru_text.lower() and "{{gallery" not in ru_text.lower():
                continue
                
            new_ru_text = merge_galleries(en_text, ru_text)
            
            if new_ru_text is None or new_ru_text == ru_text:
                continue
                
            print(f"[!] Обновляю галереи в статье {ru_title}...")
            ru_page.save(new_ru_text, summary="Автоматическая синхронизация галереи (добавлены новые файлы)")

if __name__ == "__main__":
    main()
