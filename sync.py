import os
import json
import mwclient

# --- НАСТРОЙКИ ---
USERNAME = os.environ.get('WIKI_USERNAME')
PASSWORD = os.environ.get('WIKI_PASSWORD')

# Маппинг названий папок в пространства имён MediaWiki
NAMESPACE_MAP = {
    'modules': 'Module',
    'templates': 'Template',
    'mediawiki': 'MediaWiki',
    'widgets': 'Widget'
}

# Кэш подключений, чтобы не логиниться перед загрузкой каждого файла
site_connections = {}

def get_site(domain):
    if domain not in site_connections:
        print(f"\n🔌 Подключение к {domain}...")
        site = mwclient.Site(domain, path='/')
        try:
            site.login(USERNAME, PASSWORD)
            site_connections[domain] = site
        except Exception as e:
            print(f"❌ Ошибка авторизации на {domain}: {e}")
            return None
    return site_connections[domain]

def get_page_title(folder_name, filename):
    """Определяет правильное имя страницы. Модулям и шаблонам отрезает расширения."""
    ns = NAMESPACE_MAP.get(folder_name.lower())
    if not ns:
        return None
        
    if ns in ['Module', 'Template', 'Widget']:
        name = os.path.splitext(filename)[0] # Убираем .lua или .wikitext
    else:
        name = filename # Оставляем .js или .css для MediaWiki
        
    return f"{ns}:{name}"

def upload_file(domain, filepath, page_title):
    site = get_site(domain)
    if not site: return

    with open(filepath, 'r', encoding='utf-8') as f:
        local_content = f.read()

    page = site.pages[page_title]
    remote_content = page.text()

    if local_content.strip() != remote_content.strip():
        print(f"   [Обновление] {page_title} -> {domain}")
        try:
            page.save(local_content, summary="Автоматическая синхронизация (GitHub Actions)")
        except Exception as e:
            print(f"   ❌ Ошибка при загрузке {page_title}: {e}")
    else:
        print(f"   [Без изменений] {page_title} на {domain}")

def process_directory(base_dir, target_domains):
    if not os.path.exists(base_dir): return

    for ns_folder in os.listdir(base_dir):
        ns_path = os.path.join(base_dir, ns_folder)
        if not os.path.isdir(ns_path) or ns_folder.lower() not in NAMESPACE_MAP:
            continue

        for filename in os.listdir(ns_path):
            if filename.startswith('.'): continue # Пропускаем системные файлы
            
            filepath = os.path.join(ns_path, filename)
            page_title = get_page_title(ns_folder, filename)
            
            if not page_title: continue

            for domain in target_domains:
                upload_file(domain, filepath, page_title)

def main():
    if not USERNAME or not PASSWORD:
        print("❌ Секреты WIKI_USERNAME или WIKI_PASSWORD не найдены в окружении!")
        return

    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Ошибка чтения config.json: {e}")
        return

    print("🚀 Начинаем синхронизацию файлов...")

    # 1. Загрузка ГЛОБАЛЬНЫХ файлов (на все вики)
    process_directory('src/global', config.get('all_wikis', []))

    # 2. Загрузка ЛОКАЛЬНЫХ файлов (только на конкретную вики с учетом алиасов)
    local_dir = 'src/local'
    if os.path.exists(local_dir):
        local_aliases = config.get('local_aliases', {})
        for folder_name in os.listdir(local_dir):
            domain_path = os.path.join(local_dir, folder_name)
            if os.path.isdir(domain_path):
                # Ищем папку в алиасах. Если не находим — используем название папки как домен.
                target_domain = local_aliases.get(folder_name, folder_name)
                process_directory(domain_path, [target_domain])

    # 3. Загрузка ГРУППОВЫХ файлов (на кластеры вики)
    shared_dir = 'src/shared'
    if os.path.exists(shared_dir):
        for group_folder in os.listdir(shared_dir):
            group_path = os.path.join(shared_dir, group_folder)
            if os.path.isdir(group_path):
                target_domains = config.get('groups', {}).get(group_folder, [])
                if not target_domains:
                    print(f"⚠️ Внимание: Группа '{group_folder}' не найдена в config.json!")
                    continue
                process_directory(group_path, target_domains)

    print("\n✅ Синхронизация завершена!")

if __name__ == '__main__':
    main()
