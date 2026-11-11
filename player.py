import random
import pygame
from settings import AssetManager, make_silhouette
from effects import FX
from sound import Audio

# Rows of the player sprite sheet (4 x 4 frames of 128 x 128 pixels)
FACING_ROWS = {"down": 0, "left": 1, "right": 2, "up": 3}

class Player(pygame.sprite.Sprite):
    """Represents the player-controlled entity."""

    def __init__(self, position: tuple[int, int], groups: list[pygame.sprite.Group],
                 collision_sprites: pygame.sprite.Group) -> None:
        super().__init__(groups)
        # Animation frames: facing -> list of (image, hurt-flash image, mask)
        sheet = AssetManager.get_sheet("assets/images/player_sheet.png", 128, 128)
        self.animations: dict[str, list[tuple[pygame.Surface, pygame.Surface, pygame.Mask]]] = {
            facing: [(frame, make_silhouette(frame, (255, 70, 70)), pygame.mask.from_surface(frame))
                     for frame in sheet[row]]
            for facing, row in FACING_ROWS.items()
        }
        self.facing: str = "down"
        self.frame_index: float = 0.0
        self.animation_speed: float = 8.0  # Frames per second while walking
        self.dust_timer: float = 0.0
        self.hurt_timer: float = 0.0  # > 0 while the player flashes red after being hit
        self.time_since_hit: float = 0.0  # Health regenerates after a few seconds out of combat

        # Player image
        self.image: pygame.Surface = self.animations["down"][0][0]
        self.rect: pygame.FRect = self.image.get_frect(center=position)
        self.hitbox: pygame.Rect = self.rect.inflate(-60, -90)
        self.hitbox.midbottom = self.rect.midbottom
        self.mask: pygame.Mask = pygame.mask.from_surface(self.image)
        self.z_layer: int = 1

        # Movement attributes
        self.speed: int = 300
        self.direction: pygame.Vector2 = pygame.math.Vector2(0, 0)
        self.aim: pygame.Vector2 = pygame.math.Vector2(0, 1)  # Unit vector towards the mouse

        # Sprite groups
        self.collision_sprites: pygame.sprite.Group = collision_sprites
        # Assuming groups[0] is AllSprites which has the offset
        self.offset: pygame.Vector2 = groups[0].offset if isinstance(groups, (list, tuple)) else groups.offset

        # Gun
        self.gun: Gun = Gun(self, groups[0])  # groups[0] is AllSprites

        # Health
        self.health: float = 100.0
        self.max_health: float = 100.0
        self.lives: int = 5
        self.damage_mult: float = 1.0  # Damage reduction

        # Money
        self.money: int = 500
        self.money_mult: float = 1.0

        # Upgrade flags (toggles - only purchasable once)
        self.has_trinity: bool = False
        self.has_adrenaline: bool = False
        self.has_auto_shoot: bool = False
        self.adrenaline: bool = False

        # Upgrade stats
        self.life_steal: int = 0

    def update(self, dt: float) -> None:
        """Updates the player state once per frame."""
        self.update_aim()
        self.handle_movement(dt)
        self.regenerate(dt)
        self.animate(dt)

    REGEN_DELAY = 3.0  # Seconds without taking damage before health regenerates
    REGEN_RATE = 0.08  # Fraction of max health regenerated per second

    def regenerate(self, dt: float) -> None:
        """Slowly regenerates health when the player has not been hit for a while."""
        self.time_since_hit += dt
        if self.time_since_hit >= self.REGEN_DELAY and 0 < self.health < self.max_health:
            self.health = min(self.max_health, self.health + self.max_health * self.REGEN_RATE * dt)

    def update_aim(self) -> None:
        """Updates the aim direction (towards the mouse) and the facing direction."""
        mouse_pos = pygame.math.Vector2(pygame.mouse.get_pos()) + self.offset
        aim = mouse_pos - pygame.math.Vector2(self.rect.center)
        if aim.length() > 0:
            self.aim = aim.normalize()

        # Face the direction the player is aiming in
        if abs(self.aim.x) > abs(self.aim.y):
            self.facing = "right" if self.aim.x > 0 else "left"
        else:
            self.facing = "down" if self.aim.y > 0 else "up"

    def animate(self, dt: float) -> None:
        """Advances the walk animation and applies the hurt flash."""
        frames = self.animations[self.facing]
        if self.direction.length() > 0:
            speed_ratio = self.speed / 300
            self.frame_index = (self.frame_index + self.animation_speed * speed_ratio * dt) % len(frames)

            # Kick up some dust while walking
            self.dust_timer -= dt
            if self.dust_timer <= 0:
                FX.dust(self.hitbox.midbottom)
                Audio.play("step")
                self.dust_timer = 0.18
        else:
            self.frame_index = 0  # Standing still

        image, hurt_image, mask = frames[int(self.frame_index)]
        if self.hurt_timer > 0:
            self.hurt_timer -= dt
            image = image.copy()
            hurt_image.set_alpha(int(200 * min(1.0, self.hurt_timer / 0.15)))
            image.blit(hurt_image, (0, 0))
        self.image = image
        self.mask = mask

    def handle_movement(self, dt: float) -> None:
        """Handles player input and movement with collision detection."""
        keys = pygame.key.get_pressed() # Get keys pressed

        # Calculate direction
        self.direction.x = keys[pygame.K_d] - keys[pygame.K_a] # RIGHT - LEFT (Right is positive)
        self.direction.y = keys[pygame.K_s] - keys[pygame.K_w] # DOWN - UP (Down is positive)

        # Normalize velocity to prevent faster diagonal movement
        if self.direction.length() > 0:
            self.direction = self.direction.normalize()

        # Apply adrenaline speed boost when below 30% health
        current_speed = self.speed
        if self.adrenaline and self.health < self.max_health * 0.3:
            current_speed = self.speed * 1.25

        # Update position using delta time
        step = current_speed * dt
        self.hitbox.x += self.direction.x * step
        self.collide("horizontal", step)
        self.hitbox.y += self.direction.y * step
        self.collide("vertical", step)
        self.rect.midbottom = self.hitbox.midbottom

    CORNER_SLIDE = 16  # Max pixels the player is nudged around a corner they bump into

    def collide(self, direction: str, step: float = 0.0) -> None:
        """Handles collisions with obstacles, sliding the player around corners they barely touch."""
        for obstacle in self.collision_sprites.near(self.hitbox):
            box = obstacle.hitbox
            if not box.colliderect(self.hitbox):
                continue
            if direction == "horizontal":
                # Moving purely sideways into a corner: slide up/down around it
                if self.direction.y == 0 and self.slide_around(box, "y", step):
                    continue
                if self.direction.x > 0: self.hitbox.right = box.left
                if self.direction.x < 0: self.hitbox.left = box.right
            if direction == "vertical":
                # Moving purely up/down into a corner: slide left/right around it
                if self.direction.x == 0 and self.slide_around(box, "x", step):
                    continue
                if self.direction.y < 0: self.hitbox.top = box.bottom
                if self.direction.y > 0: self.hitbox.bottom = box.top

    def slide_around(self, box, axis: str, step: float) -> bool:
        """
        If the player only overlaps the edge of an obstacle by a few pixels, nudges them
        sideways (by at most one movement step) instead of stopping them.

        :return: True if the player was nudged and is now clear of the obstacle.
        """
        if axis == "x":
            overlaps = {-1: self.hitbox.right - box.left, 1: box.right - self.hitbox.left}
        else:
            overlaps = {-1: self.hitbox.bottom - box.top, 1: box.bottom - self.hitbox.top}
        side, overlap = min(overlaps.items(), key=lambda item: item[1])
        if overlap > self.CORNER_SLIDE:
            return False

        nudge = side * min(overlap, max(step, 0.5))
        moved = self.hitbox.move(nudge, 0) if axis == "x" else self.hitbox.move(0, nudge)
        # Undo the forward movement this frame; only nudge sideways (no clipping into other walls)
        if axis == "x":
            moved.y = box.bottom if self.direction.y < 0 else box.top - moved.height
        else:
            moved.x = box.right if self.direction.x < 0 else box.left - moved.width
        if any(o.hitbox.colliderect(moved) for o in self.collision_sprites.near(moved)):
            return False
        self.hitbox.update(moved)
        return True

    def shoot(self, all_sprites: pygame.sprite.Group, bullets: pygame.sprite.Group) -> None:
        """Fires the player's weapon."""
        self.gun.shoot(self, all_sprites, bullets, self.collision_sprites)

    def take_damage(self, amount: float) -> None:
        """Reduces the player's health by the given amount, applying damage reduction."""
        # Apply damage reduction from upgrades
        damage = amount * self.damage_mult
        self.health -= damage
        self.time_since_hit = 0.0

        # Feedback: red flash, screen shake and a damage number
        self.hurt_timer = 0.15
        Audio.play("hurt")
        FX.shake(6, 0.15)
        FX.text((self.rect.centerx, self.rect.top + 20), f"-{int(round(damage))}", (255, 80, 80), 30)

    def reset(self, new_position: tuple[float, float]) -> None:
        """
        Resets player for new round while keeping persistent stats.
        :param new_position: The new position of the player.
        """
        # Reset position
        self.rect.center = new_position
        self.hitbox.midbottom = self.rect.midbottom
        self.direction = pygame.math.Vector2(0, 0)
        self.hurt_timer = 0.0

        # Reset health to max (upgrades might have increased max_health)
        self.health = self.max_health

        # Reset gun
        self.gun.ammo = self.gun.max_ammo
        self.gun.is_reloading = False

    def update_money(self, amount: int) -> None:
        """Adds or subtracts money from the player's account."""
        if amount > 0:
            amount = int(amount * self.money_mult)  # Apply money multiplier for positive amounts
        self.money += amount

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
        self.z_layer: int = 1
        self.sort_y: float | None = None  # Drawn just in front of / behind the player
        self.recoil: float = 0.0  # Pixels the gun is pushed back after firing

        # Gun stats
        self.damage: float = 25.0
        self.fire_rate: float = 0.2 # seconds between shots
        self.range: float = 600.0
        self.bullet_speed: float = 1000.0

        # Ammo
        self.ammo: int = 30
        self.max_ammo: int = 30
        self.ammo_saver_chance: float = 0.0

        # Cooldown timer
        self.last_shot_time: int = 0

        # Reloading
        self.is_reloading: bool = False
        self.reload_start_time: int = 0
        self.reload_time: int = 2500
        self.insta_reload_chance: float = 0.0

        # Special effects
        self.piercing: int = 0
        self.insta_kill_chance: float = 0.0
        self.area_damage: float = 0.0
        self.trinity: bool = False
        self.auto_shoot: bool = False

    def update(self, dt: float) -> None:
        """Updates the gun's position and rotation based on where the player is aiming."""

        self.update_reload()

        direction = self.player.aim

        base_image = self.base_image
        aiming_left = direction.x < 0
        if aiming_left: # Flipped image if aiming left
            base_image = self.base_image_flipped

        rotation = direction.angle_to(pygame.math.Vector2(1, 0)) # Rotate gun to aim direction
        if aiming_left: # Flip rotation if aiming left
            rotation += 180

        # Recoil pushes the gun back towards the player and recovers quickly
        self.recoil = max(0.0, self.recoil - 120 * dt)

        # Reloading: spin the gun once
        if self.is_reloading:
            progress = (pygame.time.get_ticks() - self.reload_start_time) / self.reload_time
            rotation += 360 * min(1.0, progress) * (1 if aiming_left else -1)

        self.image = pygame.transform.rotate(base_image, rotation)
        hand_pos = pygame.math.Vector2(self.player.rect.center) + (0, 14) + direction * (16 - self.recoil)
        self.rect = self.image.get_frect(center=hand_pos) # Update rect position

        # Draw the gun behind the player when aiming upwards, otherwise in front
        self.sort_y = self.player.rect.bottom + (-1 if direction.y < -0.4 else 1)

    def shoot(self, player: Player, all_sprites: pygame.sprite.AbstractGroup,
              bullets: pygame.sprite.Group, collision_sprites: pygame.sprite.Group) -> None:
        """Creates a bullet if the gun is not on cooldown."""

        if not self.check_cooldown():
            return

        if self.is_reloading:
            return

        # Calculate bullet direction
        mouse_pos = pygame.math.Vector2(pygame.mouse.get_pos()) + all_sprites.offset
        direction = mouse_pos - pygame.math.Vector2(player.rect.center)

        if direction.length() > 0:
            direction = direction.normalize()
        else: # Default to up if no direction
            direction = pygame.math.Vector2(0, -1)

        position = player.rect.center + direction * 64

        Bullet(position, direction, (all_sprites, bullets), collision_sprites, player)

        # Visual feedback
        self.recoil = 10.0
        Audio.play("shoot")
        FX.muzzle(pygame.math.Vector2(player.rect.center) + (0, 14) + direction * 58,
                  direction.angle_to(pygame.math.Vector2(1, 0)))
        FX.shake(2, 0.05)

        # Apply ammo saver chance - randomly don't consume ammo
        if random.random() > self.ammo_saver_chance:
            self.ammo -= 1

        if self.ammo <= 0:
            # Check for instant reload chance
            if random.random() < self.insta_reload_chance:
                self.ammo = self.max_ammo
                return
            self.reload()

    def check_cooldown(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot_time < self.fire_rate * 1000:
            return False
        self.last_shot_time = current_time
        return True

    def reload(self):
        """Begin a reload that completes after reload_time_ms."""
        if self.is_reloading or self.ammo == self.max_ammo:
            return

        self.is_reloading = True
        self.reload_start_time = pygame.time.get_ticks()
        Audio.play("reload")

    def update_reload(self):
        """Completes reload when the timer finishes."""
        if not self.is_reloading:
            return

        current_time = pygame.time.get_ticks()
        if current_time - self.reload_start_time >= self.reload_time:
            self.ammo = self.max_ammo
            self.is_reloading = False
            Audio.play("reload_done")

class Bullet(pygame.sprite.Sprite):
    """Represents a projectile fired by a gun."""
    def __init__(self, position: tuple[float, float], direction: pygame.math.Vector2, 
                 groups: pygame.sprite.AbstractGroup | list[pygame.sprite.AbstractGroup], 
                 collision_sprites: pygame.sprite.Group, player: Player) -> None:
        super().__init__(groups)
        # Bullet image
        self.image: pygame.Surface = pygame.transform.scale(AssetManager.get_image("assets/images/bullet.png"), (32, 32))

        rotation = direction.angle_to(pygame.math.Vector2(1, 0)) # Rotate bullet
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

        # Upgrade stats
        self.piercing: int = player.gun.piercing
        self.insta_kill_chance: float = player.gun.insta_kill_chance
        self.area_damage: float = player.gun.area_damage
        self.trinity: bool = player.gun.trinity
        self.enemies_hit: set = set()  # Track enemies already hit for piercing
        self.has_exploded: bool = False

        # Trinity tracking - last 3 shots in magazine are one-shot kills
        self.is_trinity_shot: bool = (
                self.trinity and
                3 >= player.gun.ammo > 0
        )

    def update(self, dt: float) -> None:
        """Updates bullet."""
        self.move(dt)
        self.check_collision()
        self.check_range()

    def move(self, dt: float) -> None:
        """Moves the bullet according to its direction and speed."""
        self.rect.x += self.direction.x * self.speed * dt
        self.rect.y += self.direction.y * self.speed * dt

    def check_collision(self) -> None:
        """Checks for collisions with obstacles and destroys the bullet on impact."""
        # Small box around the bullet's tip: the sprite's rect is much bigger than the visible bullet
        tip = pygame.FRect(0, 0, 12, 12)
        tip.center = self.rect.center
        if any(obstacle.hitbox.colliderect(tip) for obstacle in self.collision_sprites.near(tip)):
            FX.burst(self.rect.center, [(255, 230, 140), (255, 180, 60), (200, 200, 200)], count=6,
                     speed=(60, 200), lifetime=(0.12, 0.3), size=(2, 4), direction=-self.direction, spread=140)
            self.kill()
    
    def check_range(self) -> None:
        """Destroys the bullet if it travels beyond its maximum range."""
        player_pos = pygame.math.Vector2(self.player.rect.center)
        bullet_pos = pygame.math.Vector2(self.rect.center)

        if (player_pos - bullet_pos).length() > self.range:
            self.kill()
