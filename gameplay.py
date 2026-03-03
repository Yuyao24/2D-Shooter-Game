import random
import pygame
from pytmx import load_pygame
from settings import AllSprites, TILE_SIZE, COLOR_BLACK
from map import GroundTile, SmallSprite, TallSprite, RectSprite, Pathfinder
from player import Player
from enemy import MeleeEnemy, RangedEnemy
from menus import pause_menu, Text, HUD
from flag import Flag

class RoundManager:
    """
    Manages the progression and state of a single round in the game.
    """
    def __init__(self, screen, clock) -> None:
        self.screen = screen
        self.clock = clock

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
        damage_enemies(self.bullet_sprites, self.enemy_sprites)
        return self.check_round_end()

    def draw(self, mouse_screen_pos) -> None:
        """
        Draws all game entities, HUD, and crosshair.

        :param mouse_screen_pos: Position of the mouse in screen coordinates
        """
        self.screen.fill(COLOR_BLACK)
        self.all_sprites.draw_with_offset(self.player.rect.center)
        self.hud.draw(self.screen)

        # flag_position = self.flag.rect.center - self.all_sprites.offset - pygame.math.Vector2(0, 100)
        # Text(f"{self.flag.timer:.2f}", flag_position, 32, (255, 255, 255)).draw(self.screen)

        self.crosshair_rect.center = mouse_screen_pos
        self.screen.blit(self.crosshair_img, self.crosshair_rect)

        pygame.display.flip()

    def start_new_round(self) -> None:
        """
        Initializes a new round by resetting all game entities.
        """
        # Increment round number
        self.round_number += 1

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

        self.hud.flag = self.flag

        # self.show_message(f"ROUND {self.round_number}", 1500)

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

    def spawn_group(self, position, count):
        pass

    def spawn_enemies(self, player_spawn):
        valid_enemy_spawns = [obj for obj in self.enemy_spawn_points if
                              pygame.math.Vector2(obj.x, obj.y).distance_to(
                                  pygame.math.Vector2(player_spawn.x, player_spawn.y)) > 600]

        base_count = 5 + (self.round_number * 2)

        num_spawns = min(len(valid_enemy_spawns), max(3, base_count // 3))
        selected_spawns = random.sample(valid_enemy_spawns, num_spawns)
        enemies_per_spawn = max(1, base_count // num_spawns)

        for spawn in selected_spawns:
            for i in range(enemies_per_spawn):
                sx = spawn.x + random.randint(-100, 100)
                sy = spawn.y + random.randint(-100, 100)

                if random.random() < 0.7:
                    enemy = MeleeEnemy((sx, sy), (self.all_sprites, self.enemy_sprites),
                                       self.collision_sprites, self.player, self.flag, self.pathfinder)
                else:
                    enemy = RangedEnemy((sx, sy), (self.all_sprites, self.enemy_sprites),
                                        self.collision_sprites, self.player, self.flag, self.pathfinder)

                enemy.health *= (1 + self.round_number * 0.15)

    def show_message(self, message, duration_ms):
        start_time = pygame.time.get_ticks()
        font = pygame.font.Font(None, 72)

        while pygame.time.get_ticks() - start_time < duration_ms:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "QUIT"

            overlay = pygame.Surface(self.screen.get_size())
            overlay.fill((0, 0, 0))
            overlay.set_alpha(180)
            self.screen.blit(overlay, (0, 0))

            text = font.render(message, True, (255, 255, 255))
            rect = text.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2))
            self.screen.blit(text, rect)

            pygame.display.flip()
            self.clock.tick(60)

        return None

    def check_round_end(self) -> str | None:
        """
        Checks if the round has ended and returns the outcome.
        :return: "CONTINUE", "GAME_OVER", or None
        """
        # Check if flag is defended or destroyed
        if self.flag.outcome == "DEFENDED" or len(self.enemy_sprites) == 0:
            self.start_new_round()
            # self.flag.outcome = None
        elif self.flag.outcome == "DESTROYED":
            self.start_new_round()
            # self.flag.outcome = None

        # Check if player is dead
        if self.player.health <= 0:
            self.player.lives -= 1
            # Check if player has lives left
            if self.player.lives <= 0:
                return "GAME_OVER" # Game Lost
            else:
                # Next round if player has lives left
                self.start_new_round()

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
                         (self.all_sprites,), self.player)

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

def damage_enemies(bullet_sprites, enemy_sprites) -> None:
    """
    Detects collisions between bullets and enemies, and deals damage to them.
    Kills enemies if health drops to 0.

    :param bullet_sprites: Group of bullet sprite objects.
    :param enemy_sprites: Group of enemy sprite objects.
    """
    # Collision detection between bullets and enemies
    hits = pygame.sprite.groupcollide(bullet_sprites, enemy_sprites,
                                      True, False,
                                      collided=bullet_enemy_mask_collide)

    # Damage enemies and kill them if necessary
    for bullet, enemies_hit in hits.items():
        for enemy in enemies_hit:
            died = enemy.take_damage(bullet.damage)
            enemy.active = True
            if died:
                enemy.kill()

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

    while True:
        dt = clock.tick() / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "QUIT"

            if event.type == pygame.MOUSEMOTION:
                mouse_screen_pos.update(event.pos)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    paused = True
                if event.key == pygame.K_r:
                    round_manager.player.gun.reload()
                if event.key == pygame.K_f:
                    round_manager.player.rect.center = round_manager.flag.rect.center
                    round_manager.player.hitbox.midbottom = round_manager.player.rect.midbottom

            if event.type == pygame.MOUSEBUTTONDOWN and not paused:
                mouse_pos = pygame.math.Vector2(pygame.mouse.get_pos()) + round_manager.all_sprites.offset
                if event.button == 1:
                    round_manager.player.shoot(round_manager.all_sprites, round_manager.bullet_sprites)
                if event.button == 3:
                    if random.random() < 0.5:
                        RangedEnemy(mouse_pos, (round_manager.all_sprites, round_manager.enemy_sprites),
                                    round_manager.collision_sprites, round_manager.player,
                                    round_manager.flag, round_manager.pathfinder)
                    else:
                        MeleeEnemy(mouse_pos, (round_manager.all_sprites, round_manager.enemy_sprites),
                                   round_manager.collision_sprites, round_manager.player,
                                   round_manager.flag, round_manager.pathfinder)

        if paused:
            next_state = pause_menu(screen, clock)
            if next_state == "PLAYING":
                paused = False
                mouse_screen_pos.update(pygame.mouse.get_pos())
                pygame.mouse.set_visible(False)
            elif next_state in {"MAIN_MENU", "QUIT"}:
                return next_state
            continue

        next_state = round_manager.update(dt)

        if next_state == "GAME_OVER":
            return "GAME_OVER" # Go to game over screen
        # If "CONTINUE", continue with the next round
        
        round_manager.draw(mouse_screen_pos)

