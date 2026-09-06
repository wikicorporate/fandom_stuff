import os
import re
import time
import mwclient
import mwparserfromhell

PROJECTS = {
    "Hazbin Hotel": {"domain": "hazbinhotel.fandom.com", "path": "/ru/", "all_pages": True},
    "Zoophobia": {"domain": "zoophobia.fandom.com", "path": "/ru/", "all_pages": True},
    "Returnal": {"domain": "returnal.fandom.com", "path": "/ru/", "all_pages": True},
    "Helltaker": {"domain": "helltaker.fandom.com", "path": "/ru/", "all_pages": True},
    "OneShot": {"domain": "oneshot.fandom.com", "path": "/ru/", "all_pages": True}
}

def clean_typography(text):
    # 1. Умные кавычки (обрабатываем сырой текст, чтобы не разрывать ссылки)
    def smart_quotes(match):
        before, inside = match.group(1), match.group(2)
        # Если внутри есть кириллица, ставим ёлочки
        if re.search(r'[а-яА-ЯёЁ]', inside):
            return f'{before}«{inside}»'
        # Иначе (для английских слов) оставляем прямые кавычки
        return f'{before}"{inside}"'

    # Заменяем кавычки так, чтобы не сломать HTML атрибуты
    text = re.sub(r'(^|[\s(\[-|>])"([^"]+)"(?=[.,!?\)\];:]|\s|-|<|$)', smart_quotes, text)

    # 2. Дефисы и пробелы (через парсер, чтобы не сломать таблицы и шаблоны)
    parsed = mwparserfromhell.parse(text)
    for node in parsed.filter_text():
        val = str(node.value)
        val = re.sub(r'(?<=\S) - (?=\S)', r' — ', val)
        val = re.sub(r'[ \t]{2,}', ' ', val)
        node.value = val
        
    return str(parsed)

def main():
    username = os.environ.get('WIKI_USERNAME')
    password = os.environ.get('WIKI_PASSWORD')
    
    if not username or not password:
        print("❌ Ошибка: Секреты логина/пароля не найдены в окружении!")
        return
    
    for project_name, config in PROJECTS.items():
        if not config.get("all_pages"): continue
            
        print(f"\n[=== Типограф: {project_name} ===]")
        site = mwclient.Site(config["domain"], path=config["path"])
        
        try:
            site.login(username, password)
        except Exception as e:
            print(f"❌ Ошибка авторизации на {project_name}: {e}")
            continue
        
        for page in site.allpages(namespace=0):
            # === ЗАЩИТА ОТ ПОЛОМКИ JSON ===
            if page.name.lower().endswith('.json'):
                print(f"[*] Пропуск технической страницы: {page.name}")
                continue

            original = page.text()
            cleaned = clean_typography(original)
            
            if original != cleaned:
                print(f"[!] Исправлена типографика: {page.name}")
                try:
                    page.save(cleaned, summary="Автоматическое исправление типографики")
                    time.sleep(3) # ПАУЗА 3 СЕКУНДЫ ДЛЯ ОБХОДА БАНА
                except Exception as e:
                    print(f"❌ Ошибка при сохранении {page.name}: {e}")

if __name__ == "__main__":
    main()
