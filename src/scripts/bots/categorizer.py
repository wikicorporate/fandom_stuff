import os
import time
from datetime import datetime, timedelta
import mwclient

PREFIX_MAP = {
    "HH-": "Категория:Изображения Отеля Хазбин",
    "HB-": "Категория:Изображения Адского Босса"
}

def categorize_simple(site, page):
    text = page.text()
    filename = page.name.split(":", 1)[-1].strip()
    prefix = filename[:3].upper()
    
    if prefix not in PREFIX_MAP:
        return

    # ПРОВЕРКА 1: Есть ли уже какая-либо категория у файла
    if "[[Категория:" in text or "[[Category:" in text:
        print(f"[*] Пропуск (уже есть категория): {filename}")
        return

    # ПРОВЕРКА 2: Находится ли файл в общем хранилище (Shared Repository)
    res = site.api('query', prop='imageinfo', titles=page.name)
    pages = res.get('query', {}).get('pages', {})
    for pid, pdata in pages.items():
        repo = pdata.get('imagerepository')
        if repo != 'local':
            print(f"[*] Пропуск (файл из общего хранилища '{repo}'): {filename}")
            return

    # Если проверки пройдены — категоризируем
    category_name = f"[[{PREFIX_MAP[prefix]}]]"
    new_text = text.strip() + f"\n\n{category_name}"
    
    try:
        page.save(new_text, summary="Автоматическая категоризация")
        print(f"[+] Добавлена категория для {filename}")
        time.sleep(3)
    except Exception as e:
        print(f"[-] Ошибка при сохранении {filename}: {e}")

def main():
    username = os.environ.get('FANDOM_BOT_USERNAME')
    password = os.environ.get('FANDOM_BOT_PASSWORD')
    
    if not username or not password:
        print("[-] Ошибка: Секреты логина/пароля не найдены в окружении!")
        return
    
    print("[=== Запуск Категоризатора файлов ===]")
    site = mwclient.Site("hazbinhotel.fandom.com", path="/ru/")
    
    try:
        site.login(username, password)
    except Exception as e:
        print(f"[-] Ошибка авторизации: {e}")
        return
    
    # Определяем границу времени: текущее время по UTC минус 24 часа
    cutoff_time = datetime.utcnow() - timedelta(hours=24)
    print(f"[*] Проверка файлов, загруженных после: {cutoff_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")

    try:
        # Убираем жесткий лимит в 50 файлов, скрипт остановится сам по времени
        uploads = site.logevents(type='upload')
        
        for upload in uploads:
            # Получаем время загрузки файла и переводим в формат datetime
            timestamp_str = upload.get('timestamp')
            event_time = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%SZ")
            
            # Если наткнулись на файл старше 24 часов — останавливаем скрипт
            if event_time < cutoff_time:
                print("\n[+] Достигнут предел в 24 часа. Остановка скрипта.")
                break
                
            title = upload.get('title')
            if title:
                page = site.pages[title]
                categorize_simple(site, page)
                
    except Exception as e:
        print(f"[-] Ошибка при получении лога загрузок: {e}")

if __name__ == "__main__":
    main()
