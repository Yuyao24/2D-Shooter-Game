import pygame
import os

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_CENTER = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)

TILE_SIZE = 64

# Colors
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_BLUE = "#00A2E8"
COLOR_DARK_BLUE = "#3F48CC"

class AssetManager:
    _images = {}

    @classmethod
    def get_image(cls, path: str) -> pygame.Surface:
        if path not in cls._images:
            if not os.path.exists(path):
                # Fallback if path is relative to assets
                alt_path = os.path.join("assets", "images", os.path.basename(path))
                if os.path.exists(alt_path):
                    path = alt_path
            
            cls._images[path] = pygame.image.load(path).convert_alpha()
        return cls._images[path]

class AllSprites(pygame.sprite.Group):
    def __init__(self) -> None:
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.offset = pygame.Vector2(0, 0)

    def draw_with_offset(self, target_pos: pygame.Vector2 | tuple[float, float]) -> None:
        self.offset.x = target_pos[0] - WINDOW_WIDTH / 2
        self.offset.y = target_pos[1] - WINDOW_HEIGHT / 2
        
        # Sort by z_layer then by bottom Y for Y-sorting
        for sprite in sorted(self.sprites(), key=lambda s: (getattr(s, 'z_layer', 0), s.rect.bottom)):
            self.display_surface.blit(sprite.image, sprite.rect.topleft - self.offset)
