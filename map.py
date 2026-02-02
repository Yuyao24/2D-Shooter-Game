import random
from settings import *
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder
from pathfinding.core.diagonal_movement import DiagonalMovement

class GroundTile(pygame.sprite.Sprite):
    def __init__(self, position: tuple[int, int], surf, groups) -> None:
        super().__init__(groups)
        self.image = surf
        self.rect = surf.get_frect(topleft=position)
        self.z_layer = 0

class SmallSprite(pygame.sprite.Sprite):
    def __init__(self, position: tuple[int, int], surf, groups) -> None:
        super().__init__(groups)
        self.image = surf
        self.rect = surf.get_frect(topleft=position)
        self.hitbox = self.rect.inflate(0, -30)
        self.hitbox.midbottom = self.rect.midbottom
        self.z_layer = 1

class TallSprite(pygame.sprite.Sprite):
    def __init__(self, position: tuple[int, int], surf, groups) -> None:
        super().__init__(groups)
        self.image = surf
        self.rect = surf.get_frect(topleft=position)
        self.hitbox = pygame.Rect((0, 0), (70, 55))
        self.hitbox.midbottom = self.rect.midbottom
        self.z_layer = 1

class RectSprite(pygame.sprite.Sprite):
    def __init__(self, position: tuple[int, int], surf, groups) -> None:
        super().__init__(groups)
        self.image = surf
        self.rect = surf.get_frect(topleft=position)
        self.hitbox = self.rect
        self.z_layer = -1 # Invisible, underneath everything

class Pathfinder:
    def __init__(self, width, height, collision_sprites) -> None:
        self.width = width
        self.height = height
        self.collision_sprites = collision_sprites
        self.grid = self.create_grid() # Create grid when instance is created
        self.finder = AStarFinder(diagonal_movement=DiagonalMovement.only_when_no_obstacle)

    def create_grid(self) -> Grid:
        # Create a matrix representing walkable (1) and unwalkable (0) tiles
        matrix = [[1 for _ in range(self.width)] for _ in range(self.height)]
        for sprite in self.collision_sprites:
            # Calculate which tiles the sprite overlaps
            # max and min are used to ensure the tile isn't out of bounds
            left = max(0, int(sprite.hitbox.left // TILE_SIZE))
            right = min(self.width - 1, int((sprite.hitbox.right - 0.1) // TILE_SIZE))
            top = max(0, int(sprite.hitbox.top // TILE_SIZE))
            bottom = min(self.height - 1, int((sprite.hitbox.bottom - 0.1) // TILE_SIZE))

            # Set tile to unwalkable
            for y in range(top, bottom + 1):
                for x in range(left, right + 1):
                    matrix[y][x] = 0

        return Grid(matrix=matrix)

    def get_path(self, start_pos, end_pos) -> list[pygame.math.Vector2]:
        start_x, start_y = int(start_pos[0] // 64), int(start_pos[1] // 64)
        end_x, end_y = int(end_pos[0] // 64), int(end_pos[1] // 64)

        # Check if the end tile is walkable
        if not self.grid.node(end_x, end_y).walkable:
            return []

        self.grid.cleanup()

        start_node = self.grid.node(start_x, start_y)
        end_node = self.grid.node(end_x, end_y)

        path, _ = self.finder.find_path(start_node, end_node, self.grid)

        return [pygame.math.Vector2((node.x + 0.5) * TILE_SIZE , (node.y + 0.5) * TILE_SIZE) for node in path]




