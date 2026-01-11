import pygame

class GroundTile(pygame.sprite.Sprite):
    def __init__(self, position: tuple[int, int], surf, groups) -> None:
        super().__init__(groups)
        self.image = surf
        self.rect = surf.get_frect(topleft=position)
        self.z_layer = 0

class SmallSprite(pygame.sprite.Sprite):
    def __init__(self, position: tuple[int, int], surf, groups) -> None:
        super().__init__(groups)
        self.image = surf
        self.rect = surf.get_frect(topleft=position)
        self.hitbox = self.rect.inflate(0, -30)
        self.hitbox.midbottom = self.rect.midbottom
        self.z_layer = 1

class TallSprite(pygame.sprite.Sprite):
    def __init__(self, position: tuple[int, int], surf, groups) -> None:
        super().__init__(groups)
        self.image = surf
        self.rect = surf.get_frect(topleft=position)
        self.hitbox = pygame.Rect((0, 0), (70, 55))
        self.hitbox.midbottom = self.rect.midbottom
        self.z_layer = 1

