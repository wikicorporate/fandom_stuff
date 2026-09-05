import os
import re
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
    parsed = mwparserfromhell.parse(text)
    
    # filter_text() возвращает только текстовые узлы, не трогая код шаблонов и ссылок!
    for node in parsed.filter_text():
        val = str(node.value)
        
        # 1. Замена прямых кавычек "Текст" на «Текст» (елочки)
        # Ищем кавычку, за которой идёт текст, а потом закрывающая кавычка
        val = re.sub(r'(^|\s)"([^"]+)"(?=\s|[.,!?]|$)', r'\1«\2»', val)
        
        # 2. Замена дефиса, окруженного пробелами, на длинное тире
        val = re.sub(r'(?<=\S) - (?=\S)', r' — ', val)
        
        # 3. Удаление двойных пробелов (но не трогаем переносы строк и отступы)
        val = re.sub(r'[ \t]{2,}', ' ', val)
        
        node.value = val
        
    return str(parsed)

def main():
    username = os.environ.get('FANDOM_BOT_USERNAME')
    password = os.environ.get('FANDOM_BOT_PASSWORD')
    
    for project_name, config in PROJECTS.items():
        if not config.get("all_pages"): continue
            
        print(f"\n[=== Типограф: {project_name} ===]")
        site = mwclient.Site(config["domain"], path=config["path"])
        site.login(username, password)
        
        for page in site.allpages(namespace=0):
            original = page.text()
            cleaned = clean_typography(original)
            
            if original != cleaned:
                print(f"[!] Исправлена типографика: {page.name}")
                page.save(cleaned, summary="Автоматическое исправление типографики")

if __name__ == "__main__":
    main()
