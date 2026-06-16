import tkinter as tk
import json
import copy

from bots.bot import choose_bot_move
from save_manager import (
    write_save_to_slot,
    build_save_meta,
    push_new_save_to_top,
    promote_save_to_top,
    delete_save
)
from core import (
    check_collision_path as core_check_collision_path,
    check_collision_path_info as core_check_collision_path_info,
    check_checkpoint as core_check_checkpoint,
    check_finish as core_check_finish,
    get_possible_moves as core_get_possible_moves,
    apply_move as core_apply_move,
)


class Car:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.color = color
        self.path = [(x, y)]
        self.started = False
        self.checkpoint_index = 0
        self.just_crashed = False
        self.crash_axis = None


class Track:
    def __init__(self, data):
        self.width = data["width"]
        self.height = data["height"]

        self.start = [tuple(point) for point in data["start"]]
        self.finish = {tuple(point) for point in data["finish"]}
        self.walls = {tuple(point) for point in data["walls"]}
        self.spawn_positions = [tuple(point) for point in data["spawn_positions"]]

        self.checkpoints = [
            {tuple(point) for point in checkpoint}
            for checkpoint in data.get("checkpoints", [])
        ]

    def is_inside_bounds(self, x, y):
        return 0 <= x <= self.width and 0 <= y <= self.height

    def is_wall(self, x, y):
        return (x, y) in self.walls

    def is_finish(self, x, y):
        return (x, y) in self.finish


def load_track(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["walls"] = [tuple(w) for w in data["walls"]]
    data["start"] = [tuple(s) for s in data["start"]]
    data["finish"] = [tuple(f) for f in data["finish"]]
    data["spawn_positions"] = [tuple(p) for p in data["spawn_positions"]]
    data["checkpoints"] = [
        [tuple(p) for p in checkpoint]
        for checkpoint in data.get("checkpoints", [])
    ]

    return data


class Game:
    def __init__(
        self,
        menu,
        players,
        track_data,
        mode="local",
        difficulty=None,
        track_path=None,
        loaded_state=None,
        save_slot=None
    ):
        self.menu = menu
        self.root = menu.root
        self.frame = menu.main_frame

        self.screen_width = menu.screen_width
        self.screen_height = menu.screen_height

        self.mode = mode
        self.difficulty = difficulty or "normal"
        self.bot_player_index = 1 if mode == "bot" else None
        self.track_path = track_path
        self.save_slot = save_slot

        self.initial_players = copy.deepcopy(players)
        self.initial_track_data = copy.deepcopy(track_data)

        self.track = Track(track_data)

        self.cell_size = 25
        self.max_speed = 10
        self.show_debug_checkpoints = True

        self.map_width_px = self.track.width * self.cell_size
        self.map_height_px = self.track.height * self.cell_size

        self.offset_x = (self.screen_width - self.map_width_px) // 2
        self.offset_y = (self.screen_height - self.map_height_px) // 2

        spawn_positions = self.get_start_positions(len(players))
        self.cars = [
            self.create_car(spawn_positions[i], player["color"])
            for i, player in enumerate(players)
        ]

        self.current_player = 0

        if loaded_state is not None:
            self.restore_state(loaded_state)

        self.create_ui()

    # ================= БАЗОВОЕ =================

    def get_colors(self):
        return self.menu.get_colors()

    def t(self, key, **kwargs):
        return self.menu.t(key, **kwargs)

    def clear_frame(self):
        for widget in self.frame.winfo_children():
            widget.destroy()

    def create_ui(self):
        self.clear_frame()
        colors = self.get_colors()

        self.canvas = tk.Canvas(
            self.frame,
            width=self.screen_width,
            height=self.screen_height,
            bg=colors["bg"],
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self.on_click)

        self.create_game_buttons()
        self.draw()

        if self.is_bot_turn():
            self.root.after(300, self.make_bot_move)

    def create_action_button(self, parent, text, command, width=16):
        return self.menu.create_button(
            parent,
            text=text,
            command=command,
            width=width,
            height=1,
            font_scale=0.015
        )

    def create_small_action_button(self, parent, text, command, width=10):
        return self.menu.create_button(
            parent,
            text=text,
            command=command,
            width=width,
            height=1,
            font_scale=0.011
        )

    def create_game_buttons(self):
        pass

    def create_canvas_icon_button(self, x, y, icon, command):
        colors = self.get_colors()

        item = self.canvas.create_text(
            x,
            y,
            text=icon,
            font=("Arial", 40, "bold"),
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

    def draw_home_button(self):
        self.create_canvas_icon_button(
            x=self.screen_width - 40,
            y=40,
            icon="⌂",
            command=self.exit_to_menu
        )

    def exit_to_menu(self):
        self.auto_save()
        self.menu.create_menu()

    def create_centered_buttons_frame(self, rely=0.68):
        colors = self.get_colors()

        frame = tk.Frame(self.frame, bg=colors["bg"])
        frame.place(relx=0.5, rely=rely, anchor="center")
        return frame

    def create_car(self, position, color):
        x, y = position
        return Car(x, y, color)

    def get_start_positions(self, player_count):
        positions = self.track.spawn_positions

        if player_count > len(positions):
            raise ValueError("Игроков больше, чем стартовых позиций")

        start_index = (len(positions) - player_count) // 2
        end_index = start_index + player_count
        return positions[start_index:end_index]

    def grid_to_pixel(self, x, y):
        return (
            self.offset_x + x * self.cell_size,
            self.offset_y + y * self.cell_size
        )

    def draw_cell(self, x, y, fill, outline=""):
        px, py = self.grid_to_pixel(x, y)
        self.canvas.create_rectangle(
            px,
            py,
            px + self.cell_size,
            py + self.cell_size,
            fill=fill,
            outline=outline
        )

    def draw_circle(self, x, y, radius, fill, outline="", width=1):
        cx, cy = self.grid_to_pixel(x, y)
        self.canvas.create_oval(
            cx - radius,
            cy - radius,
            cx + radius,
            cy + radius,
            fill=fill,
            outline=outline,
            width=width
        )

    def draw_line(self, x1, y1, x2, y2, fill, width=2):
        px1, py1 = self.grid_to_pixel(x1, y1)
        px2, py2 = self.grid_to_pixel(x2, y2)

        self.canvas.create_line(
            px1,
            py1,
            px2,
            py2,
            fill=fill,
            width=width
        )

    # ================= СОХРАНЕНИЕ =================

    def serialize_state(self):
        return {
            "mode": self.mode,
            "difficulty": self.difficulty,
            "track_path": self.track_path,
            "track_data": self.initial_track_data,
            "current_player": self.current_player,
            "save_slot": self.save_slot,
            "players": [
                {"color": car.color}
                for car in self.cars
            ],
            "cars": [
                {
                    "x": car.x,
                    "y": car.y,
                    "vx": car.vx,
                    "vy": car.vy,
                    "color": car.color,
                    "path": car.path,
                    "started": car.started,
                    "checkpoint_index": car.checkpoint_index,
                    "just_crashed": car.just_crashed,
                    "crash_axis": car.crash_axis
                }
                for car in self.cars
            ]
        }

    def restore_state(self, state):
        self.current_player = state.get("current_player", 0)
        self.save_slot = state.get("save_slot", self.save_slot)

        cars_data = state.get("cars", [])
        for car, car_data in zip(self.cars, cars_data):
            car.x = car_data.get("x", car.x)
            car.y = car_data.get("y", car.y)
            car.vx = car_data.get("vx", 0)
            car.vy = car_data.get("vy", 0)
            car.color = car_data.get("color", car.color)
            car.path = [tuple(p) for p in car_data.get("path", [(car.x, car.y)])]
            car.started = car_data.get("started", False)
            car.checkpoint_index = car_data.get("checkpoint_index", 0)
            car.just_crashed = car_data.get("just_crashed", False)
            car.crash_axis = car_data.get("crash_axis", None)

    def auto_save(self):
        save_data = self.serialize_state()

        save_data["meta"] = build_save_meta(
            name="Автосохранение",
            track_name=self.track_path or ""
        )

        if self.save_slot is None:
            new_slot = push_new_save_to_top(save_data)
            self.save_slot = new_slot
            save_data["save_slot"] = new_slot
            write_save_to_slot(new_slot, save_data)
            return

        if self.save_slot != 0:
            new_slot = promote_save_to_top(self.save_slot, save_data)
            self.save_slot = new_slot
            save_data["save_slot"] = new_slot
            write_save_to_slot(new_slot, save_data)
            return

        save_data["save_slot"] = self.save_slot
        write_save_to_slot(self.save_slot, save_data)

    def clear_current_save(self):
        if self.save_slot is None:
            return

        delete_save(self.save_slot)
        self.save_slot = None

    @classmethod
    def from_save(cls, menu, save_data):
        track_data = save_data.get("track_data")
        players = save_data.get("players", [])

        return cls(
            menu=menu,
            players=players,
            track_data=track_data,
            mode=save_data.get("mode", "local"),
            difficulty=save_data.get("difficulty"),
            track_path=save_data.get("track_path"),
            loaded_state=save_data,
            save_slot=save_data.get("save_slot")
        )

    # ================= БОТ =================

    def is_bot_turn(self):
        return self.bot_player_index is not None and self.current_player == self.bot_player_index

    def make_bot_move(self):
        if not self.is_bot_turn():
            return

        car = self.cars[self.current_player]
        move = choose_bot_move(self, car, self.difficulty)

        if move is None:
            self.next_player()
            return

        gx, gy = move
        self.perform_move(gx, gy)

    # ================= WRAPPERS К CORE =================

    def check_collision_path(self, x1, y1, x2, y2):
        return core_check_collision_path(self.track, x1, y1, x2, y2)



    def check_collision_info(self, x1, y1, x2, y2):
        return core_check_collision_path_info(self.track.walls, x1, y1, x2, y2)

    def check_checkpoint(self, car, nx, ny):
        return core_check_checkpoint(self.track, car, nx, ny)

    def check_finish(self, car, nx, ny, checkpoint_now=False):
        return core_check_finish(self.track, car, nx, ny, checkpoint_now)

    def get_possible_moves(self, car):
        return core_get_possible_moves(self.track, car, self.max_speed)

    # ================= ОТРИСОВКА =================

    def draw(self):
        self.canvas.delete("all")
        self.draw_grid()
        self.draw_walls()
        self.draw_finish()
        # if self.show_debug_checkpoints:
        #     self.draw_checkpoints()
        self.draw_cars()
        self.draw_possible_moves()
        self.draw_home_button()

    def draw_grid(self):
        colors = self.get_colors()

        for x in range(self.track.width + 1):
            px = self.offset_x + x * self.cell_size
            self.canvas.create_line(
                px,
                self.offset_y,
                px,
                self.offset_y + self.map_height_px,
                fill=colors["grid"]
            )

        for y in range(self.track.height + 1):
            py = self.offset_y + y * self.cell_size
            self.canvas.create_line(
                self.offset_x,
                py,
                self.offset_x + self.map_width_px,
                py,
                fill=colors["grid"]
            )

    def draw_walls(self):
        colors = self.get_colors()

        for x, y in self.track.walls:
            self.draw_cell(x, y, fill=colors["text"], outline="")

    def draw_finish(self):
        for x, y in self.track.finish:
            self.draw_finish_cell(x, y)

    def draw_finish_cell(self, x, y):
        self.draw_cell(x, y, fill="white", outline="")

        px, py = self.grid_to_pixel(x, y)
        half = self.cell_size // 2

        if (x + y) % 2 == 0:
            self.canvas.create_rectangle(
                px, py,
                px + half, py + half,
                fill="black",
                outline=""
            )
            self.canvas.create_rectangle(
                px + half, py + half,
                px + self.cell_size, py + self.cell_size,
                fill="black",
                outline=""
            )
        else:
            self.canvas.create_rectangle(
                px + half, py,
                px + self.cell_size, py + half,
                fill="black",
                outline=""
            )
            self.canvas.create_rectangle(
                px, py + half,
                px + half, py + self.cell_size,
                fill="black",
                outline=""
            )

    def draw_checkpoints(self):
        checkpoint_colors = [
            "#00ffaa",
            "#00ccff",
            "#ffaa00",
            "#ff66cc",
            "#aaff00",
            "#ffffff"
        ]

        for i, checkpoint in enumerate(self.track.checkpoints):
            color = checkpoint_colors[i % len(checkpoint_colors)]

            if not checkpoint:
                continue

            for x, y in checkpoint:
                px, py = self.grid_to_pixel(x, y)
                self.canvas.create_rectangle(
                    px,
                    py,
                    px + self.cell_size,
                    py + self.cell_size,
                    outline=color,
                    width=2
                )

            cx = sum(x for x, _ in checkpoint) / len(checkpoint)
            cy = sum(y for _, y in checkpoint) / len(checkpoint)

            px, py = self.grid_to_pixel(cx, cy)
            self.canvas.create_text(
                px,
                py,
                text=str(i + 1),
                fill=color,
                font=("Arial", 12, "bold")
            )

    def draw_cars(self):
        for i, car in enumerate(self.cars):
            self.draw_car_path(car)
            self.draw_car_marker(car, is_current=(i == self.current_player))

    def draw_car_path(self, car):
        for j in range(len(car.path) - 1):
            x1, y1 = car.path[j]
            x2, y2 = car.path[j + 1]
            self.draw_line(x1, y1, x2, y2, fill=car.color, width=2)

    def draw_car_marker(self, car, is_current=False):
        self.draw_circle(
            car.x,
            car.y,
            radius=9,
            fill=car.color,
            outline="white" if is_current else "",
            width=2 if is_current else 1
        )


    def draw_possible_moves(self):
        if self.is_bot_turn():
            return

        car = self.cars[self.current_player]
        for x, y in self.get_possible_moves(car):
            self.draw_circle(x, y, radius=5, fill=car.color)

    # ================= ЛОГИКА =================

    def on_click(self, event):
        if self.is_bot_turn():
            return

        car = self.cars[self.current_player]

        gx = round((event.x - self.offset_x) / self.cell_size)
        gy = round((event.y - self.offset_y) / self.cell_size)

        if (gx, gy) not in self.get_possible_moves(car):
            return

        self.perform_move(gx, gy)

    def perform_move(self, gx, gy):
        car = self.cars[self.current_player]
        result = core_apply_move(self.track, car, gx, gy)

        if result.finish_now:
            self.clear_current_save()
            self.show_win_screen(self.current_player)
            return

        self.next_player()
        self.auto_save()

    def next_player(self):
        self.current_player = (self.current_player + 1) % len(self.cars)
        self.draw()

        if self.is_bot_turn():
            self.root.after(300, self.make_bot_move)

    # ================= ПОБЕДА =================

    def restart_game(self):
        Game(
            self.menu,
            copy.deepcopy(self.initial_players),
            copy.deepcopy(self.initial_track_data),
            mode=self.mode,
            difficulty=self.difficulty,
            track_path=self.track_path,
            save_slot=self.save_slot
        )

    def show_win_screen(self, player_index):
        self.clear_frame()
        colors = self.get_colors()

        winner_car = self.cars[player_index]
        winner_color = winner_car.color

        canvas = tk.Canvas(
            self.frame,
            width=self.screen_width,
            height=self.screen_height,
            bg=colors["bg"],
            highlightthickness=0
        )
        canvas.pack(fill="both", expand=True)

        center_x = self.screen_width // 2
        base_y = self.screen_height // 3

        if self.mode == "bot" and player_index == self.bot_player_index:
            winner_name = self.t("bot_name")
        else:
            winner_name = self.t("winner_player", number=player_index + 1)

        canvas.create_text(
            center_x,
            base_y - 20,
            text=self.t("winner_title"),
            fill=colors["text"],
            font=("Arial", 34)
        )

        canvas.create_text(
            center_x,
            base_y + 35,
            text=winner_name,
            fill=winner_color,
            font=("Arial", 42, "bold")
        )

        r = 18
        circle_y = base_y + 95
        canvas.create_oval(
            center_x - r,
            circle_y - r,
            center_x + r,
            circle_y + r,
            fill=winner_color,
            outline="white",
            width=2
        )

        self.create_win_buttons()

    def create_win_buttons(self):
        buttons_frame = self.create_centered_buttons_frame(rely=0.68)

        buttons = [
            (self.t("new_game"), self.restart_game),
            (self.t("main_menu"), self.menu.create_menu),
        ]

        for text, command in buttons:
            self.create_action_button(
                buttons_frame,
                text=text,
                command=command,
                width=16
            ).pack(side="left", padx=15)