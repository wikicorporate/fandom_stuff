import glob
import os
from typing import List

SOURCE_DIR = "src/local/wikicorporate/scripts/cwa_source"
OUTPUT_FILE = "src/local/wikicorporate/scripts/CrossWikiActivity/Main.js"

EXPECTED_LAYERS = [
    "01_init.js",
    "02_constants.js",
    "03_template.js",
    "04_state.js",
    "05_api_methods.js",
    "06_ui_methods.js",
    "07_mount.js",
]


def build() -> None:
    if not os.path.exists(SOURCE_DIR):
        os.makedirs(SOURCE_DIR, exist_ok=True)
        print(f"[!] Создана папка {SOURCE_DIR}. Положите туда исходные модули.")
        return

    files: List[str] = sorted(glob.glob(os.path.join(SOURCE_DIR, "*.js")))
    if not files:
        print(f"[-] JS-файлы не найдены в {SOURCE_DIR}")
        raise SystemExit(1)

    found_names = [os.path.basename(f) for f in files]
    missing = [layer for layer in EXPECTED_LAYERS if layer not in found_names]
    if missing:
        print(f"[!] Предупреждение: отсутствуют ожидаемые слои CWA: {', '.join(missing)}")

    chunks: List[str] = [
        "/* eslint-disable */",
        "/* Исходные файлы располагаются на GitHub (fandom_stuff) и собираются автоматически */",
    ]

    for filepath in files:
        file_name = os.path.basename(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read().strip()
        chunks.append(f"\n/* === LAYER: {file_name} === */\n{content}")

    combined_code = "\n".join(chunks) + "\n"

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            existing_code = f.read()
        if existing_code == combined_code:
            print(f"[=] Сборка не изменилась ({len(files)} слоёв): {OUTPUT_FILE}")
            return

    with open(OUTPUT_FILE, "w", encoding="utf-8", newline="\n") as f:
        f.write(combined_code)

    print(f"[+] Успешно собрано слоёв: {len(files)} -> {OUTPUT_FILE}")


if __name__ == "__main__":
    build()
