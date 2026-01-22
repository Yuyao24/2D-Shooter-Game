import pygame, random
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
        self.offset = groups[0].offset

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
        for obstacle in self.collision_sprites:
            if obstacle.hitbox.colliderect(self.hitbox):
                if direction == "horizontal":
                    if self.direction.x > 0: self.hitbox.right = obstacle.hitbox.left
                    if self.direction.x < 0: self.hitbox.left = obstacle.hitbox.right
                if direction == "vertical":
                    if self.direction.y < 0: self.hitbox.top = obstacle.hitbox.bottom
                    if self.direction.y > 0: self.hitbox.bottom = obstacle.hitbox.top

    def shoot(self, all_sprites, bullets) -> None:
        mouse_pos = pygame.math.Vector2(pygame.mouse.get_pos()) + all_sprites.offset
        direction = mouse_pos - pygame.math.Vector2(self.rect.center)
        Bullet(self.rect.center, direction, (all_sprites, bullets), self.collision_sprites, self)

class Bullet(pygame.sprite.Sprite):
    def __init__(self, position: tuple[int, int], direction: pygame.math.Vector2, groups, collision_sprites, player) -> None:
        super().__init__(groups)
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 0, 0), (10, 10), 10)
        self.rect = self.image.get_frect(center=position)
        self.direction = direction.normalize() if direction.length() > 0 else pygame.math.Vector2(0, -1)
        self.speed = 1500
        self.z_layer = 1

        # Sprite groups
        self.collision_sprites = collision_sprites
        self.player = player

    def update(self, dt) -> None:
        if self.direction.length() > 0:
            self.direction = self.direction.normalize()

        player_pos = pygame.math.Vector2(self.player.rect.center)
        bullet_pos = pygame.math.Vector2(self.rect.center)
         # Remove bullet if too far from player
        if (player_pos - bullet_pos).length() > 600:
            self.kill()

        self.rect.x += self.direction.x * self.speed * dt
        self.rect.y += self.direction.y * self.speed * dt
        self.check_collision()

    def check_collision(self) -> None:
        for obstacle in self.collision_sprites:
            if obstacle.hitbox.colliderect(self.rect):
                self.kill()




        

