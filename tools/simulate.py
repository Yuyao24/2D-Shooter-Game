"""
Headless game simulator for finding bugs and balancing.

A simple bot plays full games: it walks to the flag (A* pathfinding), plants it,
defends it, shoots the nearest visible enemy, backs away from melee enemies and
buys upgrades between rounds. Game time is simulated, so a game runs much faster
than real time. Statistics are printed as JSON.

Usage (from the project root):
    python tools/simulate.py --games 4 --max-rounds 10 --seed 1
"""
import argparse
import json
import math
import os
import random
import sys
import time
from collections import defaultdict

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, os.getcwd())

import pygame

pygame.display.init()


class _FakeInfo:
    current_w, current_h = 1920, 1080


pygame.display.Info = lambda: _FakeInfo()
pygame.font.init()
SCREEN = pygame.display.set_mode((1920, 1080))

# ------------------------------------------------------------------ fake time and input
SIM = {"ms": 0.0}
pygame.time.get_ticks = lambda: int(SIM["ms"])
KEYS: dict[int, int] = {}
MOUSE = [960, 540]


class _Keys:
    def __getitem__(self, key):
        return KEYS.get(key, 0)


pygame.key.get_pressed = lambda: _Keys()
pygame.mouse.get_pos = lambda: (int(MOUSE[0]), int(MOUSE[1]))
pygame.mouse.set_visible = lambda *a: None
pygame.mouse.set_cursor = lambda *a, **k: None

import gameplay  # noqa: E402  (must be imported after the patches above)
import enemy as enemy_module  # noqa: E402
import upgrades  # noqa: E402
from player import Player  # noqa: E402

DT = 1 / 30  # Simulation step (movement is frame-rate independent)
ROUND_TIME_LIMIT = 300  # Seconds; a round taking longer is reported as a stalemate


class Stats:
    """Collects everything we want to know about a simulated game."""

    def __init__(self):
        self.rounds = []
        self.current = None
        self.damage_source = None
        self.errors = []
        self.speed_samples = []  # actual / intended speed of moving enemies
        self.stuck_events = 0
        self.inside_wall_events = 0
        self.purchases = defaultdict(int)

    def new_round(self, number, rm):
        self.current = {
            "round": number, "start": SIM["ms"], "plant_time": None, "kills": 0,
            "damage": defaultdict(float), "flag_hits": 0, "deaths": 0,
            "enemies": len(rm.enemy_sprites),
            "brutes": sum(isinstance(e, enemy_module.BruteEnemy) for e in rm.enemy_sprites),
            "money_start": rm.player.money,
        }

    def end_round(self, reason, rm):
        r = self.current
        r["reason"] = reason
        r["duration"] = round((SIM["ms"] - r["start"]) / 1000, 1)
        r["plant_time"] = None if r["plant_time"] is None else round((r["plant_time"] - r["start"]) / 1000, 1)
        r["damage"] = {k: round(v) for k, v in r["damage"].items()}
        r["enemies_left"] = len(rm.enemy_sprites)
        r["money_end"] = rm.player.money
        r["hp_left"] = round(max(0, rm.player.health))
        r["flag_timer"] = round(rm.flag.timer, 1)
        del r["start"]
        self.rounds.append(r)


STATS = Stats()


# ------------------------------------------------------------------ instrumentation
def _wrap_damage_source(cls, method_name, label):
    original = getattr(cls, method_name)

    def wrapper(self, *args, **kwargs):
        STATS.damage_source = label(self) if callable(label) else label
        try:
            return original(self, *args, **kwargs)
        finally:
            STATS.damage_source = None

    setattr(cls, method_name, wrapper)


_wrap_damage_source(enemy_module.MeleeEnemy, "attack", lambda e: type(e).__name__)
_wrap_damage_source(enemy_module.EnemyBullet, "check_hit_target", "RangedEnemy")

_original_take_damage = Player.take_damage


def _player_take_damage(self, amount):
    if STATS.current is not None:
        STATS.current["damage"][STATS.damage_source or "unknown"] += amount * self.damage_mult
    _original_take_damage(self, amount)


Player.take_damage = _player_take_damage

_original_flag_take_damage = gameplay.Flag.take_damage


def _flag_take_damage(self, amount):
    if STATS.current is not None:
        STATS.current["flag_hits"] += 1
    _original_flag_take_damage(self, amount)


gameplay.Flag.take_damage = _flag_take_damage


def bot_shop(screen, clock, round_number, player, stats_manager, forced_upgrades=None):
    """Bot upgrade policy: buy the offered upgrades it can afford, most useful first."""
    offered = upgrades.select_random_upgrades(upgrades.create_upgrade_list(), player)
    avoid = {"Berserker", "Holy Trinity"}  # Risky upgrades the bot does not use well
    for upgrade in sorted(offered, key=lambda u: -u.cost):
        if upgrade.name in avoid or upgrade.cost > player.money:
            continue
        player.update_money(-upgrade.cost)
        stats_manager.update_money(upgrade.cost)
        upgrade.apply(player)
        stats_manager.update_upgrades()
        STATS.purchases[upgrade.name] += 1
    return "CONTINUE"


gameplay.upgrade_menu = bot_shop


class Bot:
    """Controls the player through the fake keyboard and mouse."""

    def __init__(self, rm, dodge: bool = True):
        self.rm = rm
        self.dodge = dodge
        self.path = []
        self.path_timer = 0.0
        self.last_goal = None
        self.stuck_timer = 0.0
        self.unstick_time = 0.0
        self.unstick_dir = pygame.Vector2()
        self.last_pos = None

    def has_line_of_sight(self, start, end) -> bool:
        area = pygame.Rect(min(start[0], end[0]), min(start[1], end[1]),
                           abs(start[0] - end[0]) + 1, abs(start[1] - end[1]) + 1)
        return not any(o.hitbox.clipline(start, end) for o in self.rm.collision_sprites.near(area))

    def step(self, dt):
        rm, player = self.rm, self.rm.player
        pos = pygame.Vector2(player.hitbox.center)

        # Camera offset (normally set while drawing) so aiming works
        rm.all_sprites.offset.x = int(player.rect.centerx - 960)
        rm.all_sprites.offset.y = int(player.rect.centery - 540)

        # ---- target selection: nearest visible enemy within range
        target, best = None, player.gun.range * 0.9
        for e in rm.enemy_sprites:
            d = pos.distance_to(e.rect.center)
            if d < best and self.has_line_of_sight(player.rect.center, e.rect.center):
                target, best = e, d

        if target is not None:
            MOUSE[0] = target.rect.centerx - rm.all_sprites.offset.x
            MOUSE[1] = target.rect.centery - rm.all_sprites.offset.y
            player.update_aim()
            player.shoot(rm.all_sprites, rm.bullet_sprites)
        elif player.gun.ammo < player.gun.max_ammo * 0.5:
            player.gun.reload()

        # ---- movement goal
        flag = rm.flag
        goal = pygame.Vector2(flag.position.x, flag.position.y - 20)
        planting = not flag.is_planted and pos.distance_to(flag.position) < flag.radius - 40

        direction = pygame.Vector2()
        close_melee = [e for e in rm.enemy_sprites
                       if not isinstance(e, enemy_module.RangedEnemy) and pos.distance_to(e.hitbox.center) < 150
                       and self.has_line_of_sight(pos, e.hitbox.center)]

        # Projectiles flying at us (a human would sidestep these)
        incoming = None
        for sprite in rm.all_sprites:
            if isinstance(sprite, enemy_module.EnemyBullet):
                to_player = pos - pygame.Vector2(sprite.rect.center)
                if 0 < to_player.length() < 260 and sprite.direction.dot(to_player.normalize()) > 0.9:
                    incoming = sprite
                    break

        if self.unstick_time > 0:
            # Recovering from being stuck: walk in a random direction for a moment
            self.unstick_time -= dt
            direction = pygame.Vector2(self.unstick_dir)
        elif incoming is not None and self.dodge and not planting:
            # Sidestep perpendicular to the projectile
            side = pygame.Vector2(-incoming.direction.y, incoming.direction.x)
            if side.dot(goal - pos) < 0:
                side = -side
            direction = side
        elif close_melee and not planting:
            # Back away from melee enemies (kiting)
            for e in close_melee:
                away = pos - pygame.Vector2(e.hitbox.center)
                if away.length() > 0:
                    direction += away.normalize()
        elif pos.distance_to(goal) > 60 and not planting:
            self.path_timer -= dt
            if self.path_timer <= 0 or not self.path:
                self.path = rm.pathfinder.get_path(pos, goal)[1:]  # First node is our own tile
                self.path_timer = 0.5
            grid = rm.pathfinder.grid
            while self.path and (pos.distance_to(self.path[0]) < 24 or not grid.node(
                    int(self.path[0].x // 64), int(self.path[0].y // 64)).walkable):
                self.path.pop(0)
            if self.path:
                direction = self.path[0] - pos
            else:
                direction = goal - pos

        # Stuck detection: trying to move but not moving for 1.5 s
        if direction.length() > 0 and self.last_pos is not None and pos.distance_to(self.last_pos) < 1:
            self.stuck_timer += dt
            if self.stuck_timer > 1.5:
                self.unstick_time, self.stuck_timer, self.path = 0.6, 0.0, []
                self.unstick_dir = pygame.Vector2(1, 0).rotate(random.uniform(0, 360))
        else:
            self.stuck_timer = 0.0
        self.last_pos = pos

        KEYS.clear()
        if direction.length() > 0:
            direction = direction.normalize()
            KEYS[pygame.K_d] = int(direction.x > 0.2)
            KEYS[pygame.K_a] = int(direction.x < -0.2)
            KEYS[pygame.K_s] = int(direction.y > 0.2)
            KEYS[pygame.K_w] = int(direction.y < -0.2)


def run_game(seed: int, max_rounds: int) -> dict:
    random.seed(seed)
    SIM["ms"] = 1000.0
    global STATS
    STATS = Stats()

    rm = gameplay.RoundManager(SCREEN, pygame.time.Clock())
    rm.show_message = lambda *a, **k: None
    rm.start_game(message=False)
    bot = Bot(rm)
    STATS.new_round(1, rm)

    # Record why each round ended (start_new_round is called right after)
    original_start_new_round = rm.start_new_round

    def start_new_round():
        if rm.flag.outcome:
            reason = rm.flag.outcome
        elif rm.player.health <= 0:
            reason = "PLAYER_DIED"
        elif len(rm.enemy_sprites) == 0:
            reason = "ALL_KILLED"
        else:
            reason = "OTHER"
        if reason == "PLAYER_DIED":
            STATS.current["deaths"] += 1
        STATS.end_round(reason, rm)
        result = original_start_new_round()
        bot.path = []
        STATS.new_round(rm.round_number, rm)
        return result

    rm.start_new_round = start_new_round

    last_positions = {}
    sample_timer = 0.0
    state = "CONTINUE"
    wall_clock = time.time()

    while state == "CONTINUE":
        if rm.round_number > max_rounds:
            break
        if SIM["ms"] - STATS.current["start"] > ROUND_TIME_LIMIT * 1000:
            STATS.current["stalemate_info"] = {
                "player": [round(v) for v in rm.player.hitbox.center],
                "flag": [round(v) for v in rm.flag.position],
                "next_waypoint": [round(v) for v in bot.path[0]] if bot.path else None,
                "keys": [k for k, v in KEYS.items() if v],
                "nearest_enemy_px": round(min((pygame.Vector2(rm.player.hitbox.center).distance_to(e.hitbox.center)
                                               for e in rm.enemy_sprites), default=-1)),
                "nearby_enemies": [
                    {"type": type(e).__name__, "dist": round(pygame.Vector2(rm.player.rect.center).distance_to(e.rect.center)),
                     "bot_los": bot.has_line_of_sight(rm.player.rect.center, e.rect.center), "active": e.active,
                     "hp": round(e.health), "path": len(e.path), "pos": [round(v) for v in e.hitbox.center]}
                    for e in rm.enemy_sprites
                    if pygame.Vector2(rm.player.rect.center).distance_to(e.rect.center) < 400],
                "player_bullets_alive": len(rm.bullet_sprites),
            }
            STATS.end_round("STALEMATE", rm)
            break

        SIM["ms"] += DT * 1000
        try:
            bot.step(DT)
            kills_before = rm.stats_manager.enemies_killed
            was_planted = rm.flag.is_planted
            state = rm.update(DT) or "CONTINUE"  # start_new_round() returns None, like in the real loop
            if STATS.current is not None:
                STATS.current["kills"] += max(0, rm.stats_manager.enemies_killed - kills_before)
                if not was_planted and rm.flag.is_planted and STATS.current["plant_time"] is None:
                    STATS.current["plant_time"] = SIM["ms"]
        except Exception as error:  # Record crashes instead of stopping the whole run
            import traceback
            STATS.errors.append(traceback.format_exc())
            break

        # ---- every 2 s: stuck enemies, enemies inside walls, real speed
        sample_timer += DT
        if sample_timer >= 2.0:
            for e in rm.enemy_sprites:
                pos = pygame.Vector2(e.hitbox.center)
                prev = last_positions.get(id(e))
                chasing = e.active and e.path and e.distance_to_target() > e.attack_range
                if prev is not None and chasing:
                    moved = pos.distance_to(prev)
                    STATS.speed_samples.append(moved / (e.speed * sample_timer))
                    if moved < 10:
                        STATS.stuck_events += 1
                if any(o.hitbox.colliderect(e.hitbox) for o in rm.collision_sprites.near(e.hitbox)):
                    STATS.inside_wall_events += 1
                last_positions[id(e)] = pos
            sample_timer = 0.0

    if state == "GAME_OVER":
        STATS.end_round("PLAYER_DIED", rm)
        STATS.rounds[-1]["deaths"] += 1

    speeds = sorted(STATS.speed_samples)
    return {
        "seed": seed,
        "final_state": state,
        "rounds_reached": rm.round_number,
        "lives_left": rm.player.lives,
        "score": rm.stats_manager.score,
        "sim_minutes": round(SIM["ms"] / 60000, 1),
        "real_seconds": round(time.time() - wall_clock, 1),
        "rounds": STATS.rounds,
        "enemy_speed_ratio_median": round(speeds[len(speeds) // 2], 2) if speeds else None,
        "stuck_events": STATS.stuck_events,
        "inside_wall_events": STATS.inside_wall_events,
        "purchases": dict(STATS.purchases),
        "errors": STATS.errors,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--games", type=int, default=1)
    parser.add_argument("--max-rounds", type=int, default=10)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()
    results = [run_game(args.seed + i, args.max_rounds) for i in range(args.games)]
    print(json.dumps(results, indent=1))
