import json
import os


TRACKS_CONFIG_PATH = os.path.join("tracks", "tracks_config.json")


def build_preview_path(track_file_path):
    base, _ = os.path.splitext(track_file_path)
    return f"{base}_preview.png"


def load_tracks_config():
    if not os.path.exists(TRACKS_CONFIG_PATH):
        return []

    with open(TRACKS_CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    result = []
    for item in data:
        track_file = item["file"]

        result.append({
            "id": item["id"],
            "name": item["name"],
            "file": track_file,
            "preview": build_preview_path(track_file)
        })

    return result