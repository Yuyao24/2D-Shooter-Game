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


    def draw(self) -> None: # Render button
        pygame.draw.rect(screen, self.colour, self.rect)
        pygame.draw.rect(screen, "Black", self.rect, 3) # Border
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

button1 = Button("Button", (640,360), 150, 100)

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




