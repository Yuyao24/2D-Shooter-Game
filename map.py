import pygame

class CollisionSprite(pygame.sprite.Sprite):
    def __init__(self, position: tuple[int, int], size: tuple[int, int], groups) -> None:
        super().__init__(groups)
        self.image = pygame.Surface(size)
        self.image.fill("Red")
        self.rect = self.image.get_frect(center=position)