import pygame
from sound_system import *
from player import *
from menus import *

def gameplay_loop(screen, clock) -> str:
    player = pygame.sprite.GroupSingle()
    player.add(Player())

    paused = False

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
            else:
                return next_state

        screen.fill((0, 0, 0))  # Clear screen with black

        player.update(dt)
        player.draw(screen)

        pygame.display.flip()  # Update the display

