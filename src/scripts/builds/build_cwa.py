import os
import glob

# Правильные пути к исходникам и итоговому файлу
SOURCE_DIR = 'src/local/wikicorporate/scripts/cwa_source/'
OUTPUT_FILE = 'src/local/wikicorporate/scripts/CrossWikiActivity/Main.js'

def build():
    if not os.path.exists(SOURCE_DIR):
        os.makedirs(SOURCE_DIR)
        print(f"[!] Создана папка {SOURCE_DIR}. Положите туда модули.")
        return

    files = sorted(glob.glob(os.path.join(SOURCE_DIR, '*.js')))

    if not files:
        print(f"[-] JS файлы не найдены в {SOURCE_DIR}")
        return

    combined_code = "/* Исходные файлы располагаются на GitHub и обновляются автоматически */\n"
    
    for file in files:
        with open(file, 'r', encoding='utf-8') as f:
            file_name = os.path.basename(file)
            combined_code += f"\n/* {file_name} */\n\n"
            combined_code += f.read().strip() + "\n"

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(combined_code)

    print(f"[+] Успешно собрано файлов: {len(files)} -> {OUTPUT_FILE}")

if __name__ == "__main__":
    build()
