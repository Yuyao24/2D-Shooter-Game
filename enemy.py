import pygame, random
from settings import AssetManager, TILE_SIZE
from map import Pathfinder

class BaseEnemy(pygame.sprite.Sprite):
    """Represents an enemy entity with basic AI and pathfinding."""
    def __init__(self, position: tuple[float, float], groups: list[pygame.sprite.Group],
                 collision_sprites: pygame.sprite.Group, player: pygame.sprite.Sprite, 
                 pathfinder: Pathfinder) -> None:
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

        # AI & Pathfinding
        self.player: pygame.sprite.Sprite = player
        self.target: pygame.sprite.Sprite = player

        self.active: bool = False
        self.pathfinder: Pathfinder = pathfinder

        self.path: list[pygame.Vector2] = []
        self.direction: pygame.Vector2 = pygame.math.Vector2()
        self.speed: int = random.randint(200, 300)

        self.path_timer: int = pygame.time.get_ticks() + random.randint(0, 500)
        self.last_target_tile: tuple[int, int] | None = None

        # Health
        self.health: float = 100.0

        # Attacking
        self.attack_range: int = 64

    def update(self, dt: float) -> None:
        raise NotImplementedError ("update() must be implemented in subclasses.")

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

    def distance_to_target(self) -> float:
        """Calculates the distance from the enemy to its target."""
        return pygame.math.Vector2(self.hitbox.center).distance_to(
            pygame.math.Vector2(self.target.hitbox.center)
        )

class MeleeEnemy(BaseEnemy):
    """A stronger enemy that can deal damage to the player on contact."""
    def __init__(self, position: tuple[float, float], groups: list[pygame.sprite.Group],
                 collision_sprites: pygame.sprite.Group, player: pygame.sprite.Sprite,
                 pathfinder: Pathfinder) -> None:
        super().__init__(position, groups, collision_sprites, player, pathfinder)

        # Stats
        self.health = 100.0
        self.speed = random.randint(200, 300)
        self.attack_range = 64.0
        self.damage = 10.0

        # Attacking
        self.attack_cooldown = 1000  # milliseconds
        self.last_attack_time = 0

    def update(self, dt: float) -> None:
        """Updates the enemy state, including AI and movement."""
        if self.active:
            if self.distance_to_target() > self.attack_range:
                self.pathfind()
                self.handle_movement(dt)
            else:
                self.attack()
        else:
            self.check_active()

    def attack(self) -> None:
        """Attacks the player if within range and cooldown is over."""
        current_time = pygame.time.get_ticks()
        if current_time - self.last_attack_time >= self.attack_cooldown:
            # Inflict damage to player
            self.target.take_damage(self.damage)
            self.last_attack_time = current_time

class RangedEnemy(BaseEnemy):
    """A stronger enemy that can deal damage to the player on contact."""
    def __init__(self, position: tuple[float, float], groups: list[pygame.sprite.Group],
                 collision_sprites: pygame.sprite.Group, player: pygame.sprite.Sprite,
                 pathfinder: Pathfinder) -> None:
        super().__init__(position, groups, collision_sprites, player, pathfinder)

        # Stats
        self.health = 80.0
        self.speed = random.randint(160, 220)
        self.attack_range = 320.0
        self.damage = 15.0

        # Shooting
        self.shoot_cooldown = 1500.0 # milliseconds
        self.last_shot_time = 0.0

    def update(self, dt: float) -> None:
        """Updates the enemy state, including AI and movement."""
        if self.active:
            if self.distance_to_target() > self.attack_range or not self.has_line_of_sight():
                self.pathfind()
                self.handle_movement(dt)
            else:
                self.shoot()
        else:
            self.check_active()

    def has_line_of_sight(self) -> bool:
        """Checks if the enemy has a clear line of sight to the player."""
        # Create a line from enemy to player
        start = (int(self.rect.centerx), int(self.rect.centery))
        end = (int(self.target.rect.centerx), int(self.target.rect.centery))

        # Check for collision with obstacles along the line
        for obstacle in self.collision_sprites:
            if obstacle.hitbox.clipline(start, end):
                return False

        return True

    def shoot(self):
        """Creates and fires a bullet from the enemy's position towards the player."""
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot_time >= self.shoot_cooldown:
            target_pos = pygame.math.Vector2(self.target.rect.center)
            bullet_direction = target_pos - pygame.math.Vector2(self.rect.center)
            bullet_direction = bullet_direction.normalize()

            EnemyBullet(self.rect.center, bullet_direction,
                        (self.groups()[0]), self.collision_sprites, self.target, self)

            self.last_shot_time = pygame.time.get_ticks()

class EnemyBullet(pygame.sprite.Sprite):
    """Represents a projectile fired by a ranged enemy."""
    def __init__(self, position: tuple[float, float], direction: pygame.math.Vector2,
                 groups: list[pygame.sprite.Group], collision_sprites: pygame.sprite.Group,
                 target: pygame.sprite.Sprite, enemy: pygame.sprite.Sprite) -> None:
        super().__init__(groups)
        # Bullet image
        self.image = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.circle(self.image, "RED", (8, 8), 8)
        self.rect = self.image.get_rect(center=position)
        self.mask = pygame.mask.from_surface(self.image)
        self.z_layer: int = 1

        # Sprite groups
        self.collision_sprites: pygame.sprite.Group = collision_sprites
        self.target: pygame.sprite.Sprite = target

        # Movement attributes
        self.direction: pygame.Vector2 = direction
        self.speed: float = 500.0

        # Damage
        self.damage: float = enemy.damage

    def update(self, dt: float) -> None:
        """Updates bullet"""
        self.move(dt)
        self.check_collision()
        self.check_range()
        self.check_hit_target()

    def move(self, dt: float) -> None:
        """Moves the bullet according to its direction and speed."""
        self.rect.x += self.direction.x * self.speed * dt
        self.rect.y += self.direction.y * self.speed * dt

    def check_collision(self) -> None:
        """Checks for collisions with obstacles and destroys the bullet on impact."""
        if any(obstacle.hitbox.colliderect(self.rect) for
               obstacle in self.collision_sprites):
            self.kill()

    def check_range(self) -> None:
        """Destroys the bullet if it travels beyond its maximum range."""
        target_pos = pygame.math.Vector2(self.target.rect.center)
        bullet_pos = pygame.math.Vector2(self.rect.center)
        if (target_pos - bullet_pos).length() > 500:
            self.kill()

    def check_hit_target(self):
        """Checks if the bullet has hit the target and destroys it."""
        if pygame.sprite.collide_mask(self, self.target):
            self.target.take_damage(self.damage)
            self.kill()