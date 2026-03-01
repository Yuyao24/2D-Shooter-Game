import random
import pygame
from pytmx import load_pygame
from settings import AllSprites, TILE_SIZE, COLOR_BLACK
from map import GroundTile, SmallSprite, TallSprite, RectSprite, Pathfinder
from player import Player
from enemy import MeleeEnemy, RangedEnemy
from menus import pause_menu, Text, HUD
from flag import Flag

def load_map(all_sprites: pygame.sprite.Group, collision_sprites: pygame.sprite.Group):
    map_tmx = load_pygame("assets/map/world.tmx")

    for x, y, image in map_tmx.get_layer_by_name("Ground").tiles():  # Create tiles
        GroundTile((x * TILE_SIZE, y * TILE_SIZE), image, (all_sprites,))

    for obj in map_tmx.get_layer_by_name("Rocks"):  # Create collision sprites (rocks)
        SmallSprite((obj.x, obj.y), obj.image, (all_sprites, collision_sprites))

    for obj in map_tmx.get_layer_by_name("Objects"):  # Create collision sprites (Trees, pillars)
        TallSprite((obj.x, obj.y), obj.image, (all_sprites, collision_sprites))

    for obj in map_tmx.get_layer_by_name("Collisions"):  # Create collision boxes
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
    crosshair_img = pygame.image.load("assets/images/crosshair.png").convert_alpha()
    crosshair_rect = crosshair_img.get_rect()
    mouse_screen_pos = pygame.math.Vector2(pygame.mouse.get_pos())

    paused: bool = False

    # Sprite groups
    all_sprites = AllSprites()
    collision_sprites = pygame.sprite.Group()
    enemy_sprites = pygame.sprite.Group()
    bullet_sprites = pygame.sprite.Group()

    # Map
    map_tmx = load_map(all_sprites, collision_sprites)

    # Get spawn points
    player_spawn_points = [obj for obj in map_tmx.get_layer_by_name("Entities") if obj.name == "Player"]
    enemy_spawn_points = [obj for obj in map_tmx.get_layer_by_name("Entities") if obj.name == "Enemy"]
    flag_spawn_points = [obj for obj in map_tmx.get_layer_by_name("Entities") if obj.name == "Flag"]

    # Create player
    player_spawn = random.choice(player_spawn_points)
    player = Player((player_spawn.x, player_spawn.y), (all_sprites,), collision_sprites)

    # Create flag
    valid_flag_spawns = [obj for obj in flag_spawn_points if
                         pygame.math.Vector2(obj.x, obj.y).distance_to(
                             pygame.math.Vector2(player_spawn.x, player_spawn.y)) > 2500]
    flag_spawn = random.choice(valid_flag_spawns)
    flag = Flag((flag_spawn.x, flag_spawn.y),
                (all_sprites,), player)

    # Create pathfinder
    pathfinder = Pathfinder(map_tmx.width, map_tmx.height, collision_sprites)

    # Create HUD
    hud = HUD(player, flag)

    # Create enemies at points far enough from player
    valid_enemy_spawns = [obj for obj in enemy_spawn_points if
                          pygame.math.Vector2(obj.x, obj.y).distance_to(
                              pygame.math.Vector2(player_spawn.x, player_spawn.y)) > 600]

    # if valid_enemy_spawns:
    #     k = min(len(valid_enemy_spawns), random.randint(9, 12))
    #     for spawn in random.sample(valid_enemy_spawns, k=k):  # Randomly select spawn points
    #         for _ in range(random.randint(3, 5)):  # Spawn 3-5 enemies per point
    #             # Random offset to prevent stacking
    #             sx = spawn.x + random.randint(-100, 100)
    #             sy = spawn.y + random.randint(-100, 100)
    #             if random.random() < (2/3):
    #                 MeleeEnemy((sx, sy), (all_sprites, enemy_sprites), collision_sprites, player, pathfinder)
    #             else:
    #                 RangedEnemy((sx, sy), (all_sprites, enemy_sprites), collision_sprites, player, pathfinder)

    while True:
        dt = clock.tick() / 1000  # Delta time in seconds

        for event in pygame.event.get(): # Event loop
            if event.type == pygame.QUIT:
                return "QUIT"

            if event.type == pygame.MOUSEMOTION:
                mouse_screen_pos.update(event.pos)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    paused = True
                if event.key == pygame.K_r:
                    player.gun.reload()

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.math.Vector2(pygame.mouse.get_pos()) + all_sprites.offset
                if event.button == 1:
                    player.shoot(all_sprites, bullet_sprites)
                if event.button == 3:
                    if random.random() < 0.5:
                        RangedEnemy(mouse_pos, (all_sprites, enemy_sprites), collision_sprites, player, flag, pathfinder)
                    else:
                        MeleeEnemy(mouse_pos, (all_sprites, enemy_sprites), collision_sprites, player, flag, pathfinder)

        if paused:  # Check if paused
            next_state = pause_menu(screen, clock)
            if next_state == "PLAYING":
                paused = False
                mouse_screen_pos.update(pygame.mouse.get_pos())
                pygame.mouse.set_visible(False)
            elif next_state in {"MAIN_MENU", "QUIT"}:
                return next_state  # Return to game class to handle state

        screen.fill(COLOR_BLACK)  # Clear screen with black

        # Draw and update sprites
        all_sprites.update(dt)
        all_sprites.draw_with_offset(player.rect.center)

        # Calculate bullet-enemy collisions and damage
        damage_enemies(bullet_sprites, enemy_sprites)

        # Draw HUD
        hud.draw(screen)

        # Draw crosshair
        crosshair_rect.center = mouse_screen_pos
        screen.blit(crosshair_img, crosshair_rect)

        # Flag win/loss
        if flag.outcome == "DEFENDED":
            Text("You Won!", (200, 200), 64, "White").draw(screen)
        elif flag.outcome == "DESTROYED":
            Text("You Lost!", (200, 200), 64, "White").draw(screen)

        flag_pos = pygame.math.Vector2(flag.rect.center) - all_sprites.offset - pygame.math.Vector2(0, 100)
        Text(f"{flag.timer:.2f}", (flag_pos.x, flag_pos.y), 64, "White").draw(screen)

        pygame.display.flip()  # Update the display



