import os
import glob

# Откуда берём исходники и куда кладём результат
SOURCE_DIR = 'src/local/wikicorporate/cwa_source/'
OUTPUT_FILE = 'src/local/wikicorporate/mediawiki/CrossWikiActivity/Main.js'

def build():
    if not os.path.exists(SOURCE_DIR):
        os.makedirs(SOURCE_DIR)
        print(f"[!] Создана папка {SOURCE_DIR}. Положите туда модули.")
        return

    # Получаем список файлов и сортируем по алфавиту (01_, 02_ и т.д.)
    files = sorted(glob.glob(os.path.join(SOURCE_DIR, '*.js')))

    if not files:
        print(f"[-] JS файлы не найдены в {SOURCE_DIR}")
        return

    combined_code = "/* Сгенерировано автоматически из модулей */\n"
    
    for file in files:
        with open(file, 'r', encoding='utf-8') as f:
            file_name = os.path.basename(file)
            combined_code += f"\n/* =============== ОРИГИНАЛ: {file_name} =============== */\n\n"
            combined_code += f.read().strip() + "\n"

    # Создаём целевую папку mediawiki/CrossWikiActivity/, если её нет
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    # Записываем готовый файл
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(combined_code)

    print(f"[+] Успешно собрано файлов: {len(files)} -> {OUTPUT_FILE}")

if __name__ == "__main__":
    build()
