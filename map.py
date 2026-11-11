import random
import pygame
from settings import TILE_SIZE
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder
from pathfinding.core.diagonal_movement import DiagonalMovement

class GroundLayer:
    """
    Draws the tile-based ground efficiently: only tiles on screen are drawn,
    and animated tiles (e.g. sea water) cycle through their frames.
    """
    def __init__(self, map_tmx, layer_name: str = "Ground") -> None:
        self.width: int = map_tmx.width
        self.height: int = map_tmx.height
        layer = map_tmx.get_layer_by_name(layer_name)

        # gid -> (list of frame surfaces, frame duration in ms) for animated tiles
        animations: dict[int, tuple[list[pygame.Surface], int]] = {}

        self.tiles: list[list] = [[None] * self.width for _ in range(self.height)]
        for y in range(self.height):
            for x in range(self.width):
                gid = layer.data[y][x]
                if not gid:
                    continue
                if gid not in animations:
                    props = map_tmx.get_tile_properties_by_gid(gid) or {}
                    frames = props.get("frames")
                    if frames:
                        animations[gid] = ([map_tmx.get_tile_image_by_gid(f.gid) for f in frames],
                                           frames[0].duration)
                    else:
                        animations[gid] = ([map_tmx.get_tile_image_by_gid(gid)], 0)
                self.tiles[y][x] = animations[gid]

    def draw(self, surface: pygame.Surface, offset: pygame.Vector2) -> None:
        """Draws every visible ground tile."""
        screen_w, screen_h = surface.get_size()
        left = max(0, int(offset.x // TILE_SIZE))
        top = max(0, int(offset.y // TILE_SIZE))
        right = min(self.width, int((offset.x + screen_w) // TILE_SIZE) + 1)
        bottom = min(self.height, int((offset.y + screen_h) // TILE_SIZE) + 1)
        ticks = pygame.time.get_ticks()
        blit = surface.blit
        for y in range(top, bottom):
            row = self.tiles[y]
            screen_y = y * TILE_SIZE - offset.y
            for x in range(left, right):
                tile = row[x]
                if tile is None:
                    continue
                frames, duration = tile
                image = frames[(ticks // duration) % len(frames)] if duration else frames[0]
                blit(image, (x * TILE_SIZE - offset.x, screen_y))


class DecorSprite(pygame.sprite.Sprite):
    """Represents a purely decorative object without collision (e.g., grass, background forest)."""
    def __init__(self, position: tuple[int, int], surf: pygame.Surface, groups: pygame.sprite.AbstractGroup | list[pygame.sprite.AbstractGroup]) -> None:
        super().__init__(groups)
        self.image: pygame.Surface = surf
        self.rect: pygame.FRect = surf.get_frect(topleft=position)
        self.z_layer: int = 1


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


class CollisionGroup(pygame.sprite.Group):
    """
    A sprite group for static obstacles with a spatial hash, so entities only
    test collisions against obstacles that are near them instead of all of them.
    """
    CELL_SIZE = 256

    def __init__(self, *sprites) -> None:
        super().__init__(*sprites)
        self._grid: dict[tuple[int, int], list] | None = None

    def add_internal(self, sprite, layer=None) -> None:
        super().add_internal(sprite)
        self._grid = None  # Rebuild lazily

    def remove_internal(self, sprite) -> None:
        super().remove_internal(sprite)
        self._grid = None

    def _build(self) -> None:
        self._grid = {}
        size = self.CELL_SIZE
        for sprite in self.sprites():
            box = sprite.hitbox
            for cy in range(int(box.top // size), int(box.bottom // size) + 1):
                for cx in range(int(box.left // size), int(box.right // size) + 1):
                    self._grid.setdefault((cx, cy), []).append(sprite)

    def near(self, rect) -> list:
        """Returns the obstacles whose spatial-hash cells overlap the given rect."""
        if self._grid is None:
            self._build()
        size = self.CELL_SIZE
        found = {}
        for cy in range(int(rect.top // size), int(rect.bottom // size) + 1):
            for cx in range(int(rect.left // size), int(rect.right // size) + 1):
                for sprite in self._grid.get((cx, cy), ()):
                    found[id(sprite)] = sprite
        return list(found.values())


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
