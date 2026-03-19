import pygame
import os
import json

UI_SCALE = 1.5

WINDOW_WIDTH = 1280 * UI_SCALE
WINDOW_HEIGHT = 720 * UI_SCALE
WINDOW_CENTER = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)

TILE_SIZE = 64


# Colors
COLOR_BLACK = "#000000"
COLOR_WHITE = "#FFFFFF"
COLOR_GREY = "#808080"
COLOR_BLUE = "#00A2E8"
COLOR_DARK_BLUE = "#3F48CC"
COLOR_GREEN = "#19DE21"
COLOR_DARK_GREEN = "#22B14C"
COLOR_RED = "#ED1C24"
COLOR_YELLOW = "#FFC200"
COLOR_GOLD = "#FFD700"

class AssetManager:
    """Manages game assets like images to ensure they are loaded only once."""
    _images: dict[str, pygame.Surface] = {}

    @classmethod
    def get_image(cls, path: str) -> pygame.Surface:
        """
        Loads and returns an image surface. Caches the result to avoid repeated disk I/O.
        
        :param path: The file path to the image.
        :return: A pygame.Surface containing the image.
        """
        if path not in cls._images:
            cls._images[path] = pygame.image.load(path).convert_alpha()
        return cls._images[path]

class AllSprites(pygame.sprite.Group):
    """
    A custom sprite group that handles camera offset and Y-sorting (plus Z-layering).
    """
    def __init__(self) -> None:
        super().__init__()
        self.display_surface: pygame.Surface = pygame.display.get_surface()
        self.offset: pygame.Vector2 = pygame.Vector2(0, 0)

    def draw_with_offset(self, target_pos: pygame.Vector2 | tuple[float, float]) -> None:
        """
        Calculates camera offset based on a target position and draws all sprites.
        
        :param target_pos: The position the camera should center on (usually the player).
        """
        self.offset.x = int(target_pos[0] - WINDOW_WIDTH / 2)
        self.offset.y = int(target_pos[1] - WINDOW_HEIGHT / 2)
        
        # Sort by z_layer then by bottom Y for Y-sorting
        for sprite in sorted(self.sprites(), key=lambda s: (getattr(s, 'z_layer', 0), s.rect.bottom)):
            self.display_surface.blit(sprite.image, (int(sprite.rect.left - self.offset.x), int(sprite.rect.top - self.offset.y)))

def save_data_exists() -> bool:
    """
    Checks whether there is an existing game save.

    :return: True if there is a game save, False otherwise.
    """
    with open ("game_save/save_data.txt") as f:
        return f.read() != ""  # If the file is empty -> return False
    
def clear_save_data() -> None:
    """Clears the game save data file. """
    with open ("game_save/save_data.txt", "w") as f:
        f.write("")

def save_game_data(round_number: int, player, stats_manager,
              in_upgrade_menu: bool = False,
              offered_upgrades: list = None) -> None:
    """
    Saves the current game state to a file.
    :param round_number: The current round number.
    :param player: The player object containing stats.
    :param stats_manager: The stats manager object containing score and other stats.
    :param in_upgrade_menu: Whether the player is currently in the upgrade menu.
    :param offered_upgrades: The list of currently offered upgrades (if in upgrade menu).
    """

    data = {
        # Round data and state
        "round_number": round_number,
        "in_upgrade_menu": in_upgrade_menu,
        "offered_upgrades": [u.name for u in offered_upgrades] if offered_upgrades else [],

        # Player stats
        "player": {
            "max_health" : player.max_health,
            "lives" : player.lives,
            "money" : player.money,
            "money_mult" : player.money_mult,
            "speed" : player.speed,
            "damage_mult" : player.damage_mult,
            "life_steal" : player.life_steal,
            "has_trinity": player.has_trinity,
            "has_adrenaline": player.has_adrenaline,
            "has_auto_shoot": player.has_auto_shoot,
            "adrenaline": player.adrenaline,
        },

        # Gun stats
        "gun": {
            "damage": player.gun.damage,
            "fire_rate": player.gun.fire_rate,
            "range": player.gun.range,
            "bullet_speed": player.gun.bullet_speed,
            "max_ammo": player.gun.max_ammo,
            "reload_time": player.gun.reload_time,
            "insta_reload_chance": player.gun.insta_reload_chance,
            "ammo_saver_chance": player.gun.ammo_saver_chance,
            "piercing": player.gun.piercing,
            "insta_kill_chance": player.gun.insta_kill_chance,
            "area_damage": player.gun.area_damage,
            "trinity": player.gun.trinity,
            "auto_shoot": player.gun.auto_shoot,
        },

        # Stats manager data
        "stats_manager": {
            "score": stats_manager.score,
            "enemies_killed": stats_manager.enemies_killed,
            "rounds_completed": stats_manager.rounds_completed,
            "flags_planted": stats_manager.flags_planted,
            "upgrades_purchased": stats_manager.upgrades_purchased,
            "money_spent": stats_manager.money_spent,
        }
    }

    with open("game_save/save_data.txt", "w") as f:
        json.dump(data, f, indent=4)

def load_game_data() -> dict:
    """
    Loads the game state from a file.

    :return: A dictionary containing the loaded game data.
    """
    with open("game_save/save_data.txt", "r") as f:
        data = json.load(f)
    return data

def apply_save_data(data: dict, player, stats_manager) -> None:
    """
    Applies loaded game data to the player and stats manager objects.

    :param data: The dictionary containing the loaded game data.
    :param player: The player object to apply the data to.
    :param stats_manager: The stats manager object to apply the data to.
    """
    # Apply round and upgrade menu state
    p = data["player"]
    g = data["gun"]
    s = data["stats_manager"]

    # Player stats
    player.health = p["max_health"]  # Set current health to max health
    player.max_health = p["max_health"]
    player.lives = p["lives"]
    player.money = p["money"]
    player.money_mult = p["money_mult"]
    player.speed = p["speed"]
    player.damage_mult = p["damage_mult"]
    player.life_steal = p["life_steal"]
    player.has_trinity = p["has_trinity"]
    player.has_adrenaline = p["has_adrenaline"]
    player.has_auto_shoot = p["has_auto_shoot"]
    player.adrenaline = p["adrenaline"]

    # Gun stats
    player.gun.damage = g["damage"]
    player.gun.fire_rate = g["fire_rate"]
    player.gun.range = g["range"]
    player.gun.bullet_speed = g["bullet_speed"]
    player.gun.ammo = g["max_ammo"]  # Set current ammo to max ammo
    player.gun.max_ammo = g["max_ammo"]
    player.gun.reload_time = g["reload_time"]
    player.gun.insta_reload_chance = g["insta_reload_chance"]
    player.gun.ammo_saver_chance = g["ammo_saver_chance"]
    player.gun.piercing = g["piercing"]
    player.gun.insta_kill_chance = g["insta_kill_chance"]
    player.gun.area_damage = g["area_damage"]
    player.gun.trinity = g["trinity"]
    player.gun.auto_shoot = g["auto_shoot"]

    # Stats manager data
    stats_manager.score = s["score"]
    stats_manager.enemies_killed = s["enemies_killed"]
    stats_manager.rounds_completed = s["rounds_completed"]
    stats_manager.flags_planted = s["flags_planted"]
    stats_manager.upgrades_purchased = s["upgrades_purchased"]
    stats_manager.money_spent = s["money_spent"]