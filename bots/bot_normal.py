import random

from .bot import (
    distance_to_target,
    distance_to_previous_target,
    progress_to_target,
    wall_danger,
    direction_bonus,
)


def choose_normal_move(game, car):
    moves = game.get_possible_moves(car)

    if not moves:
        return None

    safe_moves = []
    risky_moves = []

    for gx, gy in moves:
        collision, last_x, last_y = game.check_collision_path(car.x, car.y, gx, gy)

        if collision:
            landing_x, landing_y = last_x, last_y
            checkpoint_now = False
            finish_now = False
            new_vx, new_vy = 0, 0
        else:
            landing_x, landing_y = gx, gy
            checkpoint_now = game.check_checkpoint(car, gx, gy)
            finish_now = game.check_finish(car, gx, gy, checkpoint_now)
            new_vx = gx - car.x
            new_vy = gy - car.y

        score = evaluate_normal_move(
            game=game,
            car=car,
            landing_x=landing_x,
            landing_y=landing_y,
            new_vx=new_vx,
            new_vy=new_vy,
            collision=collision,
            checkpoint_now=checkpoint_now,
            finish_now=finish_now
        )

        item = {
            "move": (gx, gy),
            "score": score,
            "collision": collision,
            "checkpoint_now": checkpoint_now,
            "finish_now": finish_now,
            "progress": progress_to_target(game, car, landing_x, landing_y, checkpoint_now)
        }

        if collision:
            risky_moves.append(item)
        else:
            safe_moves.append(item)

    pool = safe_moves if safe_moves else risky_moves

    winning = [m for m in pool if m["finish_now"]]
    if winning:
        winning.sort(key=lambda m: m["score"], reverse=True)
        return winning[0]["move"]

    checkpoint_moves = [m for m in pool if m["checkpoint_now"]]
    if checkpoint_moves:
        checkpoint_moves.sort(key=lambda m: m["score"], reverse=True)
        best_score = checkpoint_moves[0]["score"]
        top = [m for m in checkpoint_moves if m["score"] >= best_score - 40]
        return random.choice(top)["move"]

    forward = [m for m in pool if m["progress"] > 0]
    if forward:
        forward.sort(key=lambda m: (m["progress"], m["score"]), reverse=True)
        best_progress = forward[0]["progress"]
        top = [m for m in forward if m["progress"] >= best_progress - 1]
        top.sort(key=lambda m: m["score"], reverse=True)
        best_score = top[0]["score"]
        best = [m for m in top if m["score"] >= best_score - 40]
        return random.choice(best[:3] if len(best) >= 3 else best)["move"]

    pool.sort(key=lambda m: m["score"], reverse=True)
    best_score = pool[0]["score"]
    top = [m for m in pool if m["score"] >= best_score - 40]
    return random.choice(top[:3] if len(top) >= 3 else top)["move"]


def evaluate_normal_move(
    game,
    car,
    landing_x,
    landing_y,
    new_vx,
    new_vy,
    collision,
    checkpoint_now,
    finish_now
):
    if finish_now:
        return 1_000_000

    score = 0

    current_dist = distance_to_target(game, car, landing_x, landing_y, checkpoint_now)
    current_dist_now = distance_to_target(game, car, car.x, car.y, False)
    progress = current_dist_now - current_dist

    prev_dist = distance_to_previous_target(game, car, landing_x, landing_y)
    danger = wall_danger(game, landing_x, landing_y)
    speed = abs(new_vx) + abs(new_vy)
    old_speed = abs(car.vx) + abs(car.vy)

    score -= current_dist * 140
    score += progress * 170
    score -= danger * 25
    score += speed * 1

    if progress < 0:
        score += progress * 220

    if collision:
        score -= 10_000

    if (landing_x, landing_y) in car.path:
        score -= 700

    if len(car.path) >= 2 and (landing_x, landing_y) == car.path[-2]:
        score -= 1800

    if checkpoint_now:
        score += 7000

    if car.checkpoint_index > 0 and prev_dist < current_dist:
        score -= 1600

    if current_dist <= 2:
        score -= speed * 180
    elif current_dist <= 5:
        score -= speed * 80

    if current_dist <= 6 and speed < old_speed:
        score += (old_speed - speed) * 60

    score += direction_bonus(game, car, landing_x, landing_y, checkpoint_now) * 3

    score += random.uniform(-6, 6)

    return score