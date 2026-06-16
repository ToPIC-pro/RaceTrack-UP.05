import tkinter as tk
from settings import Settings
from load_menu import LoadMenu
from new_game_menu import NewGameMenu
from app_config import load_config, save_config, get_theme, tr


class Menu:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Гонки на бумаге")

        self.root.attributes("-fullscreen", True)
        self.root.bind("<Escape>", lambda e: self.root.destroy())

        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()

        config = load_config()
        self.theme = config["theme"]
        self.language = config["language"]

        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True)

        self.create_menu()
        self.root.mainloop()

    # ================= CONFIG =================

    def get_colors(self):
        return get_theme(self.theme)

    def t(self, key, **kwargs):
        return tr(self.language, key, **kwargs)

    def save_settings(self):
        save_config({
            "theme": self.theme,
            "language": self.language
        })

    # ================= BASE UI =================

    def clear_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def get_font(self, scale, bold=False):
        size = int(self.screen_width * scale)
        return ("Arial", size, "bold") if bold else ("Arial", size)

    def create_canvas_screen(self):
        colors = self.get_colors()

        self.canvas = tk.Canvas(
            self.main_frame,
            width=self.screen_width,
            height=self.screen_height,
            bg=colors["bg"],
            highlightthickness=0
        )
        self.canvas.place(x=0, y=0)
        self.draw_grid()

        return self.canvas

    def draw_grid(self):
        colors = self.get_colors()
        grid_size = 40

        for x in range(0, self.screen_width, grid_size):
            self.canvas.create_line(
                x, 0, x, self.screen_height,
                fill=colors["grid"]
            )

        for y in range(0, self.screen_height, grid_size):
            self.canvas.create_line(
                0, y, self.screen_width, y,
                fill=colors["grid"]
            )

    def create_label(self, text, font_scale, pady=0, bold=False):
        colors = self.get_colors()

        label = tk.Label(
            self.main_frame,
            text=text,
            font=self.get_font(font_scale, bold=bold),
            bg=colors["bg"],
            fg=colors["text"]
        )
        label.pack(pady=pady)
        return label

    # ================= BUTTON STYLES =================

    def apply_button_style(self, button, selected=False, danger=False):
        colors = self.get_colors()

        bg = colors.get("button_bg", colors["panel"])
        fg = colors.get("button_text", colors["text"])
        active_bg = colors.get("button_hover", colors["accent"])
        active_fg = colors.get("button_text", colors["text"])
        border = colors.get("button_border", colors["accent"])

        if danger:
            bg = colors.get("button_danger_bg", "#f4c2c2")
            active_bg = colors.get("button_danger_hover", colors["danger"])

        if selected:
            bg = colors.get("button_selected_bg", colors["accent"])
            fg = colors.get("button_selected_text", "#ffffff")
            active_bg = colors.get("button_selected_bg", colors["accent"])
            active_fg = colors.get("button_selected_text", "#ffffff")
            border = colors.get("button_selected_bg", colors["accent"])

        button.config(
            bg=bg,
            fg=fg,
            activebackground=active_bg,
            activeforeground=active_fg,
            relief="solid",
            bd=1,
            highlightthickness=1,
            highlightbackground=border,
            highlightcolor=border,
            disabledforeground="#6b7280",
            cursor="hand2"
        )

    def create_button(
        self,
        parent,
        text,
        command,
        width=20,
        height=2,
        font_scale=0.015,
        selected=False,
        danger=False
    ):
        button = tk.Button(
            parent,
            text=text,
            width=width,
            height=height,
            font=self.get_font(font_scale),
            command=command,
            padx=8,
            pady=4
        )
        self.apply_button_style(button, selected=selected, danger=danger)
        return button

    def create_icon_button(self, x, y, icon, command):
        colors = self.get_colors()

        item = self.canvas.create_text(
            x,
            y,
            text=icon,
            font=("Arial", 24),
            fill=colors["text"]
        )

        self.canvas.tag_bind(item, "<Button-1>", lambda e: command())
        self.canvas.tag_bind(
            item,
            "<Enter>",
            lambda e: self.canvas.itemconfig(item, fill=colors["accent"])
        )
        self.canvas.tag_bind(
            item,
            "<Leave>",
            lambda e: self.canvas.itemconfig(item, fill=colors["text"])
        )

        return item

    # ================= MENU DECOR =================

    def draw_menu_trajectory(self):
        """
        Декоративная траектория по центру между заголовком и кнопками.
        Точки лежат прямо на линии, траектория немного сдвинута вправо.
        """
        colors = self.get_colors()

        cx = self.screen_width // 2
        cy = int(self.screen_height * 0.34)

        # Небольшой сдвиг вправо
        shift_x = 22

        points = [
            (cx - 185 + shift_x, cy + 18),
            (cx - 85 + shift_x, cy - 9),
            (cx + 55 + shift_x, cy - 30),
            (cx + 145 + shift_x, cy - 50),
        ]

        current_index = 1
        current_x, current_y = points[current_index]

        # Основная видимая линия
        visible_path = points[:current_index + 2]
        flat_visible = [coord for point in visible_path for coord in point]

        self.canvas.create_line(
            *flat_visible,
            fill=colors["accent"],
            width=4,
            smooth=False,
            capstyle="round",
            joinstyle="round"
        )

        # Светлая линия-продолжение
        ghost_line_points = points[current_index + 1:]
        if len(ghost_line_points) >= 2:
            flat_ghost = [coord for point in ghost_line_points for coord in point]
            self.canvas.create_line(
                *flat_ghost,
                fill="#cfc9ff",
                width=3,
                smooth=False,
                capstyle="round",
                joinstyle="round"
            )

        # Текущая точка
        r_main = 5
        self.canvas.create_oval(
            current_x - r_main,
            current_y - r_main,
            current_x + r_main,
            current_y + r_main,
            fill=colors["accent"],
            outline=colors["accent"]
        )

        # Предыдущая точка
        prev_x, prev_y = points[current_index - 1]
        r_prev = 4
        self.canvas.create_oval(
            prev_x - r_prev,
            prev_y - r_prev,
            prev_x + r_prev,
            prev_y + r_prev,
            fill=colors["accent"],
            outline=colors["accent"]
        )

        # Следующая точка
        next_x, next_y = points[current_index + 1]
        r_next = 5
        self.canvas.create_oval(
            next_x - r_next,
            next_y - r_next,
            next_x + r_next,
            next_y + r_next,
            fill=colors["accent"],
            outline=colors["accent"]
        )

    # ================= MAIN MENU =================

    def create_menu(self):
        self.clear_frame()
        self.create_canvas_screen()
        self.draw_menu_trajectory()

        # заголовок чуть ниже, но совсем немного
        self.create_label(
            text=self.t("main_title"),
            font_scale=0.05,
            pady=int(self.screen_height * 0.07),
            bold=True
        )

        self.create_menu_buttons()
        self.create_settings_button()

    def create_menu_buttons(self):
        # кнопки чуть выше
        new_button = self.create_button(
            self.main_frame,
            text=self.t("new_game"),
            command=self.new_game
        )
        new_button.pack(pady=(int(self.screen_height * 0.132), 15))

        load_button = self.create_button(
            self.main_frame,
            text=self.t("load_game"),
            command=self.load_game
        )
        load_button.pack(pady=15)

        exit_button = self.create_button(
            self.main_frame,
            text=self.t("exit"),
            command=self.confirm_exit,
            danger=True
        )
        exit_button.pack(pady=15)

    def create_settings_button(self):
        self.create_icon_button(
            x=self.screen_width - 40,
            y=40,
            icon="⚙",
            command=self.open_settings
        )

    # ================= NAVIGATION =================

    def open_settings(self):
        self.clear_frame()
        Settings(self)

    def new_game(self):
        self.clear_frame()
        NewGameMenu(self)

    def load_game(self):
        self.clear_frame()
        LoadMenu(self)

    # ================= EXIT =================

    def confirm_exit(self):
        self.clear_frame()
        self.create_canvas_screen()

        self.create_label(
            text=self.t("exit_confirm"),
            font_scale=0.03,
            pady=int(self.screen_height * 0.15)
        )

        colors = self.get_colors()
        buttons_frame = tk.Frame(self.main_frame, bg=colors["bg"])
        buttons_frame.pack()

        confirm_btn = self.create_button(
            buttons_frame,
            text=self.t("confirm"),
            command=self.root.destroy,
            width=14,
            font_scale=0.015,
            danger=True
        )
        confirm_btn.pack(side="left", padx=20)

        cancel_btn = self.create_button(
            buttons_frame,
            text=self.t("cancel"),
            command=self.create_menu,
            width=14,
            font_scale=0.015
        )
        cancel_btn.pack(side="left", padx=20)

