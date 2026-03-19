import sys
import pygame
from settings import UI_SCALE, WINDOW_WIDTH, WINDOW_HEIGHT, save_data_exists, clear_save_data, save_game_data
from gameplay import gameplay_loop
from menus import main_menu, pause_menu, game_over_menu

class Game:
    """The main Game class that initializes and runs the game application."""
    def __init__(self) -> None:
        pygame.display.init()  # Initialize Pygame
        pygame.font.init()
        pygame.display.set_caption("Shooter Game")  # Set window title
        self.screen: pygame.Surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)  # 16:9 aspect ratio
        self.clock: pygame.time.Clock = pygame.time.Clock()  # Set up clock timer

        self.running: bool = True # Game loop flag
        self.game_state: str = "MAIN_MENU"  # Initial game state
                                            # Possible states: MAIN_MENU, PLAYING, GAME_OVER, QUIT
        self.resume: bool = False  # Whether to resume from a save file
        self.game_over_stats: dict = {}  # To store stats for game over screen

    def run(self) -> None:
        """Starts the main game loop, switching between different game states."""
        while self.running: # Main game loop
            if self.game_state == "MAIN_MENU":
                self.game_state, self.resume = main_menu(self.screen, self.clock)
            elif self.game_state == "PLAYING":
                self.game_state, self.game_over_stats = gameplay_loop(self.screen, self.clock, self.resume)
            elif self.game_state == "GAME_OVER":
                clear_save_data()  # Clear save data on game over
                self.game_state = game_over_menu(self.screen, self.clock, self.game_over_stats)
            elif self.game_state == "QUIT":
                self.running = False

        pygame.quit()  # Quit Pygame
        sys.exit()  # Prevents Pygame quit error

if __name__ == "__main__": # Run the game
    game = Game()
    game.run()

