import pygame
import random
from pytmx import load_pygame

from sound_system import *
from player import *
from menus import *
from map import *
from settings import *

def gameplay_loop(screen, clock) -> str:

    paused: bool = False

    # Sprite groups
    all_sprites = AllSprites()
    collision_sprites = pygame.sprite.Group()

    # Map
    map_tmx = load_pygame("assets/map/world.tmx")
    for x, y, image in map_tmx.get_layer_by_name("Ground").tiles(): # Create tiles
        Sprite((x * TILE_SIZE, y * TILE_SIZE), image, (all_sprites,))

    for obj in map_tmx.get_layer_by_name("Objects"): # Create collision sprites
        CollisionSprite((obj.x, obj.y), obj.image, (all_sprites, collision_sprites))

    player_spawn_points = []
    for obj in map_tmx.get_layer_by_name("Entities"):
        if obj.name == "Player":
            player_spawn_points.append(obj)

    # for obj in map_tmx.get_layer_by_name("Collisions"): # Create collision sprites
    #     surf = pygame.Surface((obj.width, obj.height))
    #     CollisionSprite((obj.x, obj.y), surf, (collision_sprites,))

    #Create player
    spawn_point = random.choice(player_spawn_points)
    player = Player((spawn_point.x, spawn_point.y), all_sprites, collision_sprites)

    while True:
        dt = clock.tick(60) / 1000  # Delta time in seconds

        for event in pygame.event.get(): # Event loop
            if event.type == pygame.QUIT:
                return "QUIT"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    paused = True

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

