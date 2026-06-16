import tkinter as tk
from save_manager import list_saves, load_save, delete_save
from game import Game


class LoadMenu:

    def __init__(self, menu):
        self.menu = menu
        self.root = menu.root
        self.frame = menu.main_frame

        self.screen_width = menu.screen_width
        self.screen_height = menu.screen_height

        self.create_ui()

    def create_ui(self):
        self.clear_frame()
        self.menu.create_canvas_screen()
        self.create_back_button()

        self.menu.create_label(
            text=self.menu.t("load_game"),
            font_scale=0.035,
            pady=int(self.screen_height * 0.06),
            bold=True
        )

        colors = self.menu.get_colors()
        self.list_frame = tk.Frame(self.frame, bg=colors["bg"])
        self.list_frame.pack()

        self.refresh_list()

    def clear_frame(self):
        for widget in self.frame.winfo_children():
            widget.destroy()

    def refresh_list(self):
        colors = self.menu.get_colors()
        font_size = int(self.screen_width * 0.012)

        for widget in self.list_frame.winfo_children():
            widget.destroy()

        saves = list_saves()

        if not any(saves):
            empty_label = tk.Label(
                self.list_frame,
                text=self.menu.t("no_saves"),
                bg=colors["bg"],
                fg=colors["text"],
                font=("Arial", font_size)
            )
            empty_label.pack(pady=20)
            return

        for index, save in enumerate(saves):
            row = tk.Frame(self.list_frame, bg=colors["bg"])
            row.pack(pady=8)

            if save is None:
                name_text = f"{self.menu.t('save_name', number=index + 1)} — пусто"
            else:
                timestamp = save.get("timestamp", "")
                mode = save.get("mode", "")
                mode_text = "Бот" if mode == "bot" else "Локальный"
                if self.menu.language == "en":
                    mode_text = "Bot" if mode == "bot" else "Local"

                if timestamp:
                    name_text = f"{self.menu.t('save_name', number=index + 1)} — {mode_text} — {timestamp}"
                else:
                    name_text = f"{self.menu.t('save_name', number=index + 1)} — {mode_text}"

            name = tk.Label(
                row,
                text=name_text,
                width=45,
                anchor="w",
                bg=colors["bg"],
                fg=colors["text"],
                font=("Arial", font_size)
            )
            name.pack(side="left", padx=10)

            load_btn = self.menu.create_button(
                row,
                text=self.menu.t("load"),
                command=lambda slot=index: self.load_game(slot),
                width=12,
                height=1,
                font_scale=0.012
            )
            load_btn.pack(side="left", padx=5)

            if save is None:
                load_btn.config(state="disabled")

            delete_btn = self.menu.create_button(
                row,
                text=self.menu.t("delete"),
                command=lambda slot=index: self.delete_save(slot),
                width=12,
                height=1,
                font_scale=0.012
            )
            delete_btn.pack(side="left", padx=5)

            if save is None:
                delete_btn.config(state="disabled")

    def load_game(self, slot):
        save_data = load_save(slot)
        if save_data is None:
            return

        Game.from_save(self.menu, save_data)

    def delete_save(self, slot):
        delete_save(slot)
        self.refresh_list()

    def create_back_button(self):
        self.menu.create_icon_button(
            x=40,
            y=40,
            icon="←",
            command=self.menu.create_menu
        )