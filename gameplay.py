import pygame
import random
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

    # Create some collision sprites for testing
    for i in range(5):
        x, y = random.randint(0, WINDOW_WIDTH), random.randint(0, WINDOW_HEIGHT)
        width, height = random.randint(50, 150), random.randint(50, 150)
        CollisionSprite((x, y), (width, height), (all_sprites, collision_sprites))

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

