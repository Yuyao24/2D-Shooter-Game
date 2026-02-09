import random
import pygame
from settings import TILE_SIZE
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder
from pathfinding.core.diagonal_movement import DiagonalMovement

class GroundTile(pygame.sprite.Sprite):
    def __init__(self, position: tuple[int, int], surf: pygame.Surface, groups) -> None:
        super().__init__(groups)
        self.image: pygame.Surface = surf
        self.rect: pygame.FRect = surf.get_frect(topleft=position)
        self.z_layer: int = 0

class SmallSprite(pygame.sprite.Sprite):
    def __init__(self, position: tuple[int, int], surf: pygame.Surface, groups) -> None:
        super().__init__(groups)
        self.image: pygame.Surface = surf
        self.rect: pygame.FRect = surf.get_frect(topleft=position)
        self.hitbox: pygame.Rect = self.rect.inflate(0, -30)
        self.hitbox.midbottom = self.rect.midbottom
        self.z_layer: int = 1

class TallSprite(pygame.sprite.Sprite):
    def __init__(self, position: tuple[int, int], surf: pygame.Surface, groups) -> None:
        super().__init__(groups)
        self.image: pygame.Surface = surf
        self.rect: pygame.FRect = surf.get_frect(topleft=position)
        self.hitbox: pygame.Rect = pygame.Rect((0, 0), (70, 55))
        self.hitbox.midbottom = self.rect.midbottom
        self.z_layer: int = 1

class RectSprite(pygame.sprite.Sprite):
    def __init__(self, position: tuple[int, int], surf: pygame.Surface, groups) -> None:
        super().__init__(groups)
        self.image: pygame.Surface = surf
        self.rect: pygame.FRect = surf.get_frect(topleft=position)
        self.hitbox: pygame.Rect = self.rect
        self.z_layer: int = -1  # Invisible, underneath everything

class Pathfinder:
    def __init__(self, width: int, height: int, collision_sprites: pygame.sprite.Group) -> None:
        # Width and height of map in tiles
        self.width: int = width
        self.height: int = height
        self.collision_sprites: pygame.sprite.Group = collision_sprites
        # Create grid when instance is created
        self.grid: Grid = self.create_grid()
        self.finder: AStarFinder = AStarFinder(diagonal_movement=DiagonalMovement.only_when_no_obstacle)

    def create_grid(self) -> Grid:
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

    def get_path(self, start_pos: tuple[float, float] | pygame.Vector2, end_pos: tuple[float, float] | pygame.Vector2) -> list[pygame.Vector2]:
        start_x, start_y = int(start_pos[0] // TILE_SIZE), int(start_pos[1] // TILE_SIZE)
        end_x, end_y = int(end_pos[0] // TILE_SIZE), int(end_pos[1] // TILE_SIZE)

        # Check if the end tile is walkable
        end_node = self.grid.node(end_x, end_y)
        if not end_node.walkable:
            return []

        self.grid.cleanup()

        start_node = self.grid.node(start_x, start_y)

        path, _ = self.finder.find_path(start_node, end_node, self.grid)

        return [pygame.Vector2((node.x + 0.5) * TILE_SIZE, (node.y + 0.5) * TILE_SIZE) for node in path]




