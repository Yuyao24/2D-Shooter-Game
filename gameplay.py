import pygame
from sound_system import *
from player import *
from menus import *

def gameplay_loop(screen, clock) -> str:

    # Create player
    player = pygame.sprite.GroupSingle()
    player.add(Player())

    paused = False
    upgrading = False
    game_over = False

    while True:
        dt = clock.tick(60) / 1000  # Delta time in seconds

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "QUIT"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    paused = True

        if paused:
            next_state = pause_menu(screen, clock)
            if next_state == "PLAYING":
                paused = False
            elif next_state == "MAIN_MENU":
                return next_state # Return to game class to call main_menu()

        if upgrading:
            pass

        if game_over:
            pass

        screen.fill((0, 0, 0))  # Clear screen with black

        player.update(dt)
        player.draw(screen)

        pygame.display.flip()  # Update the display

