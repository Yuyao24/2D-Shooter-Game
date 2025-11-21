import pygame
import sys

# Initialize Pygame
pygame.init()
pygame.display.set_caption("Shooter Game") # Set window title
screen = pygame.display.set_mode((1280, 720)) # 16:9 aspect ratio
clock = pygame.time.Clock()

# Main loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit() # Prevents Pygame quit error

    screen.fill((0, 0, 0))  # Clear screen with solid colour

    pygame.display.flip()   # Update the display
    clock.tick(60) # Maintain 60 FPS
    dt = clock.get_time() / 1000  # Delta time in seconds