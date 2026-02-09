import pygame, random
from settings import AssetManager, TILE_SIZE

class Enemy(pygame.sprite.Sprite):
    def __init__(self, position, groups, collision_sprites, player, pathfinder, bullets) -> None:
        super().__init__(groups)
        # Enemy image
        self.image = pygame.transform.scale(AssetManager.get_image('assets/images/enemy.png'), (128, 128))
        self.rect = self.image.get_frect(center=position)
        self.mask = pygame.mask.from_surface(self.image)
        self.hitbox = self.rect.inflate(-60, -90)
        self.hitbox.midbottom = self.rect.midbottom
        self.z_layer = 1

        self.offset = groups[0].offset

        # Sprite groups
        self.collision_sprites = collision_sprites
        self.bullets = bullets

        # AI & Pathfinding
        self.player = player
        self.target = self.player

        self.active = False
        self.pathfinder = pathfinder

        self.path = []
        self.direction = pygame.math.Vector2()
        self.speed = random.randint(160, 200)

        self.path_timer = pygame.time.get_ticks() + random.randint(0, 500)
        self.last_target_tile = None

        self.health = 100

    def update(self, dt) -> None:
        if self.active:
            self.pathfind()
            self.handle_movement(dt)
        else:
            self.check_active()
        
        self.check_hit()

    def check_active(self) -> None:
        distance = pygame.math.Vector2(self.rect.center).distance_to(
            pygame.math.Vector2(self.target.rect.center)
        )
        if distance < 500 or self.check_hit():
            self.active = True

    def pathfind(self) -> None:
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

    def handle_movement(self, dt) -> None:
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

    def collide(self, direction) -> None:
        for obstacle in self.collision_sprites:
            if obstacle.hitbox.colliderect(self.hitbox):
                if direction == "horizontal":
                    if self.direction.x > 0: self.hitbox.right = obstacle.hitbox.left
                    if self.direction.x < 0: self.hitbox.left = obstacle.hitbox.right
                if direction == "vertical":
                    if self.direction.y < 0: self.hitbox.top = obstacle.hitbox.bottom
                    if self.direction.y > 0: self.hitbox.bottom = obstacle.hitbox.top

    def check_hit(self) -> bool:
        for bullet in self.bullets:
            offset = (bullet.rect.left - self.rect.left, bullet.rect.top - self.rect.top)
            if self.mask.overlap(bullet.mask, offset):
                self.take_damage(bullet.damage)
                bullet.kill()
                return True
        return False

    def take_damage(self, amount) -> None:
        self.health -= amount
        if self.health <= 0:
            self.kill()
