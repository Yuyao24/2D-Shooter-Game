import random
import pygame
from settings import TILE_SIZE
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder
from pathfinding.core.diagonal_movement import DiagonalMovement

class GroundTile(pygame.sprite.Sprite):
    """Represents a basic ground tile on the map."""
    def __init__(self, position: tuple[int, int], surf: pygame.Surface, groups: pygame.sprite.AbstractGroup | list[pygame.sprite.AbstractGroup]) -> None:
        super().__init__(groups)
        self.image: pygame.Surface = surf
        self.rect: pygame.FRect = surf.get_frect(topleft=position)
        self.z_layer: int = 0

class SmallSprite(pygame.sprite.Sprite):
    """Represents a small static object with a collision hitbox (e.g., rocks)."""
    def __init__(self, position: tuple[int, int], surf: pygame.Surface, groups: pygame.sprite.AbstractGroup | list[pygame.sprite.AbstractGroup]) -> None:
        super().__init__(groups)
        self.image: pygame.Surface = surf
        self.rect: pygame.FRect = surf.get_frect(topleft=position)
        self.hitbox: pygame.Rect = self.rect.inflate(0, -30)
        self.hitbox.midbottom = self.rect.midbottom
        self.z_layer: int = 1

class TallSprite(pygame.sprite.Sprite):
    """Represents a tall static object with a collision hitbox (e.g., trees)."""
    def __init__(self, position: tuple[int, int], surf: pygame.Surface, groups: pygame.sprite.AbstractGroup | list[pygame.sprite.AbstractGroup]) -> None:
        super().__init__(groups)
        self.image: pygame.Surface = surf
        self.rect: pygame.FRect = surf.get_frect(topleft=position)
        self.hitbox: pygame.Rect = pygame.Rect((0, 0), (70, 55))
        self.hitbox.midbottom = self.rect.midbottom
        self.z_layer: int = 1

class RectSprite(pygame.sprite.Sprite):
    """Represents an invisible collision area."""
    def __init__(self, position: tuple[int, int], surf: pygame.Surface, groups: pygame.sprite.AbstractGroup | list[pygame.sprite.AbstractGroup]) -> None:
        super().__init__(groups)
        self.image: pygame.Surface = surf
        self.rect: pygame.FRect = surf.get_frect(topleft=position)
        self.hitbox: pygame.Rect = self.rect
        self.z_layer: int = -1  # Invisible, underneath everything

class Pathfinder:
    """Handles A* pathfinding for entities."""
    def __init__(self, width: int, height: int, collision_sprites: pygame.sprite.Group) -> None:
        # Width and height of map in tiles
        self.width: int = width
        self.height: int = height
        self.collision_sprites: pygame.sprite.Group = collision_sprites
        # Create grid when instance is created
        self.grid: Grid = self.create_grid()
        self.finder: AStarFinder = AStarFinder(diagonal_movement=DiagonalMovement.only_when_no_obstacle)

    def create_grid(self) -> Grid:
        """Creates a pathfinding grid where obstacles are marked as unwalkable."""
        # Create a matrix representing walkable (1) and unwalkable (0) tiles
        matrix: list[list[int]] = [[1 for _ in range(self.width)] for _ in range(self.height)]
        for sprite in self.collision_sprites:
            # Calculate which tiles the sprite overlaps
            # clamp within bounds
            left = max(0, int(sprite.hitbox.left // TILE_SIZE))
            right = min(self.width - 1, int((sprite.hitbox.right - 0.1) // TILE_SIZE))
            top = max(0, int(sprite.hitbox.top // TILE_SIZE))
            bottom = min(self.height - 1, int((sprite.hitbox.bottom - 0.1) // TILE_SIZE))

            # Set tile to unwalkable
            for y in range(top, bottom + 1):
                for x in range(left, right + 1):
                    matrix[y][x] = 0

        return Grid(matrix=matrix)

    def get_path(self, start_pos: tuple[float, float] | pygame.Vector2,
                 end_pos: tuple[float, float] | pygame.Vector2) -> list[pygame.Vector2]:
        """
        Calculates a path between two world positions.
        
        :param start_pos: The starting position in world coordinates.
        :param end_pos: The target position in world coordinates.
        :return: A list of pygame.Vector2 nodes representing the path.
        """
        start_x, start_y = int(start_pos[0] // TILE_SIZE), int(start_pos[1] // TILE_SIZE)
        end_x, end_y = int(end_pos[0] // TILE_SIZE), int(end_pos[1] // TILE_SIZE)

        # Check if the end tile is walkable
        try:
            end_node = self.grid.node(end_x, end_y)
        except IndexError:
            return []

        if not end_node.walkable:
            return []

        self.grid.cleanup()

        try:
            start_node = self.grid.node(start_x, start_y)
        except IndexError:
            return []

        path, _ = self.finder.find_path(start_node, end_node, self.grid)

        return [pygame.Vector2((node.x + 0.5) * TILE_SIZE, (node.y + 0.5) * TILE_SIZE) for node in path]




