import pygame
from sound_system import *

class Player(pygame.sprite.Sprite):
    def __init__(self, position: tuple[int, int], groups, collision_sprites) -> None:
        super().__init__(groups)
        # Player image
        self.image = pygame.image.load("assets/images/player/down/0.png").convert_alpha()
        self.rect = self.image.get_frect(center=position)
        self.hitbox = self.rect.inflate(-60, -90)
        self.hitbox.midbottom = self.rect.midbottom
        self.z_layer = 1

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
        self.hitbox.x += self.direction.x * self.speed * dt
        self.collide("horizontal")
        self.hitbox.y += self.direction.y * self.speed * dt
        self.collide("vertical")
        self.rect.midbottom = self.hitbox.midbottom

    def collide(self, direction) -> None:
        colliders = pygame.sprite.spritecollide(
            self,
            self.collision_sprites,
            False,
            lambda spr, obs: spr.hitbox.colliderect(obs.hitbox))

        for obstacle in colliders:
            if obstacle.hitbox.colliderect(self.hitbox):
                if direction == "horizontal":
                    if self.direction.x > 0: self.hitbox.right = obstacle.hitbox.left
                    if self.direction.x < 0: self.hitbox.left = obstacle.hitbox.right
                if direction == "vertical":
                    if self.direction.y < 0: self.hitbox.top = obstacle.hitbox.bottom
                    if self.direction.y > 0: self.hitbox.bottom = obstacle.hitbox.top


