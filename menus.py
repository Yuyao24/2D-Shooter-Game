import pygame

class Button:
    def __init__(self, text: str, position: tuple[int, int], width: int, height: int,
                 colour: str = "#00A2E8", font_size: int = 50) -> None:
        self.text = text
        self.position = position
        self.width = width
        self.height = height
        self.colour = colour
        self.font_size = font_size
        self.font = pygame.font.SysFont(None, font_size)

        # Button rectangle
        self.rect = pygame.Rect(position, (width, height))
        self.rect.center = position

        # Text
        self.text = Text(text, position, font_size, "#000000")


    def draw(self, screen) -> None: # Render button
        if self.is_hovered():
            pygame.draw.rect(screen, "White", self.rect)
            pygame.draw.rect(screen, self.colour, self.rect, 3) # Border
            self.text.draw(screen)
        else:
            pygame.draw.rect(screen, self.colour, self.rect)
            pygame.draw.rect(screen, "Black", self.rect, 3) # Border
            self.text.draw(screen)

    def is_clicked(self, event) -> bool: # Checks if button is clicked
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # Button 1 is left click
            if self.is_hovered():
                return True
        return False

    def is_hovered(self) -> bool:
        mouse_pos = pygame.mouse.get_pos()
        return self.rect.collidepoint(mouse_pos)

class Text:
    def __init__(self, text: str, position: tuple[int, int], font_size: int = 50, colour: str = "#000000") -> None:
        self.text = text
        self.position = position
        self.font_size = font_size
        self.colour = colour
        self.font = pygame.font.SysFont(None, font_size)

        # Text surface and rect
        self.text_surf = self.font.render(text, True, colour)
        self.text_rect = self.text_surf.get_rect(center=position)

    def draw(self, screen) -> None:
        screen.blit(self.text_surf, self.text_rect)


def main_menu(screen, clock) -> str:

    # Load high score
    try:
        with open("game_save/highscore.txt", "r") as score_file:
            high_score = score_file.read()
    except FileNotFoundError:
        high_score = "0"

    # Create high-score text
    high_score_text = Text(f"High Score: {high_score}", (640, 120), font_size=100, colour="#3F48CC") 

    # Create buttons
    resume_game_button = Button("Resume Game", (640, 300), 300, 120)
    new_game_button = Button("New Game", (640, 450), 300, 120)
    quit_button = Button("Quit", (640, 600), 300, 120)
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

        screen.fill("#FFFFFF")  # Clear screen with a white background

        # Render buttons
        for button in buttons:
            button.draw(screen)

        # Render high score
        high_score_text.draw(screen)

        pygame.display.flip() # Update display
        clock.tick(60)

def pause_menu(screen, clock) -> str:
    background = screen.copy()# Take screenshot of background

    # Game paused text
    paused_text = Text("Game Paused", (640, 150), font_size=100, colour="#3F48CC")

    # Create buttons
    resume_button = Button("Resume", (640, 325), 300, 120)
    quit_button = Button("Save and Quit", (640, 470), 300, 120)
    buttons = [resume_button, quit_button]

    # Create a transparent overlay
    overlay = pygame.Surface((1280, 720))
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


