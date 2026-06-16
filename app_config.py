import json
import os


CONFIG_FILE = "config.json"


DEFAULT_CONFIG = {
    "theme": "blue",
    "language": "ru"
}


THEMES = {
    "blue": {
        "bg": "#1e2a38",
        "panel": "#2b3a4a",
        "grid": "#2b3a4a",
        "text": "#e8eef5",
        "accent": "#4aa3ff",
        "danger": "#ff6b6b",

        # Кнопки
        "button_bg": "#dbeafe",
        "button_text": "#102033",
        "button_hover": "#bfdbfe",
        "button_border": "#93c5fd",
        "button_selected_bg": "#4aa3ff",
        "button_selected_text": "#ffffff",
        "button_danger_bg": "#fecaca",
        "button_danger_hover": "#fca5a5",
    },

    "red": {
        "bg": "#2a1f1f",
        "panel": "#3a2b2b",
        "grid": "#4a3535",
        "text": "#f0e6e6",
        "accent": "#d96b6b",
        "danger": "#ff8a8a",

        # Кнопки
        "button_bg": "#fde2e2",
        "button_text": "#2a1111",
        "button_hover": "#f9caca",
        "button_border": "#e9a7a7",
        "button_selected_bg": "#d96b6b",
        "button_selected_text": "#ffffff",
        "button_danger_bg": "#fecaca",
        "button_danger_hover": "#fca5a5",
    },

    "purple": {
        "bg": "#221f2a",
        "panel": "#332b3d",
        "grid": "#423a4d",
        "text": "#eae6f2",
        "accent": "#a78bfa",
        "danger": "#ff8ad4",

        # Кнопки
        "button_bg": "#ede9fe",
        "button_text": "#211636",
        "button_hover": "#ddd6fe",
        "button_border": "#c4b5fd",
        "button_selected_bg": "#a78bfa",
        "button_selected_text": "#ffffff",
        "button_danger_bg": "#fbcfe8",
        "button_danger_hover": "#f9a8d4",
    }
}


TEXTS = {
    "ru": {
        # Общие
        "main_title": "ГОНКИ НА БУМАГЕ",
        "back": "Назад",
        "next": "Далее →",
        "delete": "Удалить",
        "load": "Загрузить",
        "start_game": "Начать игру",
        "settings": "Настройки",
        "language": "Язык",
        "theme": "Оформление",

        # Меню
        "new_game": "Новая гонка",
        "load_game": "Загрузить гонку",
        "exit": "Выход",

        # Выход
        "exit_confirm": "Вы уверены, что хотите выйти?",
        "confirm": "Подтвердить",
        "cancel": "Отмена",

        # Настройки
        "russian": "Русский",
        "english": "English",
        "blue_theme": "Синий",
        "red_theme": "Красный",
        "purple_theme": "Фиолетовый",

        # Загрузка
        "load_race": "Загрузить гонку",
        "no_saves": "Нет сохраненных игр",
        "save_name": "Гонка #{number}",

        # Новая игра: режим
        "select_mode": "Выберите режим игры",
        "local_multiplayer": "Локальный\nМультиплеер",
        "bot": "Бот",
        "bot_difficulty": "Сложность бота",
        "normal": "Обычный",
        "hard": "Продвинутый",

        # Новая игра: трасса
        "select_track": "Выберите трассу",
        "track": "Трасса {number}",

        # Игроки
        "players_setup": "Настройка игроков",
        "player": "Игрок",
        "player_name": "Игрок {number}",
        "bot_name": "Бот",
        "add_player": "Добавить игрока",

        # Ошибки выбора игроков
        "error_choose_colors": "Не все игроки выбрали цвет",
        "error_unique_colors": "У игроков не должны совпадать цвета",

        # Игра
        "turn_player": "Ход: Игрок {number}",
        "turn_bot": "Ход: Бот",
        "winner_title": "Победил",
        "winner_player": "Игрок {number}",
        "winner_full": "Игрок {number} победил!",
        "main_menu": "Главное меню",
        "to_menu": "В меню"
    },

    "en": {
        # Общие
        "main_title": "PAPER RACING",
        "back": "Back",
        "next": "Next →",
        "delete": "Delete",
        "load": "Load",
        "start_game": "Start Game",
        "settings": "Settings",
        "language": "Language",
        "theme": "Theme",

        # Меню
        "new_game": "New Game",
        "load_game": "Load Game",
        "exit": "Exit",

        # Выход
        "exit_confirm": "Are you sure you want to exit?",
        "confirm": "Confirm",
        "cancel": "Cancel",

        # Настройки
        "russian": "Russian",
        "english": "English",
        "blue_theme": "Blue",
        "red_theme": "Red",
        "purple_theme": "Purple",

        # Загрузка
        "load_race": "Load Race",
        "no_saves": "No saved games",
        "save_name": "Race #{number}",

        # Новая игра: режим
        "select_mode": "Select game mode",
        "local_multiplayer": "Local\nMultiplayer",
        "bot": "Bot",
        "bot_difficulty": "Bot difficulty",
        "normal": "Normal",
        "hard": "Advanced",

        # Новая игра: трасса
        "select_track": "Select track",
        "track": "Track {number}",

        # Игроки
        "players_setup": "Players setup",
        "player": "Player",
        "player_name": "Player {number}",
        "bot_name": "Bot",
        "add_player": "Add Player",

        # Ошибки выбора игроков
        "error_choose_colors": "Not all players selected a color",
        "error_unique_colors": "Players must have different colors",

        # Игра
        "turn_player": "Turn: Player {number}",
        "turn_bot": "Turn: Bot",
        "winner_title": "Winner",
        "winner_player": "Player {number}",
        "winner_full": "Player {number} wins!",
        "main_menu": "Main Menu",
        "to_menu": "To Menu"
    }
}


def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    config = DEFAULT_CONFIG.copy()
    config.update(data)

    if config["theme"] not in THEMES:
        config["theme"] = DEFAULT_CONFIG["theme"]

    if config["language"] not in TEXTS:
        config["language"] = DEFAULT_CONFIG["language"]

    return config


def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def get_theme(theme_name):
    return THEMES.get(theme_name, THEMES[DEFAULT_CONFIG["theme"]])


def get_texts(language):
    return TEXTS.get(language, TEXTS[DEFAULT_CONFIG["language"]])


def tr(language, key, **kwargs):
    text = get_texts(language).get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text