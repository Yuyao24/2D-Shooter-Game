import pygame
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
        self.grid = None
        self.finder = AStarFinder(diagonal_movement=DiagonalMovement.only_when_no_obstacle)

        self.create_grid() # Run when created

    def create_grid(self):
        matrix = [[1 for _ in range(self.width)] for _ in range(self.height)]
        for sprite in self.collision_sprites:
            # Calculate which tiles the sprite overlaps
            # Using floor for left/top and ceil for right/bottom ensures any partial overlap marks the tile
            left = max(0, int(sprite.hitbox.left // TILE_SIZE))
            right = min(self.width - 1, int((sprite.hitbox.right - 0.1) // TILE_SIZE))
            top = max(0, int(sprite.hitbox.top // TILE_SIZE))
            bottom = min(self.height - 1, int((sprite.hitbox.bottom - 0.1) // TILE_SIZE))

            # Set tile to unwalkable
            for y in range(top, bottom + 1):
                for x in range(left, right + 1):
                    matrix[y][x] = 0

        self.grid = Grid(matrix=matrix)

    def get_path(self, start_pos, end_pos):
        start_x, start_y = int(start_pos[0] // 64), int(start_pos[1] // 64)
        end_x, end_y = int(end_pos[0] // 64), int(end_pos[1] // 64)

        # Ensure start/end are within bounds
        start_x = max(0, min(self.width - 1, start_x))
        start_y = max(0, min(self.height - 1, start_y))
        end_x = max(0, min(self.width - 1, end_x))
        end_y = max(0, min(self.height - 1, end_y))

        if not self.grid.node(end_x, end_y).walkable:
            return []

        self.grid.cleanup()
        # If the enemy's center is inside an unwalkable tile, temporarily make it walkable so it can escape
        start_node = self.grid.node(start_x, start_y)
        original_walkable = start_node.walkable
        start_node.walkable = True

        end_node = self.grid.node(end_x, end_y)

        path, _ = self.finder.find_path(start_node, end_node, self.grid)

        # Restore the node's original state
        start_node.walkable = original_walkable

        return [pygame.math.Vector2(node.x * 64 + 32, node.y * 64 + 32) for node in path]

class Enemy(pygame.sprite.Sprite):
    def __init__(self, position, groups, collision_sprites, player, pathfinder):
        super().__init__(groups)
        # Enemy image
        self.image = pygame.image.load('assets/images/enemy/Clown.png').convert_alpha()
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

        # State & Timers
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
        colliders = pygame.sprite.spritecollide(
            self,
            self.collision_sprites,
            False,
            lambda spr, obs: spr.hitbox.colliderect(obs.hitbox))

        for obstacle in colliders:
            if obstacle.hitbox.colliderect(self.hitbox):
                if direction == "horizontal":
                    if self.direction.x > 0: self.hitbox.right = obstacle.hitbox.left
                    if self.direction.x < 0: self.hitbox.left = obstacle.hitbox.right
                if direction == "vertical":
                    if self.direction.y < 0: self.hitbox.top = obstacle.hitbox.bottom
                    if self.direction.y > 0: self.hitbox.bottom = obstacle.hitbox.top


