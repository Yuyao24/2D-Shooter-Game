import pygame
import sys

class Game:
    def __init__(self):
        pygame.init() # Initialize Pygame
        pygame.display.set_caption("Shooter Game") # Set window title
        self.screen = pygame.display.set_mode((1280, 720))  # 16:9 aspect ratio
        self.clock = pygame.time.Clock() # Set up clock timer

        self.running = True # Game loop flag

        self.game_state = "MAIN_MENU"  # Initial game state
                                       # Possible states: MAIN_MENU, PLAYING, PAUSED, UPGRADING, GAME_OVER

    def run(self):
        while self.running: # Main game loop
            if self.game_state == "MAIN_MENU":
                pass
            elif self.game_state == "PLAYING":
                pass
            elif self.game_state == "PAUSED":
                pass
            elif self.game_state == "UPGRADING":
                pass
            elif self.game_state == "GAME_OVER":
                pass

        pygame.quit() # Quit Pygame
        sys.exit()  # Prevents Pygame quit error

if __name__ == "__main__": # Run the game
    game = Game()
    game.run()

