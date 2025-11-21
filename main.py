import pygame
import sys

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Shooter Game")
        self.screen = pygame.display.set_mode((1280, 720))  # 16:9 aspect ratio
        self.clock = pygame.time.Clock()

        self.running = True

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def render(self):
        self.screen.fill((0, 0, 0))  # Clear screen with solid colour
        pygame.display.flip()        # Update the display

    def run(self):
        while self.running:
            self.handle_events()
            self.render()
            self.clock.tick(60)  # Maintain 60 FPS
            dt = self.clock.get_time() / 1000  # Time since last frame

        pygame.quit()
        sys.exit()  # Prevents Pygame quit error

if __name__ == "__main__": # Prevents code from running on import
    game = Game()
    game.run()

