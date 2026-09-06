import requests
import json
import os
import time

# Единая база настроек
PROJECTS = {
    "Hazbin Hotel": {
        "output": "src/local/hazbin/main/Интервики.json",
        "ru_api": "https://hazbinhotel.fandom.com/ru/api.php",
        "hubs": {
            "cs": "https://hazbinhotel.fandom.com/cs/api.php",
            "de": "https://hazbinhotel.fandom.com/de/api.php",
            "en": "https://hazbinhotel.fandom.com/api.php",
            "es": "https://hazbinhotel.fandom.com/es/api.php",
            "fr": "https://hazbin-hotel.fandom.com/fr/api.php",
            "hu": "https://voltvalaki-hotel.fandom.com/hu/api.php",
            "it": "https://hazbinhotel.fandom.com/it/api.php",
            "ja": "https://hazbinhotel.fandom.com/ja/api.php",
            "pl": "https://hazbinhotel.fandom.com/pl/api.php",
            "pt-br": "https://hazbinhotel.fandom.com/pt-br/api.php",
            "th": "https://hazbin-hotel.fandom.com/th/api.php",
            "tr": "https://hazbinhotel.fandom.com/tr/api.php",
            "zh": "https://hazbinhotel.fandom.com/zh/api.php"
        }
    },
    "Zoophobia": {
        "output": "src/local/zoophobia/main/Интервики.json",
        "ru_api": "https://zoophobia.fandom.com/ru/api.php",
        "hubs": {
            "en": "https://zoophobia.fandom.com/api.php",
            "ja": "https://zoophobia.fandom.com/ja/api.php"
        }
    },
    "Returnal": {
        "output": "src/local/returnal/main/Интервики.json",
        "ru_api": "https://returnal.fandom.com/ru/api.php",
        "hubs": {
            "en": "https://returnal.fandom.com/api.php"
        }
    },
    "Helltaker": {
        "output": "src/local/helltaker/main/Интервики.json",
        "ru_api": "https://helltaker.fandom.com/ru/api.php",
        "hubs": {
            "en": "https://helltaker.fandom.com/api.php"
        }
    },
    "Oneshot": {
        "output": "src/local/oneshot/main/Интервики.json",
        "ru_api": "https://oneshot.fandom.com/ru/api.php",
        "hubs": {
            "en": "https://oneshot.fandom.com/api.php",
            "fr": "https://oneshot.fandom.com/fr/api.php",
            "zh": "https://oneshot.fandom.com/zh/api.php"
        }
    }
}

def fetch_interwikis():
    session = requests.Session()
    
    for project_name, config in PROJECTS.items():
        print(f"\n[=== Запуск сбора для проекта: {project_name} ===]")
        
        # 1. ЗАГРУЖАЕМ СТАРУЮ БАЗУ
        interwiki_db = {}
        if os.path.exists(config["output"]):
            try:
                with open(config["output"], "r", encoding="utf-8") as f:
                    interwiki_db = json.load(f)
                print(f"[*] Загружена существующая база: {len(interwiki_db)} статей.")
            except Exception as e:
                print(f"[!] Ошибка чтения старой базы: {e}")
        
        # 2. СОБИРАЕМ НОВЫЕ ССЫЛКИ В ТЕМПОВЫЙ СЛОВАРЬ
        temp_db = {}
        for hub_lang, hub_url in config["hubs"].items():
            print(f"[*] Сканирую {hub_lang.upper()} вики ({hub_url})...")
            params = {
                "action": "query",
                "generator": "allpages",
                "gaplimit": "50",
                "gapnamespace": 0,
                "gapfilterredir": "nonredirects",
                "prop": "langlinks",
                "lllimit": "max",
                "format": "json"
            }
            
            while True:
                success = False
                for attempt in range(3):
                    try:
                        req = session.get(hub_url, params=params, timeout=60)
                        response = req.json()
                        if "error" in response:
                            print(f"  [!] Ошибка API: {response['error'].get('info', 'Unknown')}")
                            break
                        success = True
                        break
                    except Exception as e:
                        time.sleep(3)
                        
                if not success: break 
                
                pages = response.get("query", {}).get("pages", {})
                for page_id, page_data in pages.items():
                    langlinks = page_data.get("langlinks", [])
                    if not langlinks: continue
                    
                    hub_title = page_data["title"]
                    ru_title = None
                    
                    for link in langlinks:
                        if link["lang"] == "ru":
                            ru_title = link["*"]
                            break
                    
                    if ru_title:
                        if ru_title not in temp_db:
                            temp_db[ru_title] = {}
                        temp_db[ru_title][hub_lang] = hub_title
                        
                        for link in langlinks:
                            if link["lang"] != "ru" and link["lang"] not in temp_db[ru_title]:
                                temp_dbru_title = link["*"]
                                
                if "continue" in response:
                    params.update(response["continue"])
                else:
                    break

        # 3. ПРОВЕРЯЕМ РУССКУЮ ВИКИ И РЕЗОЛВИМ ПЕРЕНАПРАВЛЕНИЯ
        print("[*] Сверка с русской вики и исправление перенаправлений...")
        ru_titles = list(temp_db.keys())
        redirect_map = {}
        
        # Разбиваем на порции по 50 статей
        for i in range(0, len(ru_titles), 50):
            chunk = ru_titles[i:i+50]
            params = {
                "action": "query",
                "titles": "|".join(chunk),
                "redirects": "1",
                "format": "json"
            }
            try:
                # Отправляем POST, чтобы длинный список не сломал URL
                res = session.post(config["ru_api"], data=params, timeout=30).json()
                if "query" in res and "redirects" in res["query"]:
                    for redir in res["query"]["redirects"]:
                        redirect_map[redir["from"]] = redir["to"]
            except Exception as e:
                print(f"  [!] Ошибка при проверке редиректов: {e}")

        # 4. ОБЪЕДИНЯЕМ ЧИСТЫЕ ДАННЫЕ СО СТАРОЙ БАЗОЙ
        for ru_title, links in temp_db.items():
            # Если статья оказалась редиректом, берем ее настоящее имя
            true_title = redirect_map.get(ru_title, ru_title)
            
            if true_title not in interwiki_db:
                interwiki_db[true_title] = {}
                
            for lang, title in links.items():
                if lang not in interwiki_db[true_title]:
                    interwiki_db[true_title][lang] = title

        # Удаляем из базы ключи, которые остались от старых кривых ссылок
        for bad_title in redirect_map.keys():
            if bad_title in interwiki_db:
                del interwiki_db[bad_title]

        os.makedirs(os.path.dirname(config["output"]), exist_ok=True)
        with open(config["output"], "w", encoding="utf-8") as f:
            json.dump(interwiki_db, f, ensure_ascii=False, indent=4, sort_keys=True)
            
        print(f"[+] Успешно! База {project_name} сохранена: {len(interwiki_db)} чистых статей.")

if __name__ == "__main__":
    fetch_interwikis()
