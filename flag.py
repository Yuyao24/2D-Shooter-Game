import pygame
import math
from settings import AssetManager, COLOR_RED, COLOR_BLUE
from stats_manager import StatsManager
from player import Player


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

        # Planted flag image
        self.planted_image: pygame.Surface = AssetManager.get_image("assets/images/flag.png")
        self.planted_image: pygame.Surface = pygame.transform.scale(self.planted_image, (183, 174))

        # Position
        self.position: pygame.Vector2 = pygame.Vector2(position)
        self.hitbox: pygame.Rect | None = None

        # Start unplanted
        self.image = self.unplanted_image
        self.rect = self.unplanted_rect.copy()
        self.z_layer: int = 1

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

    def update_planting(self, dt: float) -> None:
        """Handles planting with circular arc progress visualization."""

        distance_to_player = self.position.distance_to(self.player.rect.midbottom)

        # Check if player is in radius
        if distance_to_player <= self.radius:
            self.plant_progress += dt  # Increase planting progress
            if self.plant_progress >= self.plant_time_required:
                self.plant_flag()
        else:
            self.plant_progress = 0.0  # Reset progress if player leaves

    def draw_site_radius(self) -> None:
        """Draws red outline circle with blue arc filling around based on progress."""
        center_x = self.unplanted_image.get_width() // 2
        center_y = self.unplanted_image.get_height() // 2

        # Define bounding box for arc
        arc_rect = (center_x - self.radius, center_y - self.radius,
                    self.radius * 2, self.radius * 2)

        # Draw red circle
        pygame.draw.arc(self.unplanted_image, COLOR_RED, arc_rect,
                        0, 6.5, 3)  # 6.5 radians > 2 pi

        # Calculate progress
        progress = self.plant_progress / self.plant_time_required

        # Draw blue arc on top for progress
        if progress > 0:
            start_angle = 90
            end_angle = start_angle - (360 * progress)

            pygame.draw.arc(self.unplanted_image, COLOR_BLUE, arc_rect,
                            math.radians(end_angle), math.radians(start_angle), 3)

    def plant_flag(self) -> None:
        """Transitions to planted state with flag centered on site."""
        self.is_planted = True
        self.stats_manager.update_flags()
        self.stats_manager.update_score(500)
        self.image = self.planted_image
        self.rect = self.image.get_frect(midbottom=self.position)
        self.hitbox = self.rect.inflate(-29, -26)
        self.hitbox.midbottom = self.position

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