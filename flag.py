import pygame
import math
from settings import AssetManager, COLOR_RED, COLOR_BLUE, make_silhouette
from stats_manager import StatsManager
from player import Player
from effects import FX
from sound import Audio


def make_waving_frames(image: pygame.Surface, count: int = 8, pole_width: int = 6,
                       amplitude: float = 2.5) -> list[pygame.Surface]:
    """
    Creates a waving animation from a single flag image by shifting each column
    of the cloth up and down along a sine wave (the pole stays still).

    :param image: The original (unscaled) flag image.
    :param count: Number of animation frames.
    :param pole_width: Width in pixels of the pole on the left that should not move.
    :param amplitude: Maximum vertical offset of the cloth in pixels.
    """
    width, height = image.get_size()
    frames = []
    for i in range(count):
        phase = 2 * math.pi * i / count
        frame = pygame.Surface((width, height + int(amplitude * 2) + 2), pygame.SRCALPHA)
        frame.blit(image.subsurface((0, 0, pole_width, height)), (0, int(amplitude) + 1))
        for x in range(pole_width, width):
            strength = (x - pole_width) / (width - pole_width)  # Free end waves the most
            dy = math.sin(phase - x * 0.22) * amplitude * strength
            frame.blit(image.subsurface((x, 0, 1, height)), (x, int(round(amplitude + 1 + dy))))
        frames.append(frame)
    return frames


class Flag(pygame.sprite.Sprite):
    """
    Represents a capture point flag with planting and defense mechanics.
    Contains both flag site and planted flag.
    """
    def __init__(self, position: tuple[float, float],
                 groups: pygame.sprite.AbstractGroup, player: Player, stats_manager: StatsManager) -> None:
        super().__init__(groups)
        # Unplanted image - Unrendered Surface
        self.radius: int = 150
        self.unplanted_image: pygame.Surface = (pygame.Surface(
                                (self.radius * 2, self.radius * 2), pygame.SRCALPHA))
        self.unplanted_rect: pygame.Rect = self.unplanted_image.get_frect(center=position)

        # Planted flag animation (generated once and cached)
        def build_frames():
            frames = make_waving_frames(AssetManager.get_image("assets/images/flag.png"))
            frames = [pygame.transform.scale_by(f, 3) for f in frames]
            return [(f, make_silhouette(f, (255, 80, 80))) for f in frames]
        self.flag_frames: list[tuple[pygame.Surface, pygame.Surface]] = AssetManager.cached(("flag_frames",), build_frames)
        self.planted_image: pygame.Surface = self.flag_frames[0][0]
        self.frame_index: float = 0.0
        self.hit_timer: float = 0.0
        self.rise_timer: float = 0.0  # Flag rises out of the ground when planted
        self.site_icon: pygame.Surface = pygame.transform.scale_by(AssetManager.get_image("assets/images/flag.png"), 1.5)
        self.site_icon.set_alpha(150)

        # Position
        self.position: pygame.Vector2 = pygame.Vector2(position)
        self.hitbox: pygame.Rect | None = None

        # Start unplanted
        self.image = self.unplanted_image
        self.rect = self.unplanted_rect.copy()
        self.z_layer: int = 0  # Site is drawn on the ground, the planted flag is Y-sorted

        # Planting mechanics
        self.is_planted: bool = False
        self.plant_progress: float = 0.0
        self.plant_time_required: float = 5.0

        # Defense mechanics
        self.timer: float = 60.0
        self.max_timer: float = 120.0
        self.damage_per_hit: float = 2.0

        # Outcome
        self.outcome: str | None = None  # "DEFENDED" or "DESTROYED"

        # References
        self.player: Player = player
        self.stats_manager: StatsManager = stats_manager

    def update(self, dt: float) -> None:
        """Updates flag state."""
        if not self.is_planted:
            self.update_planting(dt)
            self.draw_site_radius()
        else:
            self.update_defense(dt)
            self.animate(dt)

    def animate(self, dt: float) -> None:
        """Waves the planted flag and flashes it red when it is hit."""
        self.frame_index = (self.frame_index + 10 * dt) % len(self.flag_frames)
        image, hit_image = self.flag_frames[int(self.frame_index)]

        if self.hit_timer > 0:
            self.hit_timer -= dt
            image = image.copy()
            hit_image.set_alpha(int(200 * min(1.0, self.hit_timer / 0.12)))
            image.blit(hit_image, (0, 0))

        # Rise out of the ground right after planting
        if self.rise_timer > 0:
            self.rise_timer = max(0.0, self.rise_timer - dt)
            visible = int(image.get_height() * (1 - (self.rise_timer / 0.35) ** 2))
            image = image.subsurface((0, 0, image.get_width(), max(1, visible)))

        self.image = image
        self.rect = self.image.get_frect(midbottom=self.position)

    def update_planting(self, dt: float) -> None:
        """Handles planting with circular arc progress visualization."""

        distance_to_player = self.position.distance_to(self.player.rect.midbottom)

        # Check if player is in radius
        if distance_to_player <= self.radius:
            # Tick once per second while planting
            if int(self.plant_progress + dt) > int(self.plant_progress) or self.plant_progress == 0:
                Audio.play("tick")
            self.plant_progress += dt  # Increase planting progress
            if self.plant_progress >= self.plant_time_required:
                self.plant_flag()
        else:
            self.plant_progress = 0.0  # Reset progress if player leaves

    def draw_site_radius(self) -> None:
        """Draws the flag site: a pulsing zone with a blue arc showing planting progress."""
        self.unplanted_image.fill((0, 0, 0, 0))
        center = (self.unplanted_image.get_width() // 2, self.unplanted_image.get_height() // 2)

        # Pulsing translucent zone
        pulse = (math.sin(pygame.time.get_ticks() / 300) + 1) / 2
        pygame.draw.circle(self.unplanted_image, (237, 28, 36, int(30 + 30 * pulse)), center, self.radius)

        # Faded flag icon in the middle
        self.unplanted_image.blit(self.site_icon, self.site_icon.get_rect(center=center))

        # Define bounding box for arc
        arc_rect = (center[0] - self.radius, center[1] - self.radius,
                    self.radius * 2, self.radius * 2)

        # Draw red circle
        pygame.draw.arc(self.unplanted_image, COLOR_RED, arc_rect,
                        0, 6.5, 4)  # 6.5 radians > 2 pi

        # Calculate progress
        progress = self.plant_progress / self.plant_time_required

        # Draw blue arc on top for progress
        if progress > 0:
            start_angle = 90
            end_angle = start_angle - (360 * progress)

            pygame.draw.arc(self.unplanted_image, COLOR_BLUE, arc_rect,
                            math.radians(end_angle), math.radians(start_angle), 8)

    def plant_flag(self) -> None:
        """Transitions to planted state with flag centered on site."""
        self.is_planted = True
        self.player.update_money(300)
        self.stats_manager.update_flags()
        self.stats_manager.update_score(500)
        self.image = self.planted_image
        self.rect = self.image.get_frect(midbottom=self.position)
        self.hitbox = self.rect.inflate(-29, -26)
        self.hitbox.midbottom = self.position
        self.mask = pygame.mask.from_surface(self.planted_image)
        self.z_layer = 1
        self.rise_timer = 0.35

        # Celebration effects
        Audio.play("flag_planted")
        FX.ring(self.position, self.radius, (0, 162, 232), 0.5, 6)
        FX.burst(self.position, [(0, 162, 232), (255, 255, 255), (255, 215, 0)], count=30,
                 speed=(150, 400), lifetime=(0.4, 0.9), size=(4, 8))
        FX.text((self.position.x, self.position.y - 200), "FLAG PLANTED!", (0, 162, 232), 48, 1.4)
        FX.text((self.position.x, self.position.y - 150), "+$300", (255, 215, 0), 34, 1.2)

    def update_defense(self, dt: float) -> None:
        """Handles defense mechanics."""
        if not self.outcome:
            self.timer -= dt # Increase timer
            if self.timer <= 0:
                self.outcome = "DEFENDED"
            if self.timer >= self.max_timer:
                self.outcome = "DESTROYED"

    def take_damage(self, amount: float) -> None:
        """Increases timer by self.damage_per_hit."""
        self.timer += self.damage_per_hit
        self.hit_timer = 0.12
        Audio.play("flag_hit", self.position)
        FX.text((self.position.x, self.position.y - 180), f"+{self.damage_per_hit:g}s", (255, 80, 80), 30, 0.7)
