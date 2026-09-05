import requests
import json
import os
import time

# Единая база настроек
PROJECTS = {
    "Hazbin Hotel": {
        "output": "src/local/hazbin/main/Интервики.json",
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
        "hubs": {
            "en": "https://zoophobia.fandom.com/api.php",
            "ja": "https://zoophobia.fandom.com/ja/api.php"
        }
    },
    "Returnal": {
        "output": "src/local/returnal/main/Интервики.json",
        "hubs": {
            "en": "https://returnal.fandom.com/api.php"
        }
    },
    "Helltaker": {
        "output": "src/local/helltaker/main/Интервики.json",
        "hubs": {
            "en": "https://helltaker.fandom.com/api.php"
        }
    },
    "Oneshot": {
        "output": "src/local/oneshot/main/Интервики.json",
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
        interwiki_db = {}
        
        for hub_lang, hub_url in config["hubs"].items():
            print(f"[*] Сканирую {hub_lang.upper()} вики ({hub_url})...")
            
            params = {
                "action": "query",
                "generator": "allpages",
                "gaplimit": "50",  # Снизили нагрузку, чтобы сервер Фэндома не падал
                "prop": "langlinks",
                "lllimit": "max",
                "format": "json"
            }
            
            while True:
                success = False
                for attempt in range(3): # Даем 3 попытки на каждую порцию страниц
                    try:
                        req = session.get(hub_url, params=params, timeout=60)
                        response = req.json()
                        
                        if "error" in response:
                            print(f"  [!] Ошибка API: {response['error'].get('info', 'Неизвестная ошибка')}")
                            break # Фатальная ошибка API, прекращаем попытки
                            
                        success = True
                        break # Успешно скачали, прерываем цикл попыток
                        
                    except Exception as e:
                        print(f"  [!] Заминка со связью (попытка {attempt+1}/3). Повтор через 3 секунды...")
                        time.sleep(3)
                        
                if not success:
                    print("  [!] Не удалось загрузить кусок страниц. Переходим к следующей вики.")
                    break # Переходим к следующей вики только если все 3 попытки провалились
                
                pages = response.get("query", {}).get("pages", {})
                
                for page_id, page_data in pages.items():
                    langlinks = page_data.get("langlinks", [])
                    if not langlinks:
                        continue
                    
                    hub_title = page_data["title"]
                    ru_title = None
                    
                    for link in langlinks:
                        if link["lang"] == "ru":
                            ru_title = link["*"]
                            break
                    
                    if ru_title:
                        if ru_title not in interwiki_db:
                            interwiki_db[ru_title] = {}
                        
                        interwiki_db[ru_title][hub_lang] = hub_title
                        
                        for link in langlinks:
                            if link["lang"] != "ru" and link["lang"] not in interwiki_db[ru_title]:
                                interwiki_dbru_title = link["*"]
                                
                if "continue" in response:
                    params.update(response["continue"])
                else:
                    break
                    
        os.makedirs(os.path.dirname(config["output"]), exist_ok=True)
        with open(config["output"], "w", encoding="utf-8") as f:
            json.dump(interwiki_db, f, ensure_ascii=False, indent=4, sort_keys=True)
            
        print(f"[+] Успешно! База {project_name} обновлена: {len(interwiki_db)} статей.")

if __name__ == "__main__":
    fetch_interwikis()
