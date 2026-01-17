import sys, time
from gameplay import *
from player import *

class Game:
    def __init__(self) -> None:
        pygame.init() # Initialize Pygame
        pygame.display.set_caption("Shooter Game") # Set window title
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))  # 16:9 aspect ratio
        self.clock = pygame.time.Clock() # Set up clock timer

        self.running: bool = True # Game loop flag
        self.game_state: str = "PLAYING"  # Initial game state
                                            # Possible states: MAIN_MENU, PLAYING, PAUSED, UPGRADING, GAME_OVER
        print("\n" + "-" * 36, "\n")
        print("CHANGE GAME STATE TO MAIN MENU LATER")
        print("\n" + "-" * 36 , "\n")

    def run(self) -> None:
        while self.running: # Main game loop
            if self.game_state == "MAIN_MENU":
                self.game_state = main_menu(self.screen, self.clock)
            elif self.game_state == "PLAYING":
                self.game_state = gameplay_loop(self.screen, self.clock)
            elif self.game_state == "UPGRADING":
                pass
            elif self.game_state == "GAME_OVER":
                pass
            elif self.game_state == "QUIT":
                self.running = False
            elif self.game_state == "PAUSED":
                self.game_state = pause_menu(self.screen, self.clock)

        time.sleep(0.15) # Delay to allow sound effects to finish
        pygame.quit() # Quit Pygame
        sys.exit()  # Prevents Pygame quit error

if __name__ == "__main__": # Run the game
    game = Game()
    game.run()

