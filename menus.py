import pygame
import sys


class Button:
    def __init__(self, text: str, position: tuple[int, int], width: int, height: int, colour: str):
        self.text = text
        self.position = position
        self.width = width
        self.height = height
        self.colour = colour
        self.font = pygame.font.SysFont("Arial", 30)

        # Button rectangle
        self.rect = pygame.Rect(position, (width, height))

        # Text
        self.text_surf = self.font.render(text, True, "#FFFFFF")
        self.text_rect = self.text_surf.get_rect(center=self.rect.center)

    def draw(self) -> None: # Render button
        pygame.draw.rect(screen, self.colour, self.rect)
        screen.blit(self.text_surf, self.text_rect)

    def is_clicked(self): # Checks if button is clicked
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # Button 1 is left click
            if self.rect.collidepoint(event.pos):
                return True
        return False

pygame.init()
pygame.display.set_caption("Menu gui test")
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()

button1 = Button("Hello", (50,50), 150, 100, "Blue")

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if button1.is_clicked():
            print("Button clicked!")

    screen.fill("#FFFFFF")

    button1.draw()

    pygame.display.flip()
    clock.tick(60)




