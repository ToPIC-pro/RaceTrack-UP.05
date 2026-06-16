import tkinter as tk


class Settings:

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

        self.create_close_button()

        self.menu.create_label(
            text=self.menu.t("settings"),
            font_scale=0.035,
            pady=int(self.screen_height * 0.05),
            bold=True
        )

        self.menu.create_label(
            text=self.menu.t("language"),
            font_scale=0.018,
            pady=10
        )

        self.ru_button = self.menu.create_button(
            self.frame,
            text=self.menu.t("russian"),
            command=lambda: self.set_language("ru"),
            width=25,
            height=1,
            font_scale=0.012
        )
        self.ru_button.pack(pady=5)

        self.en_button = self.menu.create_button(
            self.frame,
            text=self.menu.t("english"),
            command=lambda: self.set_language("en"),
            width=25,
            height=1,
            font_scale=0.012
        )
        self.en_button.pack(pady=5)

        self.menu.create_label(
            text=self.menu.t("theme"),
            font_scale=0.02,
            pady=10
        )

        self.blue_button = self.menu.create_button(
            self.frame,
            text=self.menu.t("blue_theme"),
            command=lambda: self.set_theme("blue"),
            width=25,
            height=1,
            font_scale=0.012
        )
        self.blue_button.pack(pady=5)

        self.red_button = self.menu.create_button(
            self.frame,
            text=self.menu.t("red_theme"),
            command=lambda: self.set_theme("red"),
            width=25,
            height=1,
            font_scale=0.012
        )
        self.red_button.pack(pady=5)

        self.purple_button = self.menu.create_button(
            self.frame,
            text=self.menu.t("purple_theme"),
            command=lambda: self.set_theme("purple"),
            width=25,
            height=1,
            font_scale=0.012
        )
        self.purple_button.pack(pady=5)

        self.apply_selected_styles()

    def clear_frame(self):
        for widget in self.frame.winfo_children():
            widget.destroy()

    def create_close_button(self):
        self.menu.create_icon_button(
            x=self.screen_width - 40,
            y=40,
            icon="✕",
            command=self.back
        )

    def apply_selected_styles(self):
        all_buttons = [
            self.ru_button,
            self.en_button,
            self.blue_button,
            self.red_button,
            self.purple_button
        ]

        for button in all_buttons:
            self.menu.apply_button_style(button, selected=False)

        if self.menu.language == "ru":
            self.menu.apply_button_style(self.ru_button, selected=True)
        else:
            self.menu.apply_button_style(self.en_button, selected=True)

        if self.menu.theme == "blue":
            self.menu.apply_button_style(self.blue_button, selected=True)
        elif self.menu.theme == "red":
            self.menu.apply_button_style(self.red_button, selected=True)
        elif self.menu.theme == "purple":
            self.menu.apply_button_style(self.purple_button, selected=True)

    def set_language(self, lang):
        self.menu.language = lang
        self.menu.save_settings()
        self.create_ui()

    def set_theme(self, theme):
        self.menu.theme = theme
        self.menu.save_settings()
        self.create_ui()

    def back(self):
        self.menu.create_menu()