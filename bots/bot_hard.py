import random
from dataclasses import dataclass

from .bot import (
    distance_to_target,
    distance_to_previous_target,
    direction_bonus,
)
from .bot_normal import evaluate_normal_move


@dataclass
class SimCar:
    x: int
    y: int
    vx: int
    vy: int
    checkpoint_index: int
    started: bool
    path: list
    just_crashed: bool = False
    crash_axis: str = None


def choose_hard_move(game, car):
    root_car = SimCar(
        x=car.x,
        y=car.y,
        vx=car.vx,
        vy=car.vy,
        checkpoint_index=car.checkpoint_index,
        started=car.started,
        path=list(car.path),
        just_crashed=getattr(car, "just_crashed", False),
        crash_axis=getattr(car, "crash_axis", None),
    )

    first_moves = game.get_possible_moves(root_car)
    if not first_moves:
        return None

    initial_nodes = []

    for gx, gy in first_moves:
        result = simulate_move(game, root_car, gx, gy)

        if result["finish_now"] and not result["collision"]:
            return (gx, gy)

        step_score = evaluate_hard_step(game, root_car, result, depth=1)

        initial_nodes.append({
            "first_move": (gx, gy),
            "car": result["car"],
            "score": step_score,
            "recent_positions": [
                (root_car.x, root_car.y),
                (result["car"].x, result["car"].y)
            ],
            "checkpoint_now": result["checkpoint_now"],
            "finish_now": result["finish_now"],
        })

    checkpoint_nodes = [
        node for node in initial_nodes
        if node["checkpoint_now"] and not node["finish_now"]
    ]
    if checkpoint_nodes:
        checkpoint_nodes.sort(key=lambda n: n["score"], reverse=True)
        best_score = checkpoint_nodes[0]["score"]
        top = [n for n in checkpoint_nodes if n["score"] >= best_score - 25]
        return random.choice(top)["first_move"]

    beam = sorted(initial_nodes, key=lambda n: n["score"], reverse=True)[:6]

    max_depth = 2
    for depth in range(2, max_depth + 1):
        expanded = []

        for node in beam:
            sim_car = node["car"]
            moves = game.get_possible_moves(sim_car)

            if not moves:
                expanded.append(node)
                continue

            for gx, gy in moves:
                result = simulate_move(game, sim_car, gx, gy)

                if result["finish_now"] and not result["collision"]:
                    return node["first_move"]

                step_score = evaluate_hard_step(game, sim_car, result, depth=depth)
                new_score = node["score"] + step_score * depth_weight(depth)

                new_pos = (result["car"].x, result["car"].y)
                recent_positions = node["recent_positions"][-4:] + [new_pos]

                if new_pos in node["recent_positions"][-2:]:
                    new_score -= 250

                if len(node["recent_positions"]) >= 2 and new_pos == node["recent_positions"][-2]:
                    new_score -= 450

                expanded.append({
                    "first_move": node["first_move"],
                    "car": result["car"],
                    "score": new_score,
                    "recent_positions": recent_positions,
                    "checkpoint_now": result["checkpoint_now"],
                    "finish_now": result["finish_now"],
                })

        if not expanded:
            break

        expanded.sort(key=lambda n: n["score"], reverse=True)
        beam = expanded[:6]

    if not beam:
        initial_nodes.sort(key=lambda n: n["score"], reverse=True)
        return initial_nodes[0]["first_move"]

    best_score = beam[0]["score"]
    top = [n for n in beam if n["score"] >= best_score - 25]
    return random.choice(top[:3] if len(top) >= 3 else top)["first_move"]


def depth_weight(depth):
    if depth == 1:
        return 1.0
    return 0.6


def simulate_move(game, base_car, gx, gy):
    collision, last_x, last_y, hit_axis = game.check_collision_info(
        base_car.x,
        base_car.y,
        gx,
        gy
    )

    if collision:
        sim_car = SimCar(
            x=last_x,
            y=last_y,
            vx=0,
            vy=0,
            checkpoint_index=base_car.checkpoint_index,
            started=True,
            path=base_car.path + [(last_x, last_y)],
            just_crashed=True,
            crash_axis=hit_axis
        )

        return {
            "car": sim_car,
            "collision": True,
            "checkpoint_now": False,
            "finish_now": False
        }

    checkpoint_now = check_checkpoint_sim(game, base_car, gx, gy)
    finish_now = check_finish_sim(game, base_car, gx, gy, checkpoint_now)

    new_checkpoint_index = base_car.checkpoint_index + (1 if checkpoint_now else 0)

    sim_car = SimCar(
        x=gx,
        y=gy,
        vx=gx - base_car.x,
        vy=gy - base_car.y,
        checkpoint_index=new_checkpoint_index,
        started=True,
        path=base_car.path + [(gx, gy)],
        just_crashed=False,
        crash_axis=None
    )

    return {
        "car": sim_car,
        "collision": False,
        "checkpoint_now": checkpoint_now,
        "finish_now": finish_now
    }


def check_checkpoint_sim(game, car, nx, ny):
    if car.checkpoint_index >= len(game.track.checkpoints):
        return False
    return game.check_checkpoint(car, nx, ny)


def check_finish_sim(game, car, nx, ny, checkpoint_now=False):
    if not car.started:
        return False

    next_checkpoint_index = car.checkpoint_index + (1 if checkpoint_now else 0)
    if next_checkpoint_index < len(game.track.checkpoints):
        return False

    return game.check_finish(car, nx, ny, checkpoint_now)


def evaluate_hard_step(game, base_car, move_result, depth):
    sim_car = move_result["car"]

    score = evaluate_normal_move(
        game=game,
        car=base_car,
        landing_x=sim_car.x,
        landing_y=sim_car.y,
        new_vx=sim_car.vx,
        new_vy=sim_car.vy,
        collision=move_result["collision"],
        checkpoint_now=move_result["checkpoint_now"],
        finish_now=move_result["finish_now"]
    )

    if move_result["finish_now"]:
        return score

    current_dist_now = distance_to_target(game, base_car, base_car.x, base_car.y, False)
    current_dist_after = distance_to_target(
        game,
        base_car,
        sim_car.x,
        sim_car.y,
        move_result["checkpoint_now"]
    )
    progress = current_dist_now - current_dist_after
    speed = abs(sim_car.vx) + abs(sim_car.vy)

    score += progress * 35

    score += direction_bonus(
        game,
        base_car,
        sim_car.x,
        sim_car.y,
        move_result["checkpoint_now"]
    ) * 1.2

    if current_dist_after <= 2:
        score -= speed * 30
    elif current_dist_after <= 5:
        score -= speed * 12

    previous_dist = distance_to_previous_target(game, base_car, sim_car.x, sim_car.y)
    if base_car.checkpoint_index > 0 and previous_dist < current_dist_after:
        score -= 500

    if move_result["checkpoint_now"]:
        score += 1200

    score += random.uniform(-1.5, 1.5)

    return score