import os
import time
import mwclient

# Словарь префиксов
PREFIX_MAP = {
    "HH-": "Категория:Изображения Отеля Хазбин",
    "HB-": "Категория:ИзображенияАдского Босса"
}

def categorize_simple(site, page):
    text = page.text()
    # Убираем "Файл:" или "File:"
    filename = page.name.split(":", 1)[-1].strip()
    
    # Берём первые 3 символа названия
    prefix = filename[:3].upper()
    
    if prefix in PREFIX_MAP:
        category_name = f"[[{PREFIX_MAP[prefix]}]]"
        
        # Если этой категории ещё нет в тексте файла
        if category_name not in text:
            new_text = text.strip() + f"\n\n{category_name}"
            
            try:
                page.save(new_text, summary="Категоризация")
                print(f"[+] Добавлена категория для {filename}")
                time.sleep(3) # ПАУЗА ДЛЯ ОБХОДА ЛИМИТОВ
            except Exception as e:
                print(f"[-] Ошибка при сохранении {filename}: {e}")
        else:
            print(f"[*] Файл {filename} уже имеет нужную категорию.")

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
    
    # Проверяем последние 50 загруженных файлов
    try:
        uploads = site.logevents(type='upload', limit=50)
        for upload in uploads:
            title = upload.get('title')
            if title:
                page = site.pages[title]
                categorize_simple(site, page)
    except Exception as e:
        print(f"[-] Ошибка при получении лога загрузок: {e}")

if __name__ == "__main__":
    main()
