def choose_bot_move(game, car, difficulty="normal"):
    if difficulty == "hard":
        from .bot_hard import choose_hard_move
        return choose_hard_move(game, car)

    from .bot_normal import choose_normal_move
    return choose_normal_move(game, car)


def get_current_targets(game, car, checkpoint_now=False):
    next_index = car.checkpoint_index + (1 if checkpoint_now else 0)

    if next_index < len(game.track.checkpoints):
        return list(game.track.checkpoints[next_index])

    return list(game.track.finish)


def get_previous_targets(game, car):
    if car.checkpoint_index <= 0:
        return []

    return list(game.track.checkpoints[car.checkpoint_index - 1])


def distance_to_target(game, car, x, y, checkpoint_now=False):
    targets = get_current_targets(game, car, checkpoint_now)

    if not targets:
        return 0

    return min(abs(x - tx) + abs(y - ty) for tx, ty in targets)


def distance_to_previous_target(game, car, x, y):
    targets = get_previous_targets(game, car)

    if not targets:
        return 10_000

    return min(abs(x - tx) + abs(y - ty) for tx, ty in targets)


def progress_to_target(game, car, x, y, checkpoint_now=False):
    now_dist = distance_to_target(game, car, car.x, car.y, False)
    new_dist = distance_to_target(game, car, x, y, checkpoint_now)
    return now_dist - new_dist


def wall_danger(game, x, y):
    danger = 0

    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue

            nx = x + dx
            ny = y + dy

            if not game.track.is_inside_bounds(nx, ny):
                danger += 2
                continue

            if game.track.is_wall(nx, ny):
                danger += 1

    return danger


def direction_bonus(game, car, x2, y2, checkpoint_now=False):
    targets = get_current_targets(game, car, checkpoint_now)

    if not targets:
        return 0

    tx, ty = min(
        targets,
        key=lambda p: abs(x2 - p[0]) + abs(y2 - p[1])
    )

    x1, y1 = car.x, car.y
    move_dx = x2 - x1
    move_dy = y2 - y1

    to_target_dx = tx - x1
    to_target_dy = ty - y1

    return move_dx * to_target_dx + move_dy * to_target_dy