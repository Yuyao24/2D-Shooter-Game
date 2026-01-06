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
    all_sprites = pygame.sprite.Group()
    collision_sprites = pygame.sprite.Group()

    # Map
    map_tmx = load_pygame("assets/map/world.tmx")
    for x, y, image in map_tmx.get_layer_by_name("Ground").tiles():
        Sprite((x * 64, y * 64), image, (all_sprites,))
    for obj in map_tmx.get_layer_by_name("Objects"):
        CollisionSprite((obj.x, obj.y), obj.image, (all_sprites, collision_sprites))
    for obj in map_tmx.get_layer_by_name("Collisions"):
        CollisionSprite((obj.x, obj.y), pygame.Surface((obj.width, obj.height)), (collision_sprites,))


    # Create player
    player = Player((640, 360), all_sprites, collision_sprites)

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
        all_sprites.draw(screen)
        all_sprites.update(dt)


        pygame.display.flip()  # Update the display

