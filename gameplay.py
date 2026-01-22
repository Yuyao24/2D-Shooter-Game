from pytmx import load_pygame
from player import *
from menus import *
from map import *
from enemy import *
from settings import *

def gameplay_loop(screen, clock) -> str:

    paused: bool = False

    # Sprite groups
    all_sprites = AllSprites()
    collision_sprites = pygame.sprite.Group()
    enemy_sprites = pygame.sprite.Group()
    bullets = pygame.sprite.Group()

    # Map
    map_tmx = load_pygame("assets/map/world.tmx")
    for x, y, image in map_tmx.get_layer_by_name("Ground").tiles(): # Create tiles
        GroundTile((x * TILE_SIZE, y * TILE_SIZE), image, (all_sprites,))

    for obj in map_tmx.get_layer_by_name("Rocks"): # Create collision sprites
        SmallSprite((obj.x, obj.y), obj.image, (all_sprites, collision_sprites))

    for obj in map_tmx.get_layer_by_name("Objects"): # Create collision sprites
        TallSprite((obj.x, obj.y), obj.image, (all_sprites, collision_sprites))

    for obj in map_tmx.get_layer_by_name("Collisions"): # Create collision boxes
        RectSprite((obj.x, obj.y), pygame.Surface((obj.width, obj.height), pygame.SRCALPHA),
                   (all_sprites, collision_sprites))

    # Get player spawn points
    player_spawn_points = [obj for obj in map_tmx.get_layer_by_name("Entities") if obj.name == "Player"]

    # Create pathfinder
    pathfinder = Pathfinder(map_tmx.width, map_tmx.height, collision_sprites)

    # Create player
    player_spawn = random.choice(player_spawn_points)
    player = Player((player_spawn.x, player_spawn.y), all_sprites, collision_sprites)

    # Create enemies at points where the player is not spawned
    enemy_spawn_points = [obj for obj in player_spawn_points if obj != player_spawn]
    for spawn_point in enemy_spawn_points:
        for i in range(random.randint(3, 5)): # Spawn 3-5 enemies per point
            # Random offset to avoid stacking
            offset_x = random.randint(-100, 100)
            offset_y = random.randint(-100, 100)

            Enemy((spawn_point.x + offset_x, spawn_point.y + offset_y), (all_sprites, enemy_sprites), collision_sprites, player, pathfinder, bullets)

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
                    direction = mouse_pos - pygame.math.Vector2(player.rect.center)
                    Bullet(player.rect.center, direction, (all_sprites, bullets), collision_sprites, player)
                if event.button == 3:
                    Enemy(mouse_pos, (all_sprites, enemy_sprites), collision_sprites, player, pathfinder, bullets)

        if paused: # Check if paused
            next_state = pause_menu(screen, clock)
            if next_state == "PLAYING":
                paused = False
            elif next_state == "MAIN_MENU":
                return next_state # Return to game class to call main_menu()
            elif next_state == "QUIT":
                return next_state # Return to game class to call quit()

        screen.fill((0, 0, 0))  # Clear screen with black

        # Draw and update sprites
        all_sprites.draw_with_offset(player.rect.center)
        all_sprites.update(dt)

        pygame.display.flip()  # Update the display

