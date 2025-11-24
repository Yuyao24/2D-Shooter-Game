import pygame
import sys


class Button:
    def __init__(self, text: str, position: tuple[int, int], width: int, height: int,
                 colour: str = "#00A2E8", font_size: int = 40) -> None:
        self.text = text
        self.position = position
        self.width = width
        self.height = height
        self.colour = colour
        self.font_size = font_size
        self.font = pygame.font.SysFont("Gotham Rounded", font_size)

        # Button rectangle
        self.rect = pygame.Rect(position, (width, height))
        self.rect.center = position

        # Text
        self.text_surf = self.font.render(text, True, "#000000")
        self.text_rect = self.text_surf.get_rect(center=self.rect.center)


    def draw(self, screen) -> None: # Render button
        pygame.draw.rect(screen, self.colour, self.rect)
        pygame.draw.rect(screen, "Black", self.rect, 3) # Border
        screen.blit(self.text_surf, self.text_rect)

    def is_clicked(self, event): # Checks if button is clicked
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # Button 1 is left click
            if self.rect.collidepoint(event.pos):
                return True
        return False

def main_menu(screen, clock) -> str:
    running: bool = True

    resume_game_button = Button("Resume Game", (640, 300), 300, 80)
    new_game_button = Button("New Game", (640, 450), 300, 80)
    quit_button = Button("Quit Game", (640, 600), 300, 80)

    while running:
        for event in pygame.event.get():
            if quit_button.is_clicked(event) or event.type == pygame.QUIT:
                return "QUIT"  # Change game state to QUIT
            if resume_game_button.is_clicked(event):
                return "PLAYING"  # Change game state to PLAYING
            if new_game_button.is_clicked(event):
                return "PLAYING"  # Change game state to PLAYING

        screen.fill("#FFFFFF")  # Clear screen with white background

        new_game_button.draw(screen)
        resume_game_button.draw(screen)
        quit_button.draw(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit() # Quit Pygame
    sys.exit() # Prevents Pygame quit error



