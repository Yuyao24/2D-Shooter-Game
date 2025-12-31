import os

import pygame
from sound_system import play_sound

class Player(pygame.sprite.Sprite):
    def __init__(self, position: tuple[int, int], groups, collision_sprites) -> None:
        super().__init__(groups)
        # Load player image
        self.image = pygame.image.load(os.path.join("assets", "images", "player", "down", "0.png")).convert_alpha()
        self.rect = self.image.get_frect(center=position)

        # Movement attributes
        self.speed: int = 300
        self.direction = pygame.math.Vector2(0, 0)

        # Sprite groups
        self.collision_sprites = collision_sprites


    def update(self, dt) -> None:
        self.handle_movement(dt)

    def handle_movement(self, dt) -> None:
        keys = pygame.key.get_pressed() # Get keys pressed

        # Calculate direction
        self.direction.x = keys[pygame.K_d] - keys[pygame.K_a] # RIGHT - LEFT (Right is positive)
        self.direction.y = keys[pygame.K_s] - keys[pygame.K_w] # DOWN - UP (Down is positive)

        # Normalize velocity to prevent faster diagonal movement
        if self.direction.length() > 0:
            self.direction = self.direction.normalize()

        # Update position using delta time
        self.rect.x += self.direction.x * self.speed * dt
        self.collide("horizontal")
        self.rect.y += self.direction.y * self.speed * dt
        self.collide("vertical")

    def collide(self, direction) -> None:
        for sprite in self.collision_sprites:
            if sprite.rect.colliderect(self.rect):
                if direction == "horizontal":
                    if self.direction.x > 0:
                        self.rect.right = sprite.rect.left
                    if self.direction.x < 0:
                        self.rect.left = sprite.rect.right
                if direction == "vertical":
                    if self.direction.y < 0:
                        self.rect.top = sprite.rect.bottom
                    if self.direction.y > 0:
                        self.rect.bottom = sprite.rect.top


