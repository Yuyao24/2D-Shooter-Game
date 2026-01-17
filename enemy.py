import pygame, random

class Enemy(pygame.sprite.Sprite):
    def __init__(self, position, groups, collision_sprites, player, pathfinder):
        super().__init__(groups)
        # Enemy image
        self.image = pygame.image.load('assets/images/enemy/enemy.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (128, 128))
        self.rect = self.image.get_frect(center=position)
        self.hitbox = self.rect.inflate(-60, -90)
        self.hitbox.midbottom = self.rect.midbottom
        self.z_layer = 1

        # Sprite groups
        self.collision_sprites = collision_sprites

        # AI & Pathfinding
        self.player = player
        self.target = self.player
        self.pathfinder = pathfinder
        self.path = []
        self.direction = pygame.math.Vector2()
        self.speed = random.randint(160, 200)
        self.active = False
        self.path_timer = pygame.time.get_ticks() + random.randint(0, 500)
        self.last_player_tile = None

    def update(self, dt):
        if self.active:
            self.handle_ai()
            self.handle_movement(dt)
        else:
            self.check_active()

    def check_active(self):
        enemy_vec = pygame.math.Vector2(self.rect.center)
        target_vec = pygame.math.Vector2(self.target.rect.center)
        if (target_vec - enemy_vec).length() < 600:
            self.active = True

    def handle_ai(self):
        current_time = pygame.time.get_ticks()
        if current_time < self.path_timer:
            return

        target_vec = pygame.math.Vector2(self.target.hitbox.center)
        target_tile = (int(target_vec.x // 64), int(target_vec.y // 64))

        if target_tile != self.last_player_tile:
            self.path = self.pathfinder.get_path(self.hitbox.center, target_vec)
            if self.path:
                self.path.pop(0)

            self.last_player_tile = target_tile

        self.path_timer = current_time + 500 + random.randint(-100, 100)

    def handle_movement(self, dt):
        enemy_vec = pygame.math.Vector2(self.hitbox.center)
        target_vec = pygame.math.Vector2(self.target.hitbox.center)

        if (target_vec - enemy_vec).length() < 40:
            self.direction = pygame.math.Vector2()
            return

        if self.path:
            target = self.path[0]
            self.direction = (target - enemy_vec)

            if self.direction.length() > 5:  # Slightly larger threshold to prevent oscillation
                self.direction = self.direction.normalize()

                # Horizontal movement and collision
                self.hitbox.x += self.direction.x * self.speed * dt
                self.collide("horizontal")

                # Vertical movement and collision
                self.hitbox.y += self.direction.y * self.speed * dt
                self.collide("vertical")

                # Crucial: Sync rect to hitbox midbottom, then sync hitbox back to rect if needed
                # This prevents the image and the physics from drifting
                self.rect.midbottom = self.hitbox.midbottom
            else:
                # Snap to target center when very close to ensure alignment for the next node
                self.hitbox.center = target
                self.rect.midbottom = self.hitbox.midbottom
                self.path.pop(0)

    def collide(self, direction):
        for obstacle in self.collision_sprites:
            if obstacle.hitbox.colliderect(self.hitbox):
                if direction == "horizontal":
                    if self.direction.x > 0: self.hitbox.right = obstacle.hitbox.left
                    if self.direction.x < 0: self.hitbox.left = obstacle.hitbox.right
                if direction == "vertical":
                    if self.direction.y < 0: self.hitbox.top = obstacle.hitbox.bottom
                    if self.direction.y > 0: self.hitbox.bottom = obstacle.hitbox.top