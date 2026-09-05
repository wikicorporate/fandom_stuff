import os
import mwclient
import mwparserfromhell

PROJECTS = {
    "Hazbin Hotel": {"domain": "hazbinhotel.fandom.com", "path": "/ru/", "all_pages": True},
    "Zoophobia": {"domain": "zoophobia.fandom.com", "path": "/ru/", "all_pages": True},
    "Returnal": {"domain": "returnal.fandom.com", "path": "/ru/", "all_pages": True},
    "Helltaker": {"domain": "helltaker.fandom.com", "path": "/ru/", "all_pages": True},
    "OneShot": {"domain": "oneshot.fandom.com", "path": "/ru/", "all_pages": True}
}

def main():
    username = os.environ.get('FANDOM_BOT_USERNAME')
    password = os.environ.get('FANDOM_BOT_PASSWORD')
    
    for project_name, config in PROJECTS.items():
        if not config.get("all_pages"): continue
            
        print(f"\n[=== Резолвер редиректов: {project_name} ===]")
        site = mwclient.Site(config["domain"], path=config["path"])
        site.login(username, password)
        
        print("[*] Составление карты перенаправлений (это займёт пару минут)...")
        redirect_map = {}
        # Запрашиваем только страницы-редиректы
        for page in site.allpages(namespace=0, filterredir='redirects'):
            target = page.redirects_to()
            if target:
                redirect_map[page.name] = target.name
                
        print(f"[+] Найдено редиректов: {len(redirect_map)}")
        
        # Теперь сканируем обычные статьи
        print("[*] Сканирование статей на наличие старых ссылок...")
        for page in site.allpages(namespace=0, filterredir='nonredirects'):
            text = page.text()
            parsed = mwparserfromhell.parse(text)
            changed = False
            
            for wikilink in parsed.filter_wikilinks():
                link_title = str(wikilink.title).strip()
                
                # Если ссылка ведёт на редирект
                if link_title in redirect_map:
                    real_target = redirect_map[link_title]
                    
                    # Если текст ссылки не был указан, сохраняем старое название как текст
                    # [[Старое имя]] -> [[Новое имя|Старое имя]]
                    if not wikilink.text:
                        if link_title != real_target:
                            wikilink.text = link_title
                            
                    # Меняем саму ссылку на актуальную
                    wikilink.title = real_target
                    changed = True
                    
            if changed:
                new_text = str(parsed)
                print(f"[!] Обновлены ссылки в статье: {page.name}")
                page.save(new_text, summary="Замена перенаправлений на прямые ссылки")

if __name__ == "__main__":
    main()
