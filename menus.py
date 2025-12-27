from sound_system import *

class Button:
    def __init__(self, text: str, position: tuple[int, int], width: int, height: int,
                 colour: str = "#00A2E8", font_size: int = 50) -> None:
        self.text = text
        self.position = position
        self.width = width
        self.height = height
        self.colour = colour
        self.font_size = font_size
        self.font = pygame.font.SysFont("Gotham", font_size)

        # Button rectangle
        self.rect = pygame.Rect(position, (width, height))
        self.rect.center = position

        # Text
        self.text_surf = self.font.render(text, True, "#000000")
        self.text_rect = self.text_surf.get_rect(center=self.rect.center)


    def draw(self, screen) -> None: # Render button
        if self.is_hovered():
            pygame.draw.rect(screen, "White", self.rect)
            pygame.draw.rect(screen, self.colour, self.rect, 3) # Border
            screen.blit(self.text_surf, self.text_rect)
        else:
            pygame.draw.rect(screen, self.colour, self.rect)
            pygame.draw.rect(screen, "Black", self.rect, 3) # Border
            screen.blit(self.text_surf, self.text_rect)

    def is_clicked(self, event) -> bool: # Checks if button is clicked
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # Button 1 is left click
            if self.is_hovered():
                play_sound("button_click", 0.5)
                return True
        return False

    def is_hovered(self) -> bool:
        mouse_pos = pygame.mouse.get_pos()
        return self.rect.collidepoint(mouse_pos)

def main_menu(screen, clock) -> str:

    # Load high score
    try:
        with open("game_save/highscore.txt", "r") as score_file:
            high_score = score_file.read()
    except FileNotFoundError:
        high_score = "0"

    # Create high-score text
    score_font = pygame.font.SysFont("Gotham", 100)
    high_score_surf = score_font.render(f"High Score: {high_score}", True, "#3F48CC")
    high_score_rect = high_score_surf.get_rect(center=(640, 120))

    # Create buttons
    resume_game_button = Button("Resume Game", (640, 300), 300, 120)
    new_game_button = Button("New Game", (640, 450), 300, 120)
    quit_button = Button("Quit", (640, 600), 300, 120)
    buttons = [resume_game_button, new_game_button, quit_button]

    while True:
        for event in pygame.event.get():
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
        screen.blit(high_score_surf, high_score_rect)

        pygame.display.flip() # Update display
        clock.tick(60)

def pause_menu(screen, clock, background) -> str:

    # Game paused text
    paused_font = pygame.font.SysFont("Gotham", 100)
    paused_surf = paused_font.render("Game Paused", True, "#3F48CC")
    paused_rect = paused_surf.get_rect(center=(640, 100))

    # Create buttons
    resume_button = Button("Resume", (640, 325), 300, 120)
    quit_button = Button("Quit Game", (640, 470), 300, 120)
    buttons = [resume_button, quit_button]

    # Create a semi-transparent overlay
    overlay = pygame.Surface((1280, 720))
    overlay.set_alpha(128)  # 0 is fully transparent, 255 is fully opaque
    overlay.fill((255, 255, 255))  # White tint

    while True:
        for event in pygame.event.get():
            if quit_button.is_clicked(event) or event.type == pygame.QUIT:
                return "MAIN_MENU"  # Change game state to MAIN MENU
            if resume_button.is_clicked(event) or event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "PLAYING"  # Change game state to PLAYING

        # Update cursor
        if any(button.is_hovered() for button in buttons):
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
        else:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        # Draw the captured game screen first
        screen.blit(background, (0, 0))
        # Draw the semi-transparent overlay
        screen.blit(overlay, (0, 0))

        # Render paused text
        screen.blit(paused_surf, paused_rect)

        # Render buttons
        for button in buttons:
            button.draw(screen)

        pygame.display.flip() # Update display
        clock.tick(60)


