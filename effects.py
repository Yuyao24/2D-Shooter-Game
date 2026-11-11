import math
import random
import pygame
from settings import get_font


class Particle(pygame.sprite.Sprite):
    """A small square pixel that flies outwards, slows down and fades away."""
    def __init__(self, position, velocity, color, size: int, lifetime: float,
                 groups, gravity: float = 0.0, z_layer: int = 2) -> None:
        super().__init__(groups)
        self.image: pygame.Surface = pygame.Surface((size, size))
        self.image.fill(color)
        self.rect: pygame.FRect = self.image.get_frect(center=position)
        self.z_layer: int = z_layer

        self.position: pygame.Vector2 = pygame.Vector2(position)
        self.velocity: pygame.Vector2 = pygame.Vector2(velocity)
        self.gravity: float = gravity
        self.lifetime: float = lifetime
        self.age: float = 0.0

    def update(self, dt: float) -> None:
        self.age += dt
        if self.age >= self.lifetime:
            self.kill()
            return
        self.velocity *= max(0.0, 1 - 4 * dt)  # Drag
        self.velocity.y += self.gravity * dt
        self.position += self.velocity * dt
        self.rect.center = self.position
        self.image.set_alpha(int(255 * (1 - self.age / self.lifetime)))


class FloatingText(pygame.sprite.Sprite):
    """Text (damage numbers, rewards) that pops up, floats upwards and fades out."""
    def __init__(self, position, text: str, color, size: int, groups, lifetime: float = 0.8) -> None:
        super().__init__(groups)
        font = get_font(size)

        # Text with a dark outline so it is readable on any background
        label = font.render(text, True, color)
        outline = font.render(text, True, (20, 20, 20))
        self.base_image = pygame.Surface((label.get_width() + 4, label.get_height() + 4), pygame.SRCALPHA)
        for dx, dy in ((0, 2), (4, 2), (2, 0), (2, 4)):
            self.base_image.blit(outline, (dx, dy))
        self.base_image.blit(label, (2, 2))

        self.image: pygame.Surface = self.base_image
        self.position: pygame.Vector2 = pygame.Vector2(position) + (random.uniform(-12, 12), 0)
        self.rect: pygame.FRect = self.image.get_frect(center=self.position)
        self.z_layer: int = 3
        self.lifetime: float = lifetime
        self.age: float = 0.0

    def update(self, dt: float) -> None:
        self.age += dt
        if self.age >= self.lifetime:
            self.kill()
            return
        progress = self.age / self.lifetime
        self.position.y -= 70 * dt
        # Pop in quickly, then fade out
        scale = 1.4 - 0.4 * min(1.0, progress * 6)
        self.image = pygame.transform.scale_by(self.base_image, scale)
        self.image.set_alpha(int(255 * min(1.0, 2 * (1 - progress))))
        self.rect = self.image.get_frect(center=self.position)


class MuzzleFlash(pygame.sprite.Sprite):
    """A short bright flash at the end of the gun barrel."""
    def __init__(self, position, angle: float, groups) -> None:
        super().__init__(groups)
        base = pygame.Surface((40, 28), pygame.SRCALPHA)
        pygame.draw.polygon(base, (255, 200, 60), [(0, 8), (26, 0), (40, 14), (26, 28), (0, 20)])
        pygame.draw.polygon(base, (255, 250, 210), [(4, 11), (24, 6), (32, 14), (24, 22), (4, 17)])
        self.image: pygame.Surface = pygame.transform.rotate(base, angle)
        self.rect: pygame.FRect = self.image.get_frect(center=position)
        self.z_layer: int = 3
        self.lifetime: float = 0.05

    def update(self, dt: float) -> None:
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.kill()


class Ring(pygame.sprite.Sprite):
    """An expanding, fading circle (explosions, death poofs, flag planting)."""
    def __init__(self, position, max_radius: float, color, groups,
                 lifetime: float = 0.35, width: int = 4, z_layer: int = 2) -> None:
        super().__init__(groups)
        self.position = pygame.Vector2(position)
        self.max_radius = max_radius
        self.color = color
        self.width = width
        self.lifetime = lifetime
        self.age = 0.0
        self.z_layer = z_layer
        self.image = pygame.Surface((1, 1), pygame.SRCALPHA)
        self.rect = self.image.get_frect(center=position)
        self.update(0)

    def update(self, dt: float) -> None:
        self.age += dt
        if self.age >= self.lifetime:
            self.kill()
            return
        progress = self.age / self.lifetime
        radius = max(2, int(self.max_radius * (1 - (1 - progress) ** 3)))  # Ease-out
        self.image = pygame.Surface((radius * 2 + 2, radius * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, self.color, (radius + 1, radius + 1), radius,
                           max(1, int(self.width * (1 - progress)) + 1))
        self.image.set_alpha(int(255 * (1 - progress)))
        self.rect = self.image.get_frect(center=self.position)


class FX:
    """
    Global access point for spawning visual effects.
    Call FX.setup() once the camera sprite group exists.
    """
    camera = None        # AllSprites group (for drawing + screen shake)
    group = None         # Group holding only effects (so they can be cleared)

    @classmethod
    def setup(cls, camera: pygame.sprite.Group, group: pygame.sprite.Group) -> None:
        cls.camera = camera
        cls.group = group

    @classmethod
    def _groups(cls):
        return (cls.camera, cls.group)

    @classmethod
    def ready(cls) -> bool:
        return cls.camera is not None

    @classmethod
    def clear(cls) -> None:
        if cls.group is not None:
            for sprite in list(cls.group):
                sprite.kill()

    @classmethod
    def shake(cls, strength: float, duration: float = 0.2) -> None:
        if cls.ready():
            cls.camera.add_shake(strength, duration)

    @classmethod
    def burst(cls, position, colors, count: int = 10, speed: tuple = (80, 280),
              lifetime: tuple = (0.25, 0.6), size: tuple = (3, 7), gravity: float = 0.0,
              direction: pygame.Vector2 | None = None, spread: float = 360) -> None:
        """Spawns a burst of particles, optionally in a cone around a direction."""
        if not cls.ready():
            return
        if isinstance(colors[0], int):
            colors = [colors]
        base_angle = 0 if direction is None else math.degrees(math.atan2(direction.y, direction.x))
        for _ in range(count):
            angle = math.radians(base_angle + random.uniform(-spread / 2, spread / 2))
            velocity = pygame.Vector2(math.cos(angle), math.sin(angle)) * random.uniform(*speed)
            Particle(position, velocity, random.choice(colors), random.randint(*size),
                     random.uniform(*lifetime), cls._groups(), gravity)

    @classmethod
    def text(cls, position, text: str, color=(255, 255, 255), size: int = 30, lifetime: float = 0.8) -> None:
        if cls.ready():
            FloatingText(position, text, color, size, cls._groups(), lifetime)

    @classmethod
    def muzzle(cls, position, angle: float) -> None:
        if cls.ready():
            MuzzleFlash(position, angle, cls._groups())

    @classmethod
    def ring(cls, position, radius: float, color=(255, 255, 255), lifetime: float = 0.35, width: int = 4) -> None:
        if cls.ready():
            Ring(position, radius, color, cls._groups(), lifetime, width)

    @classmethod
    def dust(cls, position) -> None:
        """Small puff of dust at the feet of a walking character."""
        if cls.ready():
            for _ in range(2):
                velocity = pygame.Vector2(random.uniform(-40, 40), random.uniform(-50, -10))
                Particle(position, velocity, random.choice([(222, 214, 170), (200, 190, 150)]),
                         random.randint(3, 5), random.uniform(0.25, 0.4), cls._groups(), z_layer=1)
