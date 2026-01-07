import pygame

class GroundTile(pygame.sprite.Sprite):
    def __init__(self, position: tuple[int, int], surf, groups) -> None:
        super().__init__(groups)
        self.image = surf
        self.rect = surf.get_frect(topleft=position)

class CollisionSprite(pygame.sprite.Sprite):
    def __init__(self, position: tuple[int, int], surf, groups) -> None:
        super().__init__(groups)
        self.image = surf
        self.rect = surf.get_frect(topleft=position)

