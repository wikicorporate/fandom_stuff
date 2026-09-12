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
        page.save(new_text, summary="Категоризация новых и восстановленных файлов")
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
    
    processed_files = set() # Хранилище обработанных файлов, чтобы избежать дублей
    
    # ЭТАП 1: Проверка лога загрузок за последние 24 часа
    cutoff_time = datetime.utcnow() - timedelta(hours=24)
    print(f"\n[*] ЭТАП 1: Проверка файлов, загруженных после: {cutoff_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")

    try:
        uploads = site.logevents(type='upload')
        
        for upload in uploads:
            # mwclient возвращает время в виде объекта time.struct_time
            # Безопасно собираем из него datetime (год, месяц, день, час, минута, секунда)
            event_time = datetime(*upload['timestamp'][:6])
            
            # Если наткнулись на файл старше 24 часов — останавливаем первый этап
            if event_time < cutoff_time:
                print("[+] Достигнут предел в 24 часа. Загрузки проверены.")
                break
                
            title = upload.get('title')
            if title and title not in processed_files:
                processed_files.add(title)
                page = site.pages[title]
                categorize_simple(site, page)
                
    except Exception as e:
        print(f"[-] Ошибка при получении лога загрузок: {e}")

    # ЭТАП 2: Проверка служебной страницы "Некатегоризованные файлы"
    print("\n[*] ЭТАП 2: Сканирование служебной страницы 'Некатегоризованные файлы'...")
    try:
        qpoffset = 0
        while True:
            # Используем API для получения списка некатегоризованных файлов
            response = site.api('query', list='querypage', qppage='Uncategorizedimages', qplimit='max', qpoffset=qpoffset)
            results = response.get('query', {}).get('querypage', {}).get('results', [])
            
            if not results:
                break
                
            for item in results:
                title = item.get('title')
                if title and title not in processed_files:
                    processed_files.add(title)
                    page = site.pages[title]
                    categorize_simple(site, page)
            
            # Проверяем, есть ли еще страницы для пагинации (если файлов больше лимита выдачи)
            if 'continue' in response and 'qpoffset' in response['continue']:
                qpoffset = response['continue']['qpoffset']
            else:
                break
                
        print("[+] Сканирование некатегоризованных файлов завершено.")
        
    except Exception as e:
        print(f"[-] Ошибка при получении списка некатегоризованных файлов: {e}")

if __name__ == "__main__":
    main()
