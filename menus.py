import pygame
from settings import WINDOW_WIDTH, WINDOW_HEIGHT, COLOR_WHITE, COLOR_BLUE, COLOR_DARK_BLUE, COLOR_BLACK, COLOR_GREY

class Button:
    """Button for menus."""
    def __init__(self, text: str, position: tuple[int, int], width: int, height: int,
                 colour: str = COLOR_BLUE, font_size: int = 50) -> None:
        self.text_content: str = text
        self.position: tuple[int, int] = position
        self.width: int = width
        self.height: int = height
        self.colour: str = colour
        self.font_size: int = font_size
        self.font: pygame.font.Font = pygame.font.SysFont(None, font_size)

        # Button rectangle
        self.rect: pygame.Rect = pygame.Rect(position, (width, height))
        self.rect.center = position

        # Text object
        self.text_obj: Text = Text(text, position, font_size, "#000000")

        # Clickable
        self.is_clickable: bool = True


    def draw(self, screen: pygame.Surface) -> None: 
        """Renders the button on the given surface."""
        if self.is_clickable:
            if self.is_hovered():
                pygame.draw.rect(screen, COLOR_WHITE, self.rect)
                pygame.draw.rect(screen, self.colour, self.rect, 3) # Border
                self.text_obj.draw(screen)
            else:
                pygame.draw.rect(screen, self.colour, self.rect)
                pygame.draw.rect(screen, COLOR_BLACK, self.rect, 3) # Border
                self.text_obj.draw(screen)
        else:
            pygame.draw.rect(screen, COLOR_GREY, self.rect)
            pygame.draw.rect(screen, COLOR_BLACK, self.rect, 3)  # Border
            self.text_obj.draw(screen)

    def is_clicked(self, event: pygame.event.Event) -> bool: 
        """Checks if the button was clicked in the given event."""
        if self.is_clickable:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # Button 1 is left click
                if self.is_hovered():
                    return True
        return False

    def is_hovered(self) -> bool:
        """Checks if the mouse is currently hovering over the button."""
        mouse_pos = pygame.mouse.get_pos()
        return self.rect.collidepoint(mouse_pos)

class Text:
    """Text label."""
    def __init__(self, text: str, position: tuple[int, int], font_size: int = 50,
                 colour: str | tuple[int, int, int] = "#000000") -> None:
        self.text: str = text
        self.position: tuple[int, int] = position
        self.font_size: int = font_size
        self.colour: str | tuple[int, int, int] = colour
        self.font: pygame.font.Font = pygame.font.SysFont(None, font_size)

        # Text surface and rect
        self.text_surf: pygame.Surface = self.font.render(text, True, colour)
        self.text_rect: pygame.Rect = self.text_surf.get_rect(center=position)

    def draw(self, screen: pygame.Surface) -> None:
        """Renders the text on the given surface."""
        screen.blit(self.text_surf, self.text_rect)


def main_menu(screen: pygame.Surface, clock: pygame.time.Clock) -> str:
    """
    Displays the main menu and handles user interaction.
    
    :return: The next game state (e.g., "PLAYING", "QUIT").
    """

    pygame.mouse.set_visible(True)

    # Load high score
    try:
        with open("game_save/highscore.txt", "r") as score_file:
            high_score = score_file.read()
    except FileNotFoundError:
        high_score = "0"

    # Create high-score text
    high_score_text = Text(f"High Score: {high_score}",
                           (WINDOW_WIDTH // 2, 120), font_size=100, colour=COLOR_DARK_BLUE)

    # Load save file
    try:
        with open("game_save/save_data.txt", "r") as save_file:
            save_data = save_file.read()
    except FileNotFoundError:
        save_data = None

    # Create buttons
    resume_game_button = Button("Resume Game", (WINDOW_WIDTH // 2, 300), 300, 120)
    new_game_button = Button("New Game", (WINDOW_WIDTH // 2, 450), 300, 120)
    quit_button = Button("Quit", (WINDOW_WIDTH // 2, 600), 300, 120)
    buttons = [resume_game_button, new_game_button, quit_button]

    while True:
        for event in pygame.event.get(): # Event loop
            if quit_button.is_clicked(event) or event.type == pygame.QUIT:
                return "QUIT"  # Change game state to QUIT
            if resume_game_button.is_clicked(event):
                return "PLAYING"  # Change game state to PLAYING
            if new_game_button.is_clicked(event):
                return "PLAYING"  # Change game state to PLAYING

        # Update cursor
        if any(button.is_hovered() for button in buttons):
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        if not save_data:  # Disable resume button if no save data
            resume_game_button.is_clickable = False
        else:
            resume_game_button.is_clickable = True

        screen.fill(COLOR_WHITE)  # Clear screen with a white background

        # Render buttons
        for button in buttons:
            button.draw(screen)

        # Render high score
        high_score_text.draw(screen)

        pygame.display.flip() # Update display
        clock.tick(60)

def pause_menu(screen: pygame.Surface, clock: pygame.time.Clock) -> str:
    """
    Displays the pause menu as a transparent overlay and handles user interaction.
    
    :return: The next game state (e.g., "PLAYING", "MAIN_MENU", "QUIT").
    """

    pygame.mouse.set_visible(True)

    background = screen.copy()# Take screenshot of background

    # Game paused text
    paused_text = Text("Game Paused", (WINDOW_WIDTH // 2, 150), font_size=100, colour=COLOR_DARK_BLUE)

    # Create buttons
    resume_button = Button("Resume", (WINDOW_WIDTH // 2, 325), 300, 120)
    quit_button = Button("Save and Quit", (WINDOW_WIDTH // 2, 470), 300, 120)
    buttons = [resume_button, quit_button]

    # Create a transparent overlay
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    overlay.set_alpha(128)  # 0 : transparent, 255 : opaque
    overlay.fill((0, 0, 0))  # Black tint

    while True:
        for event in pygame.event.get(): # Event loop
            if event.type == pygame.QUIT:
                return "QUIT"
            if quit_button.is_clicked(event):
                return "MAIN_MENU"  # Change game state to MAIN MENU
            if resume_button.is_clicked(event) or event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "PLAYING"  # Change game state to PLAYING

        # Update cursor
        if any(button.is_hovered() for button in buttons):
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        # Draw the captured screenshot
        screen.blit(background, (0, 0))
        # Draw the transparent overlay
        screen.blit(overlay, (0, 0))

        # Render paused text
        paused_text.draw(screen)

        # Render buttons
        for button in buttons:
            button.draw(screen)

        pygame.display.flip() # Update display
        clock.tick(60)


