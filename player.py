import pygame
from settings import AssetManager

class Player(pygame.sprite.Sprite):
    def __init__(self, position: tuple[int, int], groups, collision_sprites) -> None:
        super().__init__(groups)
        # Player image
        self.image = AssetManager.get_image("assets/images/player.png")
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

        # Gun
        self.gun = Gun(self, groups[0])

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
        self.gun.shoot(self, all_sprites, bullets, self.collision_sprites)

class Gun(pygame.sprite.Sprite):
    def __init__(self, player, groups) -> None:
        super().__init__(groups)
        self.player = player

        self.base_image = pygame.transform.scale(AssetManager.get_image("assets/images/gun.png"), (96, 48))
        self.image = self.base_image
        self.rect = self.image.get_frect(center=self.player.rect.center)
        self.z_layer = 2

        # Gun stats
        self.damage: float = 50.0
        self.fire_rate: float = 0.2 # seconds between shots
        self.range: float = 600.0
        self.bullet_speed: float = 1000.0

        # Cooldown timer
        self.last_shot_time: float = 0.0

    def update(self, dt) -> None:
        # Rotate gun to face mouse
        mouse_pos = pygame.math.Vector2(pygame.mouse.get_pos()) + self.player.offset
        direction = mouse_pos - pygame.math.Vector2(self.player.rect.center)

        if direction.length() > 0:
            direction = direction.normalize()
            rotation = direction.angle_to(pygame.math.Vector2(1, 0)) # Rotate gun to direction of movement
            self.image = pygame.transform.rotate(self.base_image, rotation)
            self.rect = self.image.get_frect(center=self.player.rect.center)

    def shoot(self, player, all_sprites, bullets, collision_sprites) -> None:
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot_time < self.fire_rate * 1000:
            return  # Still in cooldown, cannot shoot

        self.last_shot_time = current_time
        mouse_pos = pygame.math.Vector2(pygame.mouse.get_pos()) + all_sprites.offset
        direction = mouse_pos - pygame.math.Vector2(player.rect.center)

        # Default to up if no direction
        if direction.length() > 0:
            direction = direction.normalize()
        else:
            direction = pygame.math.Vector2(0, -1)

        Bullet(player.rect.center, direction, (all_sprites, bullets), collision_sprites, player)

class Bullet(pygame.sprite.Sprite):
    def __init__(self, position: tuple[int, int], direction: pygame.math.Vector2, groups, 
                 collision_sprites, player) -> None:
        super().__init__(groups)
        # Bullet image
        self.image = pygame.transform.scale(AssetManager.get_image("assets/images/bullet.png"), (32, 32))

        rotation = direction.angle_to(pygame.math.Vector2(1, 0)) # Rotate bullet to direction of movement
        self.image = pygame.transform.rotate(self.image, rotation)

        self.rect = self.image.get_frect(center=position)
        self.mask = pygame.mask.from_surface(self.image)
        self.z_layer = 1

        # Sprite groups
        self.collision_sprites = collision_sprites
        self.player = player

        # Movement attributes
        self.direction = direction
        self.speed = player.gun.bullet_speed

        # Gun stats
        self.range = player.gun.range
        self.damage = player.gun.damage

    def update(self, dt) -> None:
        self.move(dt)
        self.check_collision()
        self.check_range()

    def move(self, dt) -> None:
        self.rect.x += self.direction.x * self.speed * dt
        self.rect.y += self.direction.y * self.speed * dt

    def check_collision(self) -> None:
        for obstacle in self.collision_sprites:
            if obstacle.hitbox.colliderect(self.rect):
                self.kill()
    
    def check_range(self) -> None:
        player_pos = pygame.math.Vector2(self.player.rect.center)
        bullet_pos = pygame.math.Vector2(self.rect.center)

        if (player_pos - bullet_pos).length() > self.range:
            self.kill()
