import pygame
import os

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_CENTER = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)

TILE_SIZE = 64

# Colors
COLOR_BLACK = "#000000"
COLOR_WHITE = "#FFFFFF"
COLOR_GREY = "#808080"
COLOR_BLUE = "#00A2E8"
COLOR_DARK_BLUE = "#3F48CC"

class AssetManager:
    """Manages game assets like images to ensure they are loaded only once."""
    _images: dict[str, pygame.Surface] = {}

    @classmethod
    def get_image(cls, path: str) -> pygame.Surface:
        """
        Loads and returns an image surface. Caches the result to avoid repeated disk I/O.
        
        :param path: The file path to the image.
        :return: A pygame.Surface containing the image.
        """
        if path not in cls._images:
            cls._images[path] = pygame.image.load(path).convert_alpha()
        return cls._images[path]

class AllSprites(pygame.sprite.Group):
    """
    A custom sprite group that handles camera offset and Y-sorting (plus Z-layering).
    """
    def __init__(self) -> None:
        super().__init__()
        self.display_surface: pygame.Surface = pygame.display.get_surface()
        self.offset: pygame.Vector2 = pygame.Vector2(0, 0)

    def draw_with_offset(self, target_pos: pygame.Vector2 | tuple[float, float]) -> None:
        """
        Calculates camera offset based on a target position and draws all sprites.
        
        :param target_pos: The position the camera should center on (usually the player).
        """
        self.offset.x = target_pos[0] - WINDOW_WIDTH / 2
        self.offset.y = target_pos[1] - WINDOW_HEIGHT / 2
        
        # Sort by z_layer then by bottom Y for Y-sorting
        for sprite in sorted(self.sprites(), key=lambda s: (getattr(s, 'z_layer', 0), s.rect.bottom)):
            self.display_surface.blit(sprite.image, sprite.rect.topleft - self.offset)
