import math
from dataclasses import dataclass
from typing import Optional


EPS = 1e-9


@dataclass
class MoveResult:
    collision: bool
    final_x: int
    final_y: int
    new_vx: int
    new_vy: int
    hit_axis: Optional[str] = None  # "vertical", "horizontal" или None


@dataclass
class TurnResult:
    collision: bool
    checkpoint_now: bool
    finish_now: bool
    final_x: int
    final_y: int
    new_vx: int
    new_vy: int
    hit_axis: Optional[str] = None


# =========================================================
# Геометрия
# =========================================================

def segment_intersects_rect(x1, y1, x2, y2, rx, ry, rw=1.0, rh=1.0):
    interval = segment_rect_contact_interval(x1, y1, x2, y2, rx, ry, rw, rh)
    return interval is not None


def segment_rect_contact_interval(x1, y1, x2, y2, rx, ry, rw=1.0, rh=1.0):
    """
    Возвращает интервал t=[u1,u2], на котором отрезок касается
    закрытого прямоугольника [rx, rx+rw] x [ry, ry+rh].
    Если пересечения нет, возвращает None.
    """
    dx = x2 - x1
    dy = y2 - y1

    p = [-dx, dx, -dy, dy]
    q = [x1 - rx, rx + rw - x1, y1 - ry, ry + rh - y1]

    u1 = 0.0
    u2 = 1.0

    for pi, qi in zip(p, q):
        if pi == 0:
            if qi < 0:
                return None
        else:
            t = qi / pi
            if pi < 0:
                if t > u2:
                    return None
                if t > u1:
                    u1 = t
            else:
                if t < u1:
                    return None
                if t < u2:
                    u2 = t

    return u1, u2


def get_last_grid_point_before_t(x1, y1, x2, y2, t_limit):
    """
    Последняя целочисленная точка на траектории,
    лежащая строго раньше момента t_limit.
    """
    dx = x2 - x1
    dy = y2 - y1

    g = math.gcd(abs(dx), abs(dy))
    if g == 0:
        return x1, y1

    step_x = dx // g
    step_y = dy // g

    best_k = 0
    for k in range(1, g + 1):
        t = k / g
        if t < t_limit - EPS:
            best_k = k
        else:
            break

    return x1 + step_x * best_k, y1 + step_y * best_k


def get_grid_point_at_t_if_exists(x1, y1, x2, y2, t_hit):
    """
    Если момент столкновения t_hit совпадает с узлом сетки на траектории,
    возвращает эту точку. Иначе None.
    """
    dx = x2 - x1
    dy = y2 - y1

    g = math.gcd(abs(dx), abs(dy))
    if g == 0:
        return (x1, y1) if abs(t_hit) <= EPS else None

    step_x = dx // g
    step_y = dy // g

    k = round(t_hit * g)
    if 0 <= k <= g:
        t = k / g
        if abs(t - t_hit) <= EPS:
            return x1 + step_x * k, y1 + step_y * k

    return None


def get_stop_point_for_collision(x1, y1, x2, y2, t_hit):
    """
    Возвращает точку остановки при столкновении.

    Если удар произошёл в узле сетки —
    остаёмся в точке удара.

    Иначе останавливаемся в ближайшей
    целой точке ДО стены.
    """

    hit_point = get_grid_point_at_t_if_exists(
        x1, y1, x2, y2, t_hit
    )

    if hit_point is not None:
        return hit_point

    dx = x2 - x1
    dy = y2 - y1

    # Чуть-чуть отступаем назад от стены
    safe_t = max(0.0, t_hit - 1e-6)

    stop_x = round(x1 + dx * safe_t)
    stop_y = round(y1 + dy * safe_t)

    return stop_x, stop_y


def _approx_equal(a, b):
    return abs(a - b) <= EPS


def _axis_at_contact(x1, y1, x2, y2, wx, wy, t):
    """
    Определяет, о какую грань клетки-стены произошёл первый контакт:
    - vertical   -> левая/правая грань клетки
    - horizontal -> верхняя/нижняя грань клетки
    - None       -> удар в угол / неоднозначный случай
    """
    dx = x2 - x1
    dy = y2 - y1

    xt = x1 + dx * t
    yt = y1 + dy * t

    vertical = (
        (_approx_equal(xt, wx) or _approx_equal(xt, wx + 1))
        and (wy - EPS <= yt <= wy + 1 + EPS)
    )
    horizontal = (
        (_approx_equal(yt, wy) or _approx_equal(yt, wy + 1))
        and (wx - EPS <= xt <= wx + 1 + EPS)
    )

    if vertical and not horizontal:
        return "vertical"
    if horizontal and not vertical:
        return "horizontal"

    return None


def _merge_axes(axis_a, axis_b):
    if axis_a is None:
        return axis_b
    if axis_b is None:
        return axis_a
    if axis_a == axis_b:
        return axis_a
    return None


def check_collision_path_info(walls, x1, y1, x2, y2):
    """
    Возвращает:
        collision, stop_x, stop_y, hit_axis

    Логика:
    - касание стены только в стартовой точке разрешено;
    - любое дальнейшее касание, включая конечную точку, считается столкновением;
    - если удар произошёл точно в узле сетки, машина остаётся в точке удара;
    - иначе машина остаётся в последней целой точке до удара.
    """
    first_hit_t = None
    first_hit_axis = None

    for wx, wy in walls:
        interval = segment_rect_contact_interval(x1, y1, x2, y2, wx, wy, 1.0, 1.0)
        if interval is None:
            continue

        u1, u2 = interval

        # Разрешаем только касание в стартовой точке
        if u2 <= EPS:
            continue

        # Любое следующее касание — столкновение, включая конец хода
        hit_t = max(u1, 0.0)
        hit_axis = _axis_at_contact(x1, y1, x2, y2, wx, wy, hit_t)

        if first_hit_t is None or hit_t < first_hit_t - EPS:
            first_hit_t = hit_t
            first_hit_axis = hit_axis
        elif abs(hit_t - first_hit_t) <= EPS:
            first_hit_axis = _merge_axes(first_hit_axis, hit_axis)

    if first_hit_t is None:
        return False, x2, y2, None

    stop_x, stop_y = get_stop_point_for_collision(x1, y1, x2, y2, first_hit_t)
    return True, stop_x, stop_y, first_hit_axis


def check_collision_path(track, x1, y1, x2, y2):
    collision, safe_x, safe_y, _ = check_collision_path_info(track.walls, x1, y1, x2, y2)
    return collision, safe_x, safe_y


def resolve_move(track, x1, y1, x2, y2):
    collision, final_x, final_y, hit_axis = check_collision_path_info(
        track.walls, x1, y1, x2, y2
    )

    if collision:
        return MoveResult(
            collision=True,
            final_x=final_x,
            final_y=final_y,
            new_vx=0,
            new_vy=0,
            hit_axis=hit_axis
        )

    return MoveResult(
        collision=False,
        final_x=x2,
        final_y=y2,
        new_vx=x2 - x1,
        new_vy=y2 - y1,
        hit_axis=None
    )


# =========================================================
# Игровые правила
# =========================================================

def check_checkpoint(track, car, nx, ny):
    if car.checkpoint_index >= len(track.checkpoints):
        return False

    current_checkpoint = track.checkpoints[car.checkpoint_index]

    x1, y1 = car.x, car.y
    x2, y2 = nx, ny

    for cx, cy in current_checkpoint:
        if segment_intersects_rect(x1, y1, x2, y2, cx, cy, 1.0, 1.0):
            return True

    return False


def check_finish(track, car, nx, ny, checkpoint_now=False):
    if not car.started:
        return False

    next_checkpoint_index = car.checkpoint_index + (1 if checkpoint_now else 0)
    if next_checkpoint_index < len(track.checkpoints):
        return False

    x1, y1 = car.x, car.y
    x2, y2 = nx, ny

    for fx, fy in track.finish:
        if segment_intersects_rect(x1, y1, x2, y2, fx, fy, 1.0, 1.0):
            return True

    return False

def get_first_finish_t(
    track,
    car,
    x1,
    y1,
    x2,
    y2,
    checkpoint_now=False
):
    """
    Возвращает минимальный t пересечения с финишем.
    Если финиш не пересечён — None.
    """

    if not car.started:
        return None

    next_checkpoint_index = (
        car.checkpoint_index +
        (1 if checkpoint_now else 0)
    )

    if next_checkpoint_index < len(track.checkpoints):
        return None

    first_t = None

    for fx, fy in track.finish:
        interval = segment_rect_contact_interval(
            x1, y1,
            x2, y2,
            fx, fy,
            1.0, 1.0
        )

        if interval is None:
            continue

        u1, u2 = interval

        if u2 <= EPS:
            continue

        hit_t = max(u1, 0.0)

        if first_t is None or hit_t < first_t:
            first_t = hit_t

    return first_t

def move_runs_along_crash_wall(track, car, nx, ny):
    """
    Режем только следующий безопасный ход после столкновения.
    Нельзя идти строго вдоль стены, о которую только что ударились:
    - vertical   -> запрещён чисто вертикальный безопасный ход
    - horizontal -> запрещён чисто горизонтальный безопасный ход
    """
    if not getattr(car, "just_crashed", False):
        return False

    crash_axis = getattr(car, "crash_axis", None)
    if crash_axis is None:
        return False

    dx = nx - car.x
    dy = ny - car.y

    if dx == 0 and dy == 0:
        return False

    collision, _, _, _ = check_collision_path_info(track.walls, car.x, car.y, nx, ny)
    if collision:
        return False

    if crash_axis == "vertical" and dx == 0 and dy != 0:
        return True

    if crash_axis == "horizontal" and dy == 0 and dx != 0:
        return True

    return False


def get_possible_moves(track, car, max_speed):
    """
    Возвращает все допустимые целевые точки:
    - ускорение по каждой оси в диапазоне -1..1
    - ограничение по max_speed
    - границы поля
    - правило первого безопасного хода после столкновения

    Столкновения здесь не отсекаются: игрок/бот может выбрать такой ход,
    а уже apply_move() обработает аварию.
    """
    moves = []

    for ax in (-1, 0, 1):
        for ay in (-1, 0, 1):
            vx = car.vx + ax
            vy = car.vy + ay

            if abs(vx) > max_speed or abs(vy) > max_speed:
                continue

            target_x = car.x + vx
            target_y = car.y + vy

            nx = max(1, min(target_x, track.width - 2))
            ny = max(1, min(target_y, track.height - 2))

            vx = nx - car.x
            vy = ny - car.y

            if move_runs_along_crash_wall(track, car, nx, ny):
                continue

            moves.append((nx, ny))

    return moves


def apply_collision(car, last_x, last_y, hit_axis):
    car.x = last_x
    car.y = last_y
    car.vx = 0
    car.vy = 0
    car.path.append((last_x, last_y))
    car.started = True
    car.just_crashed = True
    car.crash_axis = hit_axis


def apply_normal_move(car, gx, gy):
    car.vx = gx - car.x
    car.vy = gy - car.y
    car.x = gx
    car.y = gy
    car.path.append((gx, gy))
    car.started = True
    car.just_crashed = False
    car.crash_axis = None


def apply_move(track, car, gx, gy):
    """
    Применяет ход к машине, изменяя её состояние.
    Возвращает TurnResult.
    """

    collision, stop_x, stop_y, hit_axis = check_collision_path_info(
        track.walls,
        car.x,
        car.y,
        gx,
        gy
    )

    checkpoint_now = check_checkpoint(track, car, gx, gy)

    finish_t = get_first_finish_t(
        track,
        car,
        car.x,
        car.y,
        gx,
        gy,
        checkpoint_now
    )

    wall_t = None

    if collision:
        dx = gx - car.x
        dy = gy - car.y

        total_len_sq = dx * dx + dy * dy

        if total_len_sq > 0:
            stop_dx = stop_x - car.x
            stop_dy = stop_y - car.y

            wall_t = (
                (stop_dx * dx + stop_dy * dy)
                / total_len_sq
            )

    # =====================================================
    # Финиш раньше столкновения -> победа
    # =====================================================

    if finish_t is not None:
        if wall_t is None or finish_t <= wall_t + EPS:

            apply_normal_move(car, gx, gy)

            if checkpoint_now:
                car.checkpoint_index += 1

            return TurnResult(
                collision=False,
                checkpoint_now=checkpoint_now,
                finish_now=True,
                final_x=gx,
                final_y=gy,
                new_vx=car.vx,
                new_vy=car.vy,
                hit_axis=None
            )

    # =====================================================
    # Иначе обычная логика столкновения
    # =====================================================

    if collision:
        apply_collision(car, stop_x, stop_y, hit_axis)

        return TurnResult(
            collision=True,
            checkpoint_now=False,
            finish_now=False,
            final_x=stop_x,
            final_y=stop_y,
            new_vx=0,
            new_vy=0,
            hit_axis=hit_axis
        )

    apply_normal_move(car, gx, gy)

    if checkpoint_now:
        car.checkpoint_index += 1

    finish_now = check_finish(track, car, gx, gy, checkpoint_now)

    return TurnResult(
        collision=False,
        checkpoint_now=checkpoint_now,
        finish_now=finish_now,
        final_x=gx,
        final_y=gy,
        new_vx=car.vx,
        new_vy=car.vy,
        hit_axis=None
    )