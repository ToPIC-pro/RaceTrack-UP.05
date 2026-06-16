import json
import os
from datetime import datetime


SAVES_DIR = "saves"
MAX_SAVES = 3


def ensure_saves_dir():
    os.makedirs(SAVES_DIR, exist_ok=True)


def get_save_path(index):
    return os.path.join(SAVES_DIR, f"save_{index}.json")


def list_saves():
    ensure_saves_dir()
    saves = []

    for i in range(MAX_SAVES):
        path = get_save_path(i)

        if not os.path.exists(path):
            saves.append(None)
            continue

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            meta = data.get("meta", {})
            saves.append({
                "slot": i,
                "path": path,
                "name": meta.get("name", f"Гонка #{i + 1}"),
                "timestamp": meta.get("timestamp", ""),
                "track_name": meta.get("track_name", ""),
                "mode": data.get("mode", "local")
            })
        except (json.JSONDecodeError, OSError):
            saves.append(None)

    return saves


def load_save(slot):
    path = get_save_path(slot)

    if not os.path.exists(path):
        return None

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def delete_save(slot):
    ensure_saves_dir()

    path = get_save_path(slot)

    if os.path.exists(path):
        os.remove(path)

    # Сдвигаем все следующие сохранения вверх
    for i in range(slot + 1, MAX_SAVES):
        src = get_save_path(i)
        dst = get_save_path(i - 1)

        if os.path.exists(src):
            os.replace(src, dst)

    # Удаляем последний дубликат
    last_path = get_save_path(MAX_SAVES - 1)

    if os.path.exists(last_path):
        os.remove(last_path)


def write_save_to_slot(slot, data):
    ensure_saves_dir()
    path = get_save_path(slot)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def push_new_save_to_top(data):
    ensure_saves_dir()

    oldest_path = get_save_path(MAX_SAVES - 1)
    if os.path.exists(oldest_path):
        os.remove(oldest_path)

    for i in range(MAX_SAVES - 1, 0, -1):
        src = get_save_path(i - 1)
        dst = get_save_path(i)

        if os.path.exists(src):
            os.replace(src, dst)

    write_save_to_slot(0, data)
    return 0


def promote_save_to_top(slot, data):
    ensure_saves_dir()

    if slot <= 0:
        write_save_to_slot(0, data)
        return 0

    for i in range(slot, 0, -1):
        src = get_save_path(i - 1)
        dst = get_save_path(i)

        if os.path.exists(src):
            os.replace(src, dst)

    write_save_to_slot(0, data)
    return 0


def build_save_meta(name=None, track_name=""):
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

    return {
        "name": name or f"Сохранение {timestamp}",
        "timestamp": timestamp,
        "track_name": track_name
    }