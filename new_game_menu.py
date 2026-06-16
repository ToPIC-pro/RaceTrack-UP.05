import os
import tkinter as tk
from PIL import Image, ImageTk

from game import Game, load_track


class NewGameMenu:

    def __init__(self, menu):
        self.menu = menu
        self.root = menu.root
        self.frame = menu.main_frame

        self.screen_width = menu.screen_width
        self.screen_height = menu.screen_height

        self.selected_mode = None
        self.selected_difficulty = None
        self.selected_track = None

        self.players = []

        self.current_screen = "mode"
        self.error_label = None

        self.track_preview_images = []

        self.create_ui()

    def create_ui(self):
        self.show_mode_screen()

    # ===================== БАЗОВОЕ =====================

    def clear_frame(self):
        for widget in self.frame.winfo_children():
            widget.destroy()

    def colors(self):
        return self.menu.get_colors()

    def create_screen(self):
        self.clear_frame()
        self.menu.create_canvas_screen()
        self.create_back_button()

    def create_title(self, text, scale=0.035, pady=None):
        if pady is None:
            pady = int(self.screen_height * 0.06)

        self.menu.create_label(
            text=text,
            font_scale=scale,
            pady=pady,
            bold=True
        )

    def create_back_button(self):
        self.menu.create_icon_button(
            x=40,
            y=40,
            icon="←",
            command=self.go_back
        )

    def create_next_button(self):
        self.menu.create_button(
            self.frame,
            text=self.menu.t("next"),
            command=self.next_step,
            width=14,
            height=1,
            font_scale=0.012
        ).place(relx=0.5, rely=0.9, anchor="center")

    def create_panel_frame(self, parent, width=None, height=None, bg=None, border_color=None):
        colors = self.colors()

        if bg is None:
            bg = colors["panel"]
        if border_color is None:
            border_color = bg

        frame = tk.Frame(
            parent,
            bg=bg,
            highlightthickness=2,
            highlightbackground=border_color
        )

        if width is not None and height is not None:
            frame.config(width=width, height=height)
            frame.pack_propagate(False)

        return frame

    def style_button_selected(self, button, selected):
        self.menu.apply_button_style(button, selected=selected)

    # ===================== PREVIEW =====================

    def get_track_preview_path(self, index):
        return os.path.join("tracks", f"track{index + 1}_preview.png")

    def load_track_preview(self, index, size):
        path = self.get_track_preview_path(index)

        if not os.path.exists(path):
            return None

        try:
            image = Image.open(path)
            image = image.resize(size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(image)
        except Exception:
            return None

    def create_preview_widget(self, parent, index):
        colors = self.colors()

        preview_width = int(self.screen_width * 0.175)
        preview_height = int(self.screen_height * 0.175)

        preview_container = tk.Frame(
            parent,
            bg=colors["bg"],
            width=preview_width,
            height=preview_height,
            highlightthickness=0,
            bd=0
        )
        preview_container.pack(pady=(0, 10))
        preview_container.pack_propagate(False)

        image = self.load_track_preview(index, (preview_width, preview_height))

        if image is not None:
            self.track_preview_images.append(image)

            label = tk.Label(
                preview_container,
                image=image,
                bg=colors["bg"],
                bd=0,
                highlightthickness=0
            )
            label.place(x=0, y=0, relwidth=1, relheight=1)
            return preview_container, label

        label = tk.Label(
            preview_container,
            text="Нет превью",
            bg=colors["bg"],
            fg=colors["text"],
            font=self.menu.get_font(0.01),
            bd=0,
            highlightthickness=0
        )
        label.place(x=0, y=0, relwidth=1, relheight=1)

        return preview_container, label

    # ===================== SCREEN 1 =====================

    def show_mode_screen(self):
        self.create_screen()

        self.create_title(
            self.menu.t("select_mode"),
            scale=0.035,
            pady=int(self.screen_height * 0.08)
        )

        colors = self.colors()

        self.cards_frame = tk.Frame(self.frame, bg=colors["bg"])
        self.cards_frame.pack()

        self.local_card = self.create_card(self.menu.t("local_multiplayer"), "local")
        self.bot_card = self.create_card(self.menu.t("bot"), "bot")

        self.local_card.pack(side="left", padx=40)
        self.bot_card.pack(side="left", padx=40)

        self.difficulty_frame = tk.Frame(self.frame, bg=colors["bg"])

        self.create_next_button()
        self.current_screen = "mode"

        if self.selected_mode:
            self.select_mode(self.selected_mode)

    def create_card(self, text, mode):
        colors = self.colors()

        card = self.create_panel_frame(
            self.cards_frame,
            width=int(self.screen_width * 0.18),
            height=int(self.screen_height * 0.25),
            bg=colors["panel"],
            border_color=colors["panel"]
        )

        label = tk.Label(
            card,
            text=text,
            font=self.menu.get_font(0.013),
            bg=colors["panel"],
            fg=colors["text"],
            justify="center"
        )
        label.pack(expand=True)

        card.bind("<Button-1>", lambda e: self.select_mode(mode))
        label.bind("<Button-1>", lambda e: self.select_mode(mode))

        return card

    def select_mode(self, mode):
        colors = self.colors()

        previous_mode = self.selected_mode

        if previous_mode != mode:
            self.players = []
            self.selected_difficulty = None
            self.error_label = None

        self.selected_mode = mode

        self.local_card.config(bg=colors["panel"], highlightbackground=colors["panel"])
        self.bot_card.config(bg=colors["panel"], highlightbackground=colors["panel"])

        for child in self.local_card.winfo_children():
            child.config(bg=colors["panel"], fg=colors["text"])
        for child in self.bot_card.winfo_children():
            child.config(bg=colors["panel"], fg=colors["text"])

        for widget in self.difficulty_frame.winfo_children():
            widget.destroy()
        self.difficulty_frame.pack_forget()

        if mode == "local":
            self.local_card.config(bg=colors["accent"], highlightbackground=colors["accent"])
            for child in self.local_card.winfo_children():
                child.config(bg=colors["accent"], fg=colors["text"])

        elif mode == "bot":
            self.bot_card.config(bg=colors["accent"], highlightbackground=colors["accent"])
            for child in self.bot_card.winfo_children():
                child.config(bg=colors["accent"], fg=colors["text"])
            self.show_difficulty()

    def show_difficulty(self):
        colors = self.colors()

        tk.Label(
            self.difficulty_frame,
            text=self.menu.t("bot_difficulty"),
            font=self.menu.get_font(0.02),
            bg=colors["bg"],
            fg=colors["text"]
        ).pack(pady=10)

        buttons_frame = tk.Frame(self.difficulty_frame, bg=colors["bg"])
        buttons_frame.pack()

        self.easy_btn = self.menu.create_button(
            buttons_frame,
            text=self.menu.t("normal"),
            command=lambda: self.select_difficulty("normal"),
            width=15,
            height=1,
            font_scale=0.012
        )
        self.easy_btn.pack(side="left", padx=10)

        self.hard_btn = self.menu.create_button(
            buttons_frame,
            text=self.menu.t("hard"),
            command=lambda: self.select_difficulty("hard"),
            width=15,
            height=1,
            font_scale=0.012
        )
        self.hard_btn.pack(side="left", padx=10)

        self.difficulty_frame.pack(pady=20)

        if self.selected_difficulty:
            self.select_difficulty(self.selected_difficulty)

    def select_difficulty(self, level):
        self.selected_difficulty = level

        self.style_button_selected(self.easy_btn, level == "normal")
        self.style_button_selected(self.hard_btn, level == "hard")

    # ===================== SCREEN 2 =====================

    def show_track_screen(self):
        self.create_screen()
        self.create_title(self.menu.t("select_track"))

        colors = self.colors()
        self.track_preview_images = []

        tracks_frame = tk.Frame(self.frame, bg=colors["bg"])
        tracks_frame.pack(pady=(0, 30))

        self.track_cards = []

        card_width = int(self.screen_width * 0.2)
        card_height = int(self.screen_height * 0.26)

        for i in range(4):
            card = self.create_panel_frame(
                tracks_frame,
                width=card_width,
                height=card_height,
                bg=colors["panel"],
                border_color=colors["panel"]
            )
            card.grid(row=i // 2, column=i % 2, padx=25, pady=25)
            card.pack_propagate(False)

            title = tk.Label(
                card,
                text=self.menu.t("track", number=i + 1),
                bg=colors["panel"],
                fg=colors["text"],
                font=self.menu.get_font(0.013)
            )
            title.pack(pady=(8, 6))

            preview, preview_label = self.create_preview_widget(card, i)

            card.bind("<Button-1>", lambda e, i=i: self.select_track(i))
            title.bind("<Button-1>", lambda e, i=i: self.select_track(i))
            preview.bind("<Button-1>", lambda e, i=i: self.select_track(i))
            preview_label.bind("<Button-1>", lambda e, i=i: self.select_track(i))

            self.track_cards.append((card, title, preview, preview_label))

        self.create_next_button()
        self.current_screen = "track"

        if self.selected_track is not None:
            self.select_track(self.selected_track)

    def select_track(self, index):
        colors = self.colors()
        self.selected_track = index

        for card, title, preview, _preview_label in self.track_cards:
            card.config(bg=colors["panel"], highlightbackground=colors["panel"])
            title.config(bg=colors["panel"], fg=colors["text"])
            preview.config(bg=colors["bg"])

        card, title, preview, _preview_label = self.track_cards[index]
        card.config(bg=colors["accent"], highlightbackground=colors["accent"])
        title.config(bg=colors["accent"], fg=colors["text"])
        preview.config(bg=colors["panel"])

    # ===================== SCREEN 3 =====================

    def show_players_screen(self):
        self.create_screen()
        self.create_title(self.menu.t("players_setup"), scale=0.03, pady=20)

        colors = self.colors()

        self.players_frame = tk.Frame(self.frame, bg=colors["bg"])
        self.players_frame.pack()

        if self.selected_mode == "bot":
            self.players = [
                {"name": self.menu.t("player_name", number=1), "color": None},
                {"name": self.menu.t("bot_name"), "color": None}
            ]
        else:
            if not self.players:
                self.players = [
                    {"name": self.menu.t("player_name", number=1), "color": None},
                    {"name": self.menu.t("player_name", number=2), "color": None}
                ]

        self.draw_players()

        if self.selected_mode == "local":
            self.add_player_button = self.menu.create_button(
                self.frame,
                text=self.menu.t("add_player"),
                command=self.add_player,
                width=18,
                height=1,
                font_scale=0.012
            )
            self.add_player_button.place(relx=0.5, rely=0.74, anchor="center")

            if len(self.players) >= 4:
                self.add_player_button.place_forget()

        self.error_label = tk.Label(
            self.frame,
            text="",
            font=self.menu.get_font(0.012),
            bg=colors["bg"],
            fg=colors["danger"]
        )
        self.error_label.place(relx=0.5, rely=0.80, anchor="center")

        self.start_button = self.menu.create_button(
            self.frame,
            text=self.menu.t("start_game"),
            command=self.start_game,
            width=20,
            height=2,
            font_scale=0.015
        )
        self.start_button.place(relx=0.5, rely=0.9, anchor="center")

        self.current_screen = "players"

    def draw_players(self):
        colors = self.colors()

        for widget in self.players_frame.winfo_children():
            widget.destroy()

        player_colors = ["blue", "red", "green", "yellow"]

        for i, player in enumerate(self.players):
            card = tk.Frame(self.players_frame, bg=colors["panel"])
            card.pack(pady=14, padx=30, fill="x")

            top = tk.Frame(card, bg=colors["panel"])
            top.pack(fill="x")

            tk.Label(
                top,
                text=player["name"],
                bg=colors["panel"],
                fg=colors["text"],
                font=self.menu.get_font(0.013)
            ).pack(side="left", padx=10)

            if self.selected_mode == "local" and len(self.players) > 2:
                delete_btn = self.menu.create_button(
                    top,
                    text=self.menu.t("delete"),
                    command=lambda i=i: self.remove_player(i),
                    width=8,
                    height=1,
                    font_scale=0.009
                )
                delete_btn.pack(side="right", padx=10)

            colors_frame = tk.Frame(card, bg=colors["panel"])
            colors_frame.pack(pady=14)

            for color in player_colors:
                is_selected = player["color"] == color

                btn = tk.Button(
                    colors_frame,
                    bg=color,
                    activebackground=color,
                    width=4,
                    height=1,
                    relief="solid",
                    bd=3 if is_selected else 1,
                    highlightthickness=2 if is_selected else 1,
                    highlightbackground="white" if is_selected else colors["panel"],
                    highlightcolor="white" if is_selected else colors["panel"],
                    command=lambda c=color, i=i: self.select_color(i, c)
                )
                btn.pack(side="left", padx=6, pady=4)

    def add_player(self):
        if len(self.players) < 4:
            self.players.append({
                "name": self.menu.t("player_name", number=len(self.players) + 1),
                "color": None
            })
            self.draw_players()

            if len(self.players) == 4:
                self.add_player_button.place_forget()

    def remove_player(self, index):
        self.players.pop(index)

        player_number = 1
        for player in self.players:
            if player["name"] != self.menu.t("bot_name"):
                player["name"] = self.menu.t("player_name", number=player_number)
                player_number += 1

        self.draw_players()

        if len(self.players) < 4 and self.selected_mode == "local":
            self.add_player_button.place(relx=0.5, rely=0.74, anchor="center")

    def select_color(self, player_index, color):
        self.players[player_index]["color"] = color

        if self.error_label:
            self.error_label.config(text="")

        self.draw_players()

    def get_used_colors(self):
        return [player["color"] for player in self.players if player["color"]]

    def start_game(self):
        if self.error_label:
            self.error_label.config(text="")

        for player in self.players:
            if not player["color"]:
                if self.error_label:
                    self.error_label.config(text=self.menu.t("error_choose_colors"))
                return

        selected_colors = [player["color"] for player in self.players]
        if len(selected_colors) != len(set(selected_colors)):
            if self.error_label:
                self.error_label.config(text=self.menu.t("error_unique_colors"))
            return

        track_path = f"tracks/track{self.selected_track + 1}.json"
        track_data = load_track(track_path)

        Game(
            self.menu,
            self.players,
            track_data,
            mode=self.selected_mode,
            difficulty=self.selected_difficulty,
            track_path=track_path
        )

    # ===================== НАВИГАЦИЯ =====================

    def next_step(self):
        if self.current_screen == "mode":
            if not self.selected_mode:
                return
            if self.selected_mode == "bot" and not self.selected_difficulty:
                return
            self.show_track_screen()

        elif self.current_screen == "track":
            if self.selected_track is None:
                return
            self.show_players_screen()

    def go_back(self):
        if self.current_screen == "mode":
            self.menu.create_menu()
        elif self.current_screen == "track":
            self.show_mode_screen()
        elif self.current_screen == "players":
            self.show_track_screen()