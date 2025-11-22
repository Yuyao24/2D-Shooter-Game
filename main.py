import pygame
import sys

class Game:
    def __init__(self):
        pygame.init() # Initialize Pygame
        pygame.display.set_caption("Shooter Game") # Set window title
        self.screen = pygame.display.set_mode((1280, 720))  # 16:9 aspect ratio
        self.clock = pygame.time.Clock() # Set up clock timer

        self.running = True

    def run(self):
        while self.running: # Main game loop
            for event in pygame.event.get(): # Event handling
                if event.type == pygame.QUIT:
                    self.running = False      # Stop the game loop

            self.screen.fill((0, 0, 0))  # Clear screen with solid colour

            pygame.display.flip()        # Update the display
            self.clock.tick(60)         # Maintain 60 FPS
            dt = self.clock.tick(60) / 1000  # Time since last frame

        pygame.quit() # Quit Pygame
        sys.exit()  # Prevents Pygame quit error

if __name__ == "__main__": # Run the game
    game = Game()
    game.run()

