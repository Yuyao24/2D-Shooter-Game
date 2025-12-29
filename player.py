import os

import pygame
from sound_system import play_sound

class Player(pygame.sprite.Sprite):
    def __init__(self) -> None:
        super().__init__()
        # Load player image
        self.image = pygame.image.load(os.path.join("assets", "player", "down", "0.png")).convert_alpha()

        # Movement and positioning
        self.pos = pygame.math.Vector2(640, 360)  # Start in the center of the screen
        self.rect = self.image.get_frect(center=self.pos)
        self.speed: int = 300
        self.velocity = pygame.math.Vector2(0, 0)

    def update(self, dt) -> None:
        self.handle_movement(dt)

    def handle_movement(self, dt) -> None:
        keys = pygame.key.get_pressed() # Get keys pressed

        # Use boolean subtraction to get direction (-1, 0, or 1)
        self.velocity.x = keys[pygame.K_d] - keys[pygame.K_a] # Right - Left
        self.velocity.y = keys[pygame.K_s] - keys[pygame.K_w] # Down - Up

        # Normalize velocity to prevent faster diagonal movement
        if self.velocity.length() > 0:
            self.velocity = self.velocity.normalize()

        # Update position using delta time
        self.pos += self.velocity * self.speed * dt
        self.rect.center = self.pos
