import pygame, random
from settings import AssetManager, TILE_SIZE
from map import Pathfinder

class Enemy(pygame.sprite.Sprite):
    """Represents an enemy entity with basic AI and pathfinding."""
    def __init__(self, position: tuple[float, float], groups: list[pygame.sprite.Group],
                 collision_sprites: pygame.sprite.Group, player: pygame.sprite.Sprite, 
                 pathfinder: Pathfinder, bullets: pygame.sprite.Group) -> None:
        super().__init__(groups)
        # Enemy image
        self.image: pygame.Surface = pygame.transform.scale(AssetManager.get_image('assets/images/enemy.png'), (128, 128))
        self.rect: pygame.FRect = self.image.get_frect(center=position)
        self.mask: pygame.Mask = pygame.mask.from_surface(self.image)
        self.hitbox: pygame.Rect = self.rect.inflate(-60, -90)
        self.hitbox.midbottom = self.rect.midbottom
        self.z_layer: int = 1

        self.offset: pygame.Vector2 = groups[0].offset if isinstance(groups, (list, tuple)) else groups.offset

        # Sprite groups
        self.collision_sprites: pygame.sprite.Group = collision_sprites
        self.bullets: pygame.sprite.Group = bullets

        # AI & Pathfinding
        self.player: pygame.sprite.Sprite = player
        self.target: pygame.sprite.Sprite = player

        self.active: bool = False
        self.pathfinder: Pathfinder = pathfinder

        self.path: list[pygame.Vector2] = []
        self.direction: pygame.Vector2 = pygame.math.Vector2()
        self.speed: int = random.randint(160, 200)

        self.path_timer: int = pygame.time.get_ticks() + random.randint(0, 500)
        self.last_target_tile: tuple[int, int] | None = None

        # Health
        self.health: float = 100.0

    def update(self, dt: float) -> None:
        """Updates the enemy state, including AI and movement."""
        if self.active:
            self.pathfind()
            self.handle_movement(dt)
        else:
            self.check_active()

    def check_active(self) -> None:
        """Checks if the player is close enough to activate the enemy."""
        distance = pygame.math.Vector2(self.rect.center).distance_to(
            pygame.math.Vector2(self.target.rect.center)
        )
        if distance < 500:
            self.active = True

    def pathfind(self) -> None:
        """Updates the path towards the target periodically."""
        current_time = pygame.time.get_ticks()
        if current_time < self.path_timer:
            return

        target_pos = pygame.math.Vector2(self.target.hitbox.center)

        random_offset = pygame.math.Vector2(random.randint(-64, 64), random.randint(-64, 64))
        target_pos = target_pos + random_offset

        target_tile = (int(target_pos.x // TILE_SIZE), int(target_pos.y // TILE_SIZE))

        if target_tile != self.last_target_tile:
            self.path = self.pathfinder.get_path(self.hitbox.center, target_pos)
            if self.path:
                self.path.pop(0)

            self.last_target_tile = target_tile

        self.path_timer = current_time + 500 + random.randint(-100, 100)

    def handle_movement(self, dt: float) -> None:
        """Moves the enemy along the current path."""
        enemy_pos = pygame.math.Vector2(self.hitbox.center)
        target_pos = pygame.math.Vector2(self.target.hitbox.center)
        distance = (target_pos - enemy_pos).length()

        if distance < 64:
            self.direction = pygame.math.Vector2()
            return

        if self.path:
            target = self.path[0]
            self.direction = (target - enemy_pos)

            if self.direction.length() > 5:
                self.direction = self.direction.normalize()
                self.hitbox.x += self.direction.x * self.speed * dt
                self.collide("horizontal")
                self.hitbox.y += self.direction.y * self.speed * dt
                self.collide("vertical")
                self.rect.midbottom = self.hitbox.midbottom
            else:
                self.hitbox.center = target
                self.rect.midbottom = self.hitbox.midbottom
                self.path.pop(0)

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

    def take_damage(self, amount: float) -> bool:
        """Reduces the enemy's health by the given amount and checks for death."""
        self.health -= amount
        if self.health <= 0:
            return True
        return False