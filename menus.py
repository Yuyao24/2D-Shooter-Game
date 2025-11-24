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
        self.rect.center = position

        # Text
        self.text_surf = self.font.render(text, True, "#FFFFFF")
        self.text_rect = self.text_surf.get_rect(center=self.rect.center)

    def draw(self): # Render button
        pygame.draw.rect(screen, self.colour, self.rect)
        screen.blit(self.text_surf, self.text_rect)



pygame.init()
pygame.display.set_caption("Menu gui test")
screen = pygame.display.set_mode((1280, 720))
clock = pygame.time.Clock()

button1 = Button("Hello", (640,360), 150, 100, "Blue")

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    screen.fill((0,0,0))

    button1.draw()

    pygame.display.flip()
    clock.tick(60)




