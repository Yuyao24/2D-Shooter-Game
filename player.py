import pygame
from settings import AssetManager

class Player(pygame.sprite.Sprite):
    """Represents the player-controlled entity."""
    def __init__(self, position: tuple[int, int], groups: list[pygame.sprite.Group], collision_sprites: pygame.sprite.Group) -> None:
        super().__init__(groups)
        # Player image
        self.image: pygame.Surface = AssetManager.get_image("assets/images/player.png")
        self.rect: pygame.FRect = self.image.get_frect(center=position)
        self.hitbox: pygame.Rect = self.rect.inflate(-60, -90)
        self.hitbox.midbottom = self.rect.midbottom
        self.z_layer: int = 1

        # Movement attributes
        self.speed: int = 300
        self.direction: pygame.Vector2 = pygame.math.Vector2(0, 0)

        # Sprite groups
        self.collision_sprites: pygame.sprite.Group = collision_sprites
        # Assuming groups[0] is AllSprites which has the offset
        self.offset: pygame.Vector2 = groups[0].offset if isinstance(groups, (list, tuple)) else groups.offset

        # Gun
        self.gun: Gun = Gun(self, groups[0])  # groups[0] is AllSprites

    def update(self, dt: float) -> None:
        """Updates the player state once per frame."""
        self.handle_movement(dt)

    def handle_movement(self, dt: float) -> None:
        """Handles player input and movement with collision detection."""
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

    def collide(self, direction: str) -> None:
        """Handles collisions with obstacles."""
        for obstacle in self.collision_sprites:
            if obstacle.hitbox.colliderect(self.hitbox):
                if direction == "horizontal":
                    if self.direction.x > 0: self.hitbox.right = obstacle.hitbox.left
                    if self.direction.x < 0: self.hitbox.left = obstacle.hitbox.right
                if direction == "vertical":
                    if self.direction.y < 0: self.hitbox.top = obstacle.hitbox.bottom
                    if self.direction.y > 0: self.hitbox.bottom = obstacle.hitbox.top

    def shoot(self, all_sprites: pygame.sprite.AbstractGroup, bullets: pygame.sprite.Group) -> None:
        """Fires the player's weapon."""
        self.gun.shoot(self, all_sprites, bullets, self.collision_sprites)

class Gun(pygame.sprite.Sprite):
    """Represents the weapon held by the player."""
    def __init__(self, player: Player, groups: pygame.sprite.AbstractGroup | list[pygame.sprite.AbstractGroup]) -> None:
        super().__init__(groups)
        self.player: Player = player

        self.base_image: pygame.Surface = AssetManager.get_image("assets/images/gun.png")
        self.base_image: pygame.Surface = pygame.transform.scale(self.base_image, (96, 48))
        self.base_image_flipped: pygame.Surface = pygame.transform.flip(self.base_image, True, False)
        self.image: pygame.Surface = self.base_image
        self.rect: pygame.FRect = self.image.get_frect(center=self.player.rect.center)
        self.z_layer: int = 2

        # Gun stats
        self.damage: float = 50.0
        self.fire_rate: float = 0.2 # seconds between shots
        self.range: float = 600.0
        self.bullet_speed: float = 1000.0

        # Cooldown timer
        self.last_shot_time: float = 0.0

    def update(self, dt: float) -> None:
        """Updates the gun's position and rotation based on the player's movement direction and mouse position."""

        # Rotate gun to face mouse
        mouse_pos = pygame.math.Vector2(pygame.mouse.get_pos()) + self.player.offset
        direction = mouse_pos - pygame.math.Vector2(self.player.rect.center)

        if direction.length() > 0:
            direction = direction.normalize()

        base_image = self.base_image
        aiming_left = direction.x < 0
        if aiming_left: # Flipped image if aiming left
            base_image = self.base_image_flipped

        rotation = direction.angle_to(pygame.math.Vector2(1, 0)) # Rotate gun to direction of movement
        if aiming_left: # Flip rotation if aiming left
            rotation += 180

        self.image = pygame.transform.rotate(base_image, rotation)
        self.rect = self.image.get_frect(center=self.player.rect.center) # Update rect position

    def shoot(self, player: Player, all_sprites: pygame.sprite.AbstractGroup, bullets: pygame.sprite.Group, collision_sprites: pygame.sprite.Group) -> None:
        """Creates a bullet if the gun is not on cooldown."""
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
    """Represents a projectile fired by a gun."""
    def __init__(self, position: tuple[float, float], direction: pygame.math.Vector2, 
                 groups: pygame.sprite.AbstractGroup | list[pygame.sprite.AbstractGroup], 
                 collision_sprites: pygame.sprite.Group, player: Player) -> None:
        super().__init__(groups)
        # Bullet image
        self.image: pygame.Surface = pygame.transform.scale(AssetManager.get_image("assets/images/bullet.png"), (32, 32))

        rotation = direction.angle_to(pygame.math.Vector2(1, 0)) # Rotate bullet to direction of movement
        self.image = pygame.transform.rotate(self.image, rotation)

        self.rect: pygame.FRect = self.image.get_frect(center=position)
        self.mask: pygame.Mask = pygame.mask.from_surface(self.image)
        self.z_layer: int = 1

        # Sprite groups
        self.collision_sprites: pygame.sprite.Group = collision_sprites
        self.player: Player = player

        # Movement attributes
        self.direction: pygame.Vector2 = direction
        self.speed: float = player.gun.bullet_speed

        # Gun stats
        self.range: float = player.gun.range
        self.damage: float = player.gun.damage

    def update(self, dt: float) -> None:
        """Updates bullet position and checks for collisions or range expiration."""
        self.move(dt)
        self.check_collision()
        self.check_range()

    def move(self, dt: float) -> None:
        """Moves the bullet according to its direction and speed."""
        self.rect.x += self.direction.x * self.speed * dt
        self.rect.y += self.direction.y * self.speed * dt

    def check_collision(self) -> None:
        """Checks for collisions with obstacles and destroys the bullet on impact."""
        for obstacle in self.collision_sprites:
            if obstacle.hitbox.colliderect(self.rect):
                self.kill()
    
    def check_range(self) -> None:
        """Destroys the bullet if it travels beyond its maximum range."""
        player_pos = pygame.math.Vector2(self.player.rect.center)
        bullet_pos = pygame.math.Vector2(self.rect.center)

        if (player_pos - bullet_pos).length() > self.range:
            self.kill()
