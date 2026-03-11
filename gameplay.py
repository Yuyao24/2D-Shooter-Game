import random
from pytmx import load_pygame
from settings import *
from map import GroundTile, SmallSprite, TallSprite, RectSprite, Pathfinder
from player import Player
from enemy import MeleeEnemy, RangedEnemy
from menus import pause_menu, Text, HUD
from flag import Flag
from stats_manager import StatsManager
from upgrades import upgrade_menu

class RoundManager:
    """
    Manages the progression and state of a single round in the game.
    """
    def __init__(self, screen, clock) -> None:
        self.screen = screen
        self.clock = clock
        self.stats_manager = StatsManager()

        # Round tracking
        self.round_number: int = 1

        # Sprite groups
        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()
        self.bullet_sprites = pygame.sprite.Group()

        # Map data
        self.map_tmx = None
        self.player_spawn_points = []
        self.enemy_spawn_points = []
        self.flag_spawn_points = []

        # Player
        self.player = None

        # Other entities
        self.flag = None
        self.pathfinder = None
        self.hud = None

        # Crosshair
        self.crosshair_img = pygame.image.load("assets/images/crosshair.png").convert_alpha()
        self.crosshair_rect = self.crosshair_img.get_rect()

        self.start_game()

    def update(self, dt) -> str:
        """
        Updates all game entities, checks for enemy-bullet collisions,
        and checks if the round has ended.
        """
        self.all_sprites.update(dt)
        self.damage_enemies()
        return self.check_round_end()

    def draw(self, mouse_screen_pos) -> None:
        """
        Draws all game entities, HUD, and crosshair.

        :param mouse_screen_pos: Position of the mouse in screen coordinates
        """
        self.screen.fill(COLOR_BLACK)
        self.all_sprites.draw_with_offset(self.player.rect.center)
        self.hud.draw(self.screen)

        self.crosshair_rect.center = mouse_screen_pos
        self.screen.blit(self.crosshair_img, self.crosshair_rect)

        pygame.display.flip()

    def start_new_round(self) -> None:
        """
        Initializes a new round by resetting all game entities.
        """
        # Open upgrade menu
        next_state = upgrade_menu(self.screen, self.clock, self.player, self.stats_manager)
        if next_state == "MAIN_MENU":
            return "MAIN_MENU"
        # if CONTINUE, continue with the next round

        # Increment round number
        self.round_number += 1
        self.stats_manager.update_rounds()

        # Kill all enemies and bullets
        for sprite in list(self.enemy_sprites):
            sprite.kill()
        for sprite in list(self.bullet_sprites):
            sprite.kill()

        # Kill flag
        self.flag.kill()

        # Reset player
        player_spawn = random.choice(self.player_spawn_points)
        self.player.reset((player_spawn.x, player_spawn.y))

        # Create new flag
        self.spawn_flag(player_spawn)

        # Spawn enemies
        self.spawn_enemies(player_spawn)

        # Update HUD
        self.hud.flag = self.flag
        self.hud.round = self.round_number

        # New round message
        self.show_message(f"ROUND {self.round_number}", 2000)
        return None

    def start_game(self) -> None:
        """
        Initializes the game state for the first round, including:
        loading the map, spawning the player, flag, and enemies.
        """

        # Load map
        self.map_tmx = load_map(self.all_sprites, self.collision_sprites)
        self.player_spawn_points = [obj for obj in self.map_tmx.get_layer_by_name("Entities")
                                    if obj.name == "Player"]
        self.enemy_spawn_points = [obj for obj in self.map_tmx.get_layer_by_name("Entities")
                                   if obj.name == "Enemy"]
        self.flag_spawn_points = [obj for obj in self.map_tmx.get_layer_by_name("Entities")
                                  if obj.name == "Flag"]

        # Create player
        player_spawn = random.choice(self.player_spawn_points)
        self.player = Player((player_spawn.x, player_spawn.y),
                             (self.all_sprites,), self.collision_sprites)

        # Create flag
        self.spawn_flag(player_spawn)

        # Pathfinder
        self.pathfinder = Pathfinder(self.map_tmx.width, self.map_tmx.height, self.collision_sprites)

        # Spawn enemies
        self.spawn_enemies(player_spawn)

        # HUD
        self.hud = HUD(self.player, self.flag)

        # Show start message
        self.show_message(f"ROUND {self.round_number}", 2000)

    def spawn_group(self, position, count):
        for i in range(count):
            sx = position.x + random.randint(-100, 100)
            sy = position.y + random.randint(-100, 100)

            # 2 melee : 1 ranged
            if random.random() < (2/3):
                MeleeEnemy((sx, sy), (self.all_sprites, self.enemy_sprites),
                           self.collision_sprites, self.player, self.flag, self.pathfinder)
            else:
                RangedEnemy((sx, sy), (self.all_sprites, self.enemy_sprites),
                            self.collision_sprites, self.player, self.flag, self.pathfinder)

    def spawn_enemies(self, player_spawn):
        # Far enough from the player
        valid_enemy_spawns = [obj for obj in self.enemy_spawn_points if
                              pygame.math.Vector2(obj.x, obj.y).distance_to(
                                  pygame.math.Vector2(player_spawn.x, player_spawn.y)) > 600]

        # Spawn 3 enemies near the flag
        spawns_near_flag = [obj for obj in valid_enemy_spawns if
                           pygame.math.Vector2(obj.x, obj.y).distance_to(
                               pygame.math.Vector2(self.flag.rect.center)) < 1200]
        selection = random.sample(spawns_near_flag, 3)
        for spawn in selection:
            count = random.randint(3, 5)
            self.spawn_group(spawn, count)
            valid_enemy_spawns.remove(spawn)

        # Spawn extra enemies
        for i in range(random.randint(4, 7)):
            count = random.randint(3, 5)
            spawn = random.choice(valid_enemy_spawns)
            self.spawn_group(spawn, count)
            valid_enemy_spawns.remove(spawn)


        for enemy in self.enemy_sprites:
            enemy.calculate_difficulty(self.round_number)

    def show_message(self, message, duration_ms, color=COLOR_WHITE) -> None:
        """
        Shows a message on the screen for the specified duration.
        :param message: The message to display.
        :param duration_ms: The duration of the message in milliseconds.
        :param color: The color of the message text.
        """
        start_time = pygame.time.get_ticks()

        while pygame.time.get_ticks() - start_time < duration_ms:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return

            self.screen.fill(COLOR_BLACK)
            Text(message, WINDOW_CENTER, 72, color).draw(self.screen)

            pygame.display.flip()
            self.clock.tick(60)

    def check_round_end(self) -> str | None:
        """
        Checks if the round has ended and returns the outcome.
        :return: "CONTINUE", "GAME_OVER", or None
        """
        # Check if flag is defended or destroyed
        if self.flag.outcome == "DEFENDED":
            self.player.update_money(800)
            self.stats_manager.update_score(1000)
            self.show_message(f"ROUND WON", 2000, color=COLOR_GREEN)
            return self.start_new_round()
        elif self.flag.outcome == "DESTROYED":
            self.player.update_money(300)
            self.show_message(f"ROUND LOST", 2000, color=COLOR_RED)
            return self.start_new_round()

        if len(self.enemy_sprites) == 0 and self.flag.outcome is None:
            self.player.update_money(300)
            if self.flag.is_planted:
                self.stats_manager.update_score(1000)
            self.show_message(f"ROUND WON", 2000, color=COLOR_GREEN)
            return self.start_new_round()

        # Check if player is dead
        if self.player.health <= 0:
            self.player.lives -= 1
            # Check if player has lives left
            if self.player.lives <= 0:
                self.show_message(f"GAME OVER", 2000, color=COLOR_RED)
                return "GAME_OVER" # Game Lost
            else:
                # Next round if player has lives left
                self.show_message(f"ROUND LOST", 2000, color=COLOR_RED)
                if self.flag.is_planted:
                    self.player.update_money(300)
                return self.start_new_round()

        return "CONTINUE"

    def spawn_flag(self, player_spawn) -> None:
        """
        Spawns a new flag at a random location far enough from the player.

        :param player_spawn: The spawn point of the player.
        """
        valid_flag_spawns = [obj for obj in self.flag_spawn_points if
                             pygame.math.Vector2(obj.x, obj.y).distance_to(
                                 pygame.math.Vector2(player_spawn.x, player_spawn.y)) > 2500]
        flag_spawn = random.choice(valid_flag_spawns)
        self.flag = Flag((flag_spawn.x, flag_spawn.y),
                         (self.all_sprites,), self.player, self.stats_manager)

    def damage_enemies(self) -> None:
        """
        Detects collisions between bullets and enemies, and deals damage to them.
        Kills enemies if health drops to 0.
        """
        import random

        # Collision detection between bullets and enemies
        hits = pygame.sprite.groupcollide(self.bullet_sprites, self.enemy_sprites,
                                          False, False,
                                          collided=bullet_enemy_mask_collide)

        # Damage enemies and kill them if necessary
        for bullet, enemies_hit in hits.items():
            bullet_hit_first_enemy = False
            for enemy in enemies_hit:
                # Skip if already hit by this bullet (piercing)
                if id(enemy) in bullet.enemies_hit:
                    continue

                # Check if bullet has already hit max enemies allowed by piercing
                # max_enemies = 1 base hit + number of piercing levels
                max_enemies_allowed = bullet.piercing

                # Add this enemy to the hit set
                bullet.enemies_hit.add(id(enemy))

                # Check if we've now exceeded the max enemies (kill bullet after this enemy is processed)
                should_kill_bullet = len(bullet.enemies_hit) > max_enemies_allowed

                # Apply damage
                damage = bullet.damage

                # Check for instant kill (Lucky Shot upgrade)
                if random.random() < bullet.insta_kill_chance:
                    died = True
                    enemy.health = 0
                # Check for trinity shot (Holy Trinity upgrade - last 3 shots)
                elif bullet.is_trinity_shot:
                    died = True
                    enemy.health = 0
                else:
                    died = enemy.take_damage(damage)

                enemy.active = True

                if died:
                    enemy.kill()
                    self.player.update_money(10)
                    # Apply life steal upgrade
                    if self.player.life_steal > 0:
                        self.player.health = min(self.player.health + self.player.life_steal,
                                                 self.player.max_health)
                    self.stats_manager.update_kills()
                    self.stats_manager.update_score(50)

                # Mark that the bullet hit at least one enemy for piercing logic
                bullet_hit_first_enemy = True

                # Kill bullet if it exceeded max enemies allowed
                if should_kill_bullet:
                    bullet.kill()
                    break

            if bullet.area_damage > 0 and not bullet.has_exploded and bullet_hit_first_enemy:
                bullet.has_exploded = True
                explosion_radius = 100
                explosion_damage = bullet.damage * bullet.area_damage
                for other_enemy in self.enemy_sprites:
                    if id(other_enemy) not in bullet.enemies_hit and (
                                pygame.math.Vector2(bullet.rect.center).
                                        distance_to(other_enemy.rect.center)
                                            <= explosion_radius):
                        other_enemy.take_damage(explosion_damage)
                        other_enemy.active = True
                        if other_enemy.health <= 0:
                            other_enemy.kill()
                            self.player.update_money(10)
                            if self.player.life_steal > 0:
                                self.player.health = min(self.player.health + self.player.life_steal,
                                                         self.player.max_health)
                            self.stats_manager.update_kills()
                            self.stats_manager.update_score(50)


def load_map(all_sprites: pygame.sprite.Group, collision_sprites: pygame.sprite.Group):
    """
    Loads a map from a Tiled map file and creates sprite objects for each tile, object, and collision.

    :param all_sprites: Group to add all visual sprites to.
    :param collision_sprites: Group to add all collision sprites to.
    :return: Map TMX object.
    """
    map_tmx = load_pygame("assets/map/world.tmx")

    for x, y, image in map_tmx.get_layer_by_name("Ground").tiles():
        GroundTile((x * TILE_SIZE, y * TILE_SIZE), image, (all_sprites,))

    for obj in map_tmx.get_layer_by_name("Rocks"):
        SmallSprite((obj.x, obj.y), obj.image, (all_sprites, collision_sprites))

    for obj in map_tmx.get_layer_by_name("Objects"):
        TallSprite((obj.x, obj.y), obj.image, (all_sprites, collision_sprites))

    for obj in map_tmx.get_layer_by_name("Collisions"):
        RectSprite((obj.x, obj.y), pygame.Surface((obj.width, obj.height), pygame.SRCALPHA),
                   (all_sprites, collision_sprites))

    return map_tmx

def bullet_enemy_mask_collide(bullet: pygame.sprite.Sprite, enemy: pygame.sprite.Sprite) -> bool:
    """
    Performs a pixel-perfect collision check between a bullet and an enemy using their masks.

    :param bullet: The bullet sprite.
    :param enemy: The enemy sprite.
    :return: True if there is a collision, False otherwise.
    """
    # Check hitbox collision first
    if not bullet.rect.colliderect(enemy.rect):
        return False

    # Pixel-perfect check
    offset = (bullet.rect.left - enemy.rect.left, bullet.rect.top - enemy.rect.top)
    return enemy.mask.overlap(bullet.mask, offset) is not None

def gameplay_loop(screen: pygame.Surface, clock: pygame.time.Clock) -> str:
    """
    The main gameplay loop where the game action takes place.
    
    :param screen: The surface to draw the game on.
    :param clock: The clock to control the frame rate.
    :return: The next game state (e.g., "QUIT", "MAIN_MENU").
    """

    pygame.mouse.set_visible(False)

    round_manager = RoundManager(screen, clock)

    mouse_screen_pos = pygame.math.Vector2(pygame.mouse.get_pos())
    paused = False
    mouse_button_held = False

    while True:
        dt = clock.tick() / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "QUIT", round_manager.stats_manager.get_stats()

            if event.type == pygame.MOUSEMOTION:
                mouse_screen_pos.update(event.pos)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    paused = True
                if event.key == pygame.K_r:
                    round_manager.player.gun.reload()

            if event.type == pygame.MOUSEBUTTONDOWN and not paused:
                if event.button == 1:
                    mouse_button_held = True
                    round_manager.player.shoot(round_manager.all_sprites, round_manager.bullet_sprites)

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    mouse_button_held = False

        # Auto-shoot logic when mouse button held
        if mouse_button_held and not paused and round_manager.player.gun.auto_shoot:
            round_manager.player.shoot(round_manager.all_sprites, round_manager.bullet_sprites)

        if paused:
            next_state = pause_menu(screen, clock)
            if next_state == "PLAYING":
                paused = False
                mouse_screen_pos.update(pygame.mouse.get_pos())
                pygame.mouse.set_visible(False)
            elif next_state in {"MAIN_MENU", "QUIT"}:
                return next_state, round_manager.stats_manager.get_stats()
            continue

        # Check next state
        next_state = round_manager.update(dt)

        if next_state == "GAME_OVER":
            return "GAME_OVER", round_manager.stats_manager.get_stats() # Go to game over screen
        if next_state == "MAIN_MENU":
            return "MAIN_MENU", round_manager.stats_manager.get_stats() # Go to main menu screen
        # If "CONTINUE", continue with the next round
        
        round_manager.draw(mouse_screen_pos)

