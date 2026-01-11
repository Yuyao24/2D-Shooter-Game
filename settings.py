import pygame

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720

TILE_SIZE = 64

class AllSprites(pygame.sprite.Group):
    def __init__(self) -> None:
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.offset = pygame.Vector2(0, 0)

    def draw_with_offset(self, target_pos) -> None:
        self.offset.x = target_pos[0] - WINDOW_WIDTH / 2
        self.offset.y = target_pos[1] - WINDOW_HEIGHT / 2
        for sprite in sorted(self.sprites() , key=lambda s: (s.z_layer, s.rect.bottom)):
            self.display_surface.blit(sprite.image, sprite.rect.topleft - self.offset)
