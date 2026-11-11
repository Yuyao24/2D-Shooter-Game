import pygame, random
from settings import AssetManager, TILE_SIZE, make_silhouette
from map import Pathfinder
from effects import FX
from sound import Audio

# Monster sprite sheets: 4 columns x 2 rows of 192 x 192 frames.
# Row 0 is the idle / walk cycle, row 1 is the attack cycle.
# scale: how much to scale the pixel art, projectile: colour of ranged attacks.
MONSTERS: dict[str, dict] = {
    # Melee
    "Larvea":      {"scale": 1.0},
    "Atrox":       {"scale": 0.9},
    "Plumette":    {"scale": 1.0},
    "Draem":       {"scale": 0.85},
    # Ranged
    "Sparchu":     {"scale": 1.0, "projectile": (255, 140, 40)},
    "Cindrill":    {"scale": 0.75, "projectile": (255, 90, 30)},
    "Cleaf":       {"scale": 0.85, "projectile": (120, 220, 80)},
    "Jacana":      {"scale": 0.9, "projectile": (255, 110, 170)},
    # Brute
    "Charmadillo": {"scale": 0.7},
}
MELEE_MONSTERS = ["Larvea", "Atrox", "Plumette", "Draem"]
RANGED_MONSTERS = ["Sparchu", "Cindrill", "Cleaf", "Jacana"]
BRUTE_MONSTERS = ["Charmadillo"]


def load_monster(name: str) -> dict:
    """
    Loads, crops and scales a monster's animation frames (cached).

    :param name: The monster's name (file name in assets/images/monsters).
    :return: Dict with "idle"/"attack" frame lists for both facings, plus a particle colour.
    """
    def build() -> dict:
        sheet = AssetManager.get_sheet(f"assets/images/monsters/{name}.png", 192, 192)
        frames = sheet[0] + sheet[1]

        # Crop every frame to the same area so the animation stays aligned
        bounds = frames[0].get_bounding_rect().unionall([f.get_bounding_rect() for f in frames[1:]])
        scale = MONSTERS[name]["scale"]

        def prepare(frame: pygame.Surface, flip: bool) -> tuple:
            image = pygame.transform.scale_by(frame.subsurface(bounds), scale)
            if flip:
                image = pygame.transform.flip(image, True, False)
            return image, make_silhouette(image, (255, 255, 255)), pygame.mask.from_surface(image)

        data = {}
        for row_name, row in (("idle", sheet[0]), ("attack", sheet[1])):
            data[row_name] = {"left": [prepare(f, False) for f in row],
                              "right": [prepare(f, True) for f in row]}

        # Average colour of the sprite, used for death particles
        image = data["idle"]["left"][0][0]
        pixels = [image.get_at((x, y)) for x in range(0, image.get_width(), 3)
                  for y in range(0, image.get_height(), 3)]
        pixels = [p for p in pixels if p.a > 200]
        data["color"] = tuple(sum(p[i] for p in pixels) // max(1, len(pixels)) for i in range(3))
        return data

    return AssetManager.cached(("monster", name), build)


class BaseEnemy(pygame.sprite.Sprite):
    """Represents an enemy entity with basic AI and pathfinding."""
    monster_pool: list[str] = MELEE_MONSTERS

    def __init__(self, position: tuple[float, float], groups: list[pygame.sprite.Group],
                 collision_sprites: pygame.sprite.Group, player: pygame.sprite.Sprite, flag: pygame.sprite.Sprite,
                 pathfinder: Pathfinder) -> None:
        super().__init__(groups)
        # Enemy animation frames
        self.monster: str = random.choice(self.monster_pool)
        self.frames: dict = load_monster(self.monster)
        self.facing: str = random.choice(["left", "right"])
        self.animation: str = "idle"
        self.frame_index: float = random.uniform(0, 4)
        self.animation_speed: float = 6.0
        self.attack_anim_timer: float = 0.0
        self.flash_timer: float = 0.0

        # Enemy image
        self.image: pygame.Surface = self.frames["idle"][self.facing][0][0]
        self.rect: pygame.FRect = self.image.get_frect(center=position)
        self.mask: pygame.Mask = self.frames["idle"][self.facing][0][2]
        self.hitbox: pygame.Rect = pygame.Rect(0, 0, 56, 36)
        self.hitbox.midbottom = self.rect.midbottom
        self.z_layer: int = 1

        self.all_sprites: pygame.sprite.Group = groups[0] if isinstance(groups, (list, tuple)) else groups
        self.offset: pygame.Vector2 = self.all_sprites.offset

        # Sprite groups
        self.collision_sprites: pygame.sprite.Group = collision_sprites

        # AI & Pathfinding
        self.player: pygame.sprite.Sprite = player
        self.flag: pygame.sprite.Sprite = flag
        self.target: pygame.sprite.Sprite = player

        self.active: bool = False
        self.pathfinder: Pathfinder = pathfinder

        self.path: list[pygame.Vector2] = []
        self.direction: pygame.Vector2 = pygame.math.Vector2()
        self.speed: int = random.randint(200, 300)

        self.path_timer: int = pygame.time.get_ticks() + random.randint(0, 500)
        self.last_target_tile: tuple[int, int] | None = None

        self.flag_response_time: int | None = None
        self.flag_target_offset: pygame.Vector2 = pygame.Vector2(
            random.randint(-96, 96), random.randint(-96, 96)
        )

        # Health
        self.health: float = 100.0
        self.max_health: float = 100.0

        # Attacking
        self.damage: float = 10.0
        self.attack_range: int = 64

        # Rewards
        self.money_reward: int = 10
        self.score_reward: int = 50

    def update(self, dt: float) -> None:
        raise NotImplementedError ("update() must be implemented in subclasses.")

    def animate(self, dt: float) -> None:
        """Advances the current animation and applies the hit flash."""
        # Face the way we are walking, or towards the target while attacking
        if self.attack_anim_timer > 0:
            dx = self.target.rect.centerx - self.rect.centerx
        else:
            dx = self.direction.x
        if abs(dx) > 0.1:
            self.facing = "right" if dx > 0 else "left"

        if self.attack_anim_timer > 0:
            self.attack_anim_timer -= dt
            self.animation = "attack"
        else:
            self.animation = "idle"

        frames = self.frames[self.animation][self.facing]
        moving = self.active and self.direction.length() > 0
        speed = self.animation_speed * (1.6 if moving or self.animation == "attack" else 1.0)
        self.frame_index = (self.frame_index + speed * dt) % len(frames)
        image, flash, mask = frames[int(self.frame_index)]

        if self.flash_timer > 0:
            self.flash_timer -= dt
            image = image.copy()
            flash.set_alpha(int(230 * min(1.0, self.flash_timer / 0.1)))
            image.blit(flash, (0, 0))

        self.image = image
        self.mask = mask
        self.rect = self.image.get_frect(midbottom=self.hitbox.midbottom)

        # Health bar once damaged
        if self.health < self.max_health:
            self.image = self.image.copy() if self.flash_timer <= 0 else self.image
            self.draw_health_bar()

    def draw_health_bar(self) -> None:
        """Draws a small health bar on top of the sprite's image."""
        width = min(60, self.image.get_width() - 4)
        ratio = max(0.0, self.health / self.max_health)
        x = (self.image.get_width() - width) // 2
        pygame.draw.rect(self.image, (30, 30, 30), (x - 1, 0, width + 2, 7))
        pygame.draw.rect(self.image, (220, 50, 50), (x, 1, width, 5))
        pygame.draw.rect(self.image, (90, 230, 90), (x, 1, int(width * ratio), 5))

    def check_active(self) -> None:
        """
        Checks if the player is close enough to activate the enemy.
        Checks if flag is planted and activates the enemy sets target to flag.
        """
        distance = pygame.math.Vector2(self.rect.center).distance_to(
                    pygame.math.Vector2(self.target.rect.center))
        # Check if player is within activation range
        if distance < 500:
            self.alert()

        # Check if flag is planted
        if self.flag.is_planted:
            self.target = self.flag
            self.active = True

    def alert(self) -> None:
        """Activates the enemy, showing a "!" the first time it notices the player."""
        if not self.active:
            FX.text((self.rect.centerx, self.rect.top), "!", (255, 220, 60), 42, 0.6)
            Audio.play("alert", self.rect.center)
        self.active = True

    def pathfind(self) -> None:
        """Updates the path towards the target periodically."""
        current_time = pygame.time.get_ticks()
        if current_time < self.path_timer:
            return

        target_pos = pygame.math.Vector2(self.target.hitbox.center)

        if self.target is self.flag:
            target_pos += self.flag_target_offset

        target_tile = (int(target_pos.x // TILE_SIZE), int(target_pos.y // TILE_SIZE))

        if target_tile != self.last_target_tile:
            self.path = self.pathfinder.get_path(self.hitbox.center, target_pos)
            if self.path:
                self.path.pop(0)

            self.last_target_tile = target_tile

        self.path_timer = current_time + 700 + random.randint(0, 300)

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
        else:
            self.direction = pygame.math.Vector2()

    def collide(self, direction: str) -> None:
        """Handles collisions with obstacles."""
        for obstacle in self.collision_sprites.near(self.hitbox):
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
        self.flash_timer = 0.1
        FX.text((self.rect.centerx, self.rect.top + 10), str(int(round(amount))), (255, 255, 255), 28, 0.6)
        if self.health <= 0:
            return True
        return False

    def die(self) -> None:
        """Removes the enemy with a burst of particles."""
        center = self.rect.center
        FX.burst(center, [self.frames["color"], (255, 255, 255)], count=16, speed=(100, 320),
                 lifetime=(0.3, 0.7), size=(4, 8))
        FX.ring(center, 50, (255, 255, 255), 0.3, 5)
        FX.text((center[0], self.rect.top), f"+${self.money_reward}", (255, 215, 0), 30, 0.9)
        Audio.play("enemy_die", center)
        Audio.play("coin", center)
        self.kill()

    def distance_to_target(self) -> float:
        """Calculates the distance from the enemy to its target."""
        return pygame.math.Vector2(self.hitbox.center).distance_to(
            pygame.math.Vector2(self.target.hitbox.center)
        )

    def calculate_difficulty(self, round_number) -> None:
        """
        Scales difficulty based on round number.
        :param round_number: The current round number.
        """
        health_multiplier = 0.1 * (round_number - 1) * random.uniform(0.8, 1.2)  # +10% Each round
        self.health *= (1 + health_multiplier)
        self.max_health = self.health

        damage_multiplier = 0.2 * ((round_number - 1) ** 0.7) * random.uniform(0.8, 1.2)  # Diminishing scaling
        self.damage *= (1 + damage_multiplier)


class MeleeEnemy(BaseEnemy):
    """A stronger enemy that can deal damage to the player on contact."""
    monster_pool = MELEE_MONSTERS

    def __init__(self, position: tuple[float, float], groups: list[pygame.sprite.Group],
                 collision_sprites: pygame.sprite.Group, player: pygame.sprite.Sprite, flag: pygame.sprite.Sprite,
                 pathfinder: Pathfinder) -> None:
        super().__init__(position, groups, collision_sprites, player, flag, pathfinder)

        # Stats
        self.health = 100.0
        self.max_health = self.health
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
                self.direction = pygame.math.Vector2()
                self.attack()
        else:
            self.check_active()
        self.animate(dt)

    def attack(self) -> None:
        """Attacks the player if within range and cooldown is over."""
        current_time = pygame.time.get_ticks()
        if current_time - self.last_attack_time >= self.attack_cooldown:
            # Inflict damage to player
            self.target.take_damage(self.damage)
            self.last_attack_time = current_time
            self.attack_anim_timer = 0.4
            self.frame_index = 0

            # Impact effect between the enemy and its target
            impact = (pygame.math.Vector2(self.rect.center) + pygame.math.Vector2(self.target.rect.center)) / 2
            FX.burst(impact, [(255, 255, 255), (255, 120, 120)], count=6, speed=(80, 200),
                     lifetime=(0.15, 0.3), size=(3, 5))


class BruteEnemy(MeleeEnemy):
    """A big, slow and tanky melee enemy that hits hard. Appears from round 3."""
    monster_pool = BRUTE_MONSTERS

    def __init__(self, position: tuple[float, float], groups: list[pygame.sprite.Group],
                 collision_sprites: pygame.sprite.Group, player: pygame.sprite.Sprite, flag: pygame.sprite.Sprite,
                 pathfinder: Pathfinder) -> None:
        super().__init__(position, groups, collision_sprites, player, flag, pathfinder)

        # Stats
        self.health = 400.0
        self.max_health = self.health
        self.speed = random.randint(130, 160)
        self.attack_range = 80.0
        self.damage = 25.0
        self.attack_cooldown = 1400
        self.animation_speed = 4.0

        # Rewards
        self.money_reward = 40
        self.score_reward = 150

    def attack(self) -> None:
        """Heavy attack that also shakes the screen."""
        before = self.last_attack_time
        super().attack()
        if self.last_attack_time != before:
            FX.shake(10, 0.25)
            Audio.play("brute_slam", self.rect.center)
            FX.ring(self.hitbox.midbottom, 90, (230, 200, 160), 0.4, 6)


class RangedEnemy(BaseEnemy):
    """A stronger enemy that can deal damage to the player on contact."""
    monster_pool = RANGED_MONSTERS

    def __init__(self, position: tuple[float, float], groups: list[pygame.sprite.Group],
                 collision_sprites: pygame.sprite.Group, player: pygame.sprite.Sprite, flag: pygame.sprite.Sprite,
                 pathfinder: Pathfinder) -> None:
        super().__init__(position, groups, collision_sprites, player, flag, pathfinder)

        # Stats
        self.health = 80.0
        self.max_health = self.health
        self.speed = random.randint(160, 220)
        self.attack_range = 320.0
        self.damage = 15.0

        # Shooting
        self.shoot_cooldown = 1500.0 # milliseconds
        self.last_shot_time = 0.0
        self.projectile_color: tuple[int, int, int] = MONSTERS[self.monster]["projectile"]

    def update(self, dt: float) -> None:
        """Updates the enemy state, including AI and movement."""
        if self.active:
            if self.distance_to_target() > self.attack_range or not self.has_line_of_sight():
                self.pathfind()
                self.handle_movement(dt)
            else:
                self.direction = pygame.math.Vector2()
                self.shoot()
        else:
            self.check_active()
        self.animate(dt)

    def has_line_of_sight(self) -> bool:
        """Checks if the enemy has a clear line of sight to the player."""
        # Create a line from enemy to player
        start = (int(self.rect.centerx), int(self.rect.centery))
        end = (int(self.target.rect.centerx), int(self.target.rect.centery))
        area = pygame.Rect(min(start[0], end[0]), min(start[1], end[1]),
                           abs(start[0] - end[0]) + 1, abs(start[1] - end[1]) + 1)

        # Check for collision with obstacles along the line
        for obstacle in self.collision_sprites.near(area):
            if obstacle.hitbox.clipline(start, end):
                return False

        return True

    def shoot(self):
        """Creates and fires a bullet from the enemy's position towards the player."""
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot_time >= self.shoot_cooldown:
            target_pos = pygame.math.Vector2(self.target.rect.center)
            bullet_direction = target_pos - pygame.math.Vector2(self.rect.center)
            if bullet_direction.length() == 0:
                return
            bullet_direction = bullet_direction.normalize()

            Audio.play("enemy_shoot", self.rect.center)
            EnemyBullet(self.rect.center, bullet_direction,
                        (self.all_sprites,), self.collision_sprites, self.target, self)

            self.last_shot_time = pygame.time.get_ticks()
            self.attack_anim_timer = 0.4
            self.frame_index = 0


class EnemyBullet(pygame.sprite.Sprite):
    """Represents a projectile fired by a ranged enemy."""
    def __init__(self, position: tuple[float, float], direction: pygame.math.Vector2,
                 groups: list[pygame.sprite.Group], collision_sprites: pygame.sprite.Group,
                 target: pygame.sprite.Sprite, enemy: pygame.sprite.Sprite) -> None:
        super().__init__(groups)
        # Glowing orb in the colour of the monster's element (two frames for a pulse)
        self.color: tuple[int, int, int] = enemy.projectile_color
        self.frames: list[pygame.Surface] = AssetManager.cached(("orb", self.color), lambda: self.make_frames(self.color))
        self.image = self.frames[0]
        self.rect = self.image.get_frect(center=position)
        self.mask = pygame.mask.from_surface(self.frames[0])
        self.z_layer: int = 2
        self.age: float = 0.0
        self.trail_timer: float = 0.0

        # Sprite groups
        self.collision_sprites: pygame.sprite.Group = collision_sprites
        self.target: pygame.sprite.Sprite = target

        # Movement attributes
        self.direction: pygame.Vector2 = direction
        self.speed: float = 500.0

        # Damage
        self.damage: float = enemy.damage

    @staticmethod
    def make_frames(color: tuple[int, int, int]) -> list[pygame.Surface]:
        """Builds the pulsing orb images."""
        frames = []
        for glow in (12, 10):
            surf = pygame.Surface((24, 24), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*color, 90), (12, 12), glow)
            pygame.draw.circle(surf, color, (12, 12), 7)
            pygame.draw.circle(surf, (255, 255, 230), (12, 12), 3)
            frames.append(surf)
        return frames

    def update(self, dt: float) -> None:
        """Updates bullet"""
        self.age += dt
        self.image = self.frames[int(self.age * 12) % 2]
        self.move(dt)

        # Leave a small trail behind
        self.trail_timer -= dt
        if self.trail_timer <= 0:
            self.trail_timer = 0.03
            FX.burst(self.rect.center, [self.color], count=1, speed=(5, 20), lifetime=(0.15, 0.25), size=(3, 5))

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
               obstacle in self.collision_sprites.near(self.rect)):
            self.explode()

    def check_range(self) -> None:
        """Destroys the bullet if it travels beyond its maximum range."""
        target_pos = pygame.math.Vector2(self.target.rect.center)
        bullet_pos = pygame.math.Vector2(self.rect.center)
        if (target_pos - bullet_pos).length() > 500:
            self.kill()

    def check_hit_target(self):
        """Checks if the bullet has hit the target and destroys it."""
        if self.alive() and pygame.sprite.collide_mask(self, self.target):
            self.target.take_damage(self.damage)
            self.explode()

    def explode(self) -> None:
        """Small splash of particles on impact."""
        FX.burst(self.rect.center, [self.color, (255, 255, 255)], count=8, speed=(60, 180),
                 lifetime=(0.15, 0.35), size=(2, 5))
        self.kill()
