import os
import mwclient
import mwparserfromhell
import time

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
    
    if not username or not password:
        print("[-] Ошибка: Секреты логина/пароля не найдены в окружении!")
        return
    
    for project_name, config in PROJECTS.items():
        if not config.get("all_pages"): continue
            
        print(f"\n[=== Резолвер редиректов: {project_name} ===]")
        site = mwclient.Site(config["domain"], path=config["path"])
        
        try:
            site.login(username, password)
            print("[+] Успешная авторизация.")
        except Exception as e:
            print(f"[-] Ошибка авторизации на {project_name}: {e}")
            continue
        
        print("[*] Составление карты перенаправлений (это займёт пару минут)...")
        redirect_map = {}
        for page in site.allpages(namespace=0, filterredir='redirects'):
            target = page.redirects_to()
            if target:
                redirect_map[page.name] = target.name
                
        print(f"[+] Найдено редиректов: {len(redirect_map)}")
        
        print("[*] Сканирование статей на наличие старых ссылок...")
        for page in site.allpages(namespace=0, filterredir='nonredirects'):
            text = page.text()
            parsed = mwparserfromhell.parse(text)
            changed = False
            
            for wikilink in parsed.filter_wikilinks():
                link_title = str(wikilink.title).strip()
                
                if link_title in redirect_map:
                    real_target = redirect_map[link_title]
                    
                    if not wikilink.text:
                        if link_title != real_target:
                            wikilink.text = link_title
                            
                    wikilink.title = real_target
                    changed = True
                    
            if changed:
                new_text = str(parsed)
                print(f"[!] Обновлены ссылки в статье: {page.name}")
                
                for attempt in range(3):
                    try:
                        page.save(new_text, summary="Автоматическая замена перенаправлений на прямые ссылки")
                        time.sleep(3) 
                        break
                    except mwclient.errors.APIError as e:
                        if e.code == 'ratelimited':
                            print(f"    [!] Сработал антиспам. Ждём 15 секунд... (Попытка {attempt + 1}/3)")
                            time.sleep(15)
                        else:
                            print(f"    [-] Ошибка API при сохранении: {e}")
                            break
                    except Exception as e:
                        print(f"    [-] Неизвестная ошибка при сохранении: {e}")
                        break

if __name__ == "__main__":
    main()
