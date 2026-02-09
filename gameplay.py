import random
import pygame
from pytmx import load_pygame
from settings import AllSprites, TILE_SIZE, COLOR_BLACK
from map import GroundTile, SmallSprite, TallSprite, RectSprite, Pathfinder
from player import Player
from enemy import Enemy
from menus import pause_menu

def gameplay_loop(screen: pygame.Surface, clock: pygame.time.Clock) -> str:
    """
    The main gameplay loop where the game action takes place.
    
    :param screen: The surface to draw the game on.
    :param clock: The clock to control the frame rate.
    :return: The next game state (e.g., "QUIT", "MAIN_MENU").
    """

    paused: bool = False

    # Sprite groups
    all_sprites = AllSprites()
    collision_sprites = pygame.sprite.Group()
    enemy_sprites = pygame.sprite.Group()
    bullet_sprites = pygame.sprite.Group()

    # Map
    map_tmx = load_pygame("assets/map/world.tmx")
    for x, y, image in map_tmx.get_layer_by_name("Ground").tiles(): # Create tiles
        GroundTile((x * TILE_SIZE, y * TILE_SIZE), image, (all_sprites,))

    for obj in map_tmx.get_layer_by_name("Rocks"): # Create collision sprites (rocks)
        SmallSprite((obj.x, obj.y), obj.image, (all_sprites, collision_sprites))

    for obj in map_tmx.get_layer_by_name("Objects"): # Create collision sprites (Trees, pillars)
        TallSprite((obj.x, obj.y), obj.image, (all_sprites, collision_sprites))

    for obj in map_tmx.get_layer_by_name("Collisions"): # Create collision boxes
        RectSprite((obj.x, obj.y), pygame.Surface((obj.width, obj.height), pygame.SRCALPHA),
                   (all_sprites, collision_sprites))

    # Get spawn points
    player_spawn_points = [obj for obj in map_tmx.get_layer_by_name("Entities") if obj.name == "Player"]
    enemy_spawn_points = [obj for obj in map_tmx.get_layer_by_name("Entities") if obj.name == "Enemy"]

    # Create player
    player_spawn = random.choice(player_spawn_points)
    player = Player((player_spawn.x, player_spawn.y), (all_sprites,), collision_sprites)

    # Create pathfinder
    pathfinder = Pathfinder(map_tmx.width, map_tmx.height, collision_sprites)

    # Create enemies at points far enough from player
    valid_enemy_spawns = [obj for obj in enemy_spawn_points if
                          pygame.math.Vector2(obj.x, obj.y).distance_to(
                              pygame.math.Vector2(player_spawn.x, player_spawn.y)) > 600]

    if valid_enemy_spawns:
        k = min(len(valid_enemy_spawns), random.randint(9, 12))
        for spawn in random.sample(valid_enemy_spawns, k=k):  # Randomly select spawn points
            for _ in range(random.randint(3, 5)):  # Spawn 3-5 enemies per point
                # Random offset to prevent stacking (do not mutate TMX object)
                sx = spawn.x + random.randint(-100, 100)
                sy = spawn.y + random.randint(-100, 100)
                Enemy((sx, sy), (all_sprites, enemy_sprites), collision_sprites, player, pathfinder, bullet_sprites)

    while True:
        dt = clock.tick(60) / 1000  # Delta time in seconds

        for event in pygame.event.get(): # Event loop
            if event.type == pygame.QUIT:
                return "QUIT"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    paused = True
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.math.Vector2(pygame.mouse.get_pos()) + all_sprites.offset
                if event.button == 1:
                    player.shoot(all_sprites, bullet_sprites)
                if event.button == 3:
                    Enemy(mouse_pos, (all_sprites, enemy_sprites), collision_sprites, player, pathfinder, bullet_sprites)

        if paused:  # Check if paused
            next_state = pause_menu(screen, clock)
            if next_state == "PLAYING":
                paused = False
            elif next_state in {"MAIN_MENU", "QUIT"}:
                return next_state  # Return to game class to handle state

        screen.fill(COLOR_BLACK)  # Clear screen with black

        # Draw and update sprites
        all_sprites.draw_with_offset(player.rect.center)
        all_sprites.update(dt)

        pygame.display.flip()  # Update the display

