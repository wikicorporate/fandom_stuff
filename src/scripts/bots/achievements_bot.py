import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set
import mwclient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from utils.wiki_client import REPO_ROOT, connect_site, load_projects

DEFAULT_THRESHOLDS = [1, 5, 10, 25, 50, 100, 250, 500, 1000]
DEFAULT_POINTS = [10, 20, 30, 40, 50, 50, 50, 100, 150]
REMOTE_CONFIG_PAGE = "MediaWiki:Custom-AchievementsConfig.json"


def fetch_remote_tracks_config(site: mwclient.Site) -> Dict[str, Any]:
    """Читает дополнительный конфиг треков, если админ сохранил его через Special:AchievementsCustomize."""
    try:
        page = site.pages[REMOTE_CONFIG_PAGE]
        if page.exists:
            raw = page.text().strip()
            if raw:
                data = json.loads(raw)
                if isinstance(data, dict):
                    return data
    except Exception as e:
        print(f"  [!] Не удалось прочитать {REMOTE_CONFIG_PAGE}: {e}")
    return {}


def get_category_pages(site: mwclient.Site, category_name: str) -> Set[str]:
    """Возвращает множество названий всех статей (ns=0) в указанной категории."""
    clean_cat = category_name.strip()
    if not clean_cat.lower().startswith(("категория:", "category:")):
        clean_cat = f"Категория:{clean_cat}"

    titles: Set[str] = set()
    try:
        cat_page = site.pages[clean_cat]
        for member in cat_page.members(namespace=0):
            titles.add(member.name)
    except Exception as e:
        print(f"  [-] Ошибка получения страниц категории '{clean_cat}': {e}")
    return titles


def scan_category_edits(site: mwclient.Site, page_titles: Set[str]) -> Dict[str, List[str]]:
    """
    Сканирует историю правок всех страниц категории.
    Возвращает словарь: { "Имя_Участника": ["2026-01-01T10:00:00Z", ...] } (от старых к новым).
    """
    user_timestamps: Dict[str, List[str]] = {}

    for title in sorted(page_titles):
        try:
            page = site.pages[title]
            for rev in page.revisions(prop="user|timestamp|flags", limit="max"):
                user = rev.get("user")
                # Игнорируем анонимов и ботов
                if not user or "bot" in rev.get("flags", "") or user.lower().endswith("bot"):
                    continue
                ts_struct = rev.get("timestamp")
                if ts_struct:
                    iso_ts = datetime(*ts_struct[:6], tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                else:
                    iso_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

                user_timestamps.setdefault(user, []).append(iso_ts)
        except Exception as e:
            print(f"  [!] Ошибка чтения ревизий статьи '{title}': {e}")

    for user in user_timestamps:
        user_timestamps[user].sort()

    return user_timestamps


def build_project_achievements(site: mwclient.Site, local_cfg: Dict[str, Any]) -> Dict[str, Any]:
    remote_cfg = fetch_remote_tracks_config(site)

    thresholds: List[int] = remote_cfg.get("thresholds") or local_cfg.get("thresholds") or DEFAULT_THRESHOLDS
    points_table: List[int] = remote_cfg.get("points") or local_cfg.get("points") or DEFAULT_POINTS

    # Объединяем треки из config.json и из MediaWiki:Custom-AchievementsConfig.json (приоритет у вики)
    tracks_map: Dict[str, Dict[str, Any]] = {}
    for t in local_cfg.get("tracks", []):
        if t.get("id"):
            tracks_map[t["id"]] = t
    for t in remote_cfg.get("tracks", []):
        if t.get("id"):
            tracks_map[t["id"]] = t

    special_map: Dict[str, Dict[str, Any]] = {}
    for sb in local_cfg.get("special_badges", []):
        if sb.get("id"):
            special_map[sb["id"]] = sb
    for sb in remote_cfg.get("special_badges", []):
        if sb.get("id"):
            special_map[sb["id"]] = sb

    users_summary: Dict[str, Dict[str, Any]] = {}
    recent_unlocks: List[Dict[str, Any]] = []

    # 1. Обработка категориальных треков
    for track_id, track in tracks_map.items():
        cat_name = track.get("category", "")
        if not cat_name:
            continue

        print(f"  [*] Сканирование трека '{track.get('title', track_id)}' (Категория:{cat_name})...")
        pages = get_category_pages(site, cat_name)
        print(f"      Найдено статей в категории: {len(pages)}")

        user_edits = scan_category_edits(site, pages)
        levels_cfg = track.get("levels", [])
        default_icon = track.get("default_icon", "Badge-Default.png")

        for user, timestamps in user_edits.items():
            edit_count = len(timestamps)
            unlocked_level = 0
            earned_points = 0
            unlocked_at = ""

            for idx, req_count in enumerate(thresholds):
                if edit_count >= req_count:
                    unlocked_level = idx + 1
                    earned_points += points_table[idx] if idx < len(points_table) else 50
                    unlocked_at = timestamps[req_count - 1]
                else:
                    break

            u_entry = users_summary.setdefault(user, {"points": 0, "tracks": {}, "special": []})
            u_entry["points"] += earned_points
            u_entry["tracks"][track_id] = {
                "edits": edit_count,
                "level": unlocked_level,
                "points": earned_points,
                "unlocked_at": unlocked_at,
            }

            if unlocked_level > 0:
                lvl_idx = unlocked_level - 1
                lvl_info = levels_cfg[lvl_idx] if lvl_idx < len(levels_cfg) else {}
                badge_name = lvl_info.get("name") or f"{track.get('title', cat_name)} — Уровень {unlocked_level}"
                badge_icon = lvl_info.get("icon") or default_icon
                badge_pts = points_table[lvl_idx] if lvl_idx < len(points_table) else 50

                recent_unlocks.append({
                    "user": user,
                    "track_id": track_id,
                    "level": unlocked_level,
                    "name": badge_name,
                    "description": track.get("description") or f"За правки в категории «{cat_name}»",
                    "icon": badge_icon,
                    "points": badge_pts,
                    "timestamp": unlocked_at,
                })

    # 2. Обработка специальных (ручных) наград
    for spec_id, spec in special_map.items():
        pts = int(spec.get("points", 100))
        for user in spec.get("users", []):
            u_entry = users_summary.setdefault(user, {"points": 0, "tracks": {}, "special": []})
            u_entry["points"] += pts
            u_entry["special"].append(spec_id)

    recent_unlocks.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    return {
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "thresholds": thresholds,
        "points": points_table,
        "tracks": list(tracks_map.values()),
        "special_badges": list(special_map.values()),
        "users": users_summary,
        "recent": recent_unlocks[:20],
    }


def main() -> None:
    projects = load_projects()
    processed = 0

    for project_name, cfg in projects.items():
        ach_cfg = cfg.get("achievements", {})
        if not ach_cfg.get("enabled"):
            continue

        domain = cfg.get("domain")
        api_path = cfg.get("path", "/ru/")
        alias = cfg.get("alias", project_name.lower())
        output_rel = ach_cfg.get("output") or f"src/local/{alias}/mediawiki/Custom-Achievements.json"
        output_path = REPO_ROOT / output_rel

        print(f"\n[=== Расчёт кастомных достижений: {project_name} ({domain}{api_path}) ===]")
        site = connect_site(domain, path=api_path)
        if not site:
            continue

        compiled_data = build_project_achievements(site, ach_cfg)

        os.makedirs(output_path.parent, exist_ok=True)
        with open(output_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(compiled_data, f, ensure_ascii=False, indent=2)
            f.write("\n")

        processed += 1
        print(
            f"[+] База достижений {project_name} сохранена в {output_path.relative_to(REPO_ROOT)} "
            f"(участников: {len(compiled_data['users'])}, недавних наград: {len(compiled_data['recent'])})."
        )

    if processed == 0:
        print("[*] Нет проектов с включённым блоком 'achievements.enabled: true' в config.json.")


if __name__ == "__main__":
    main()
