import pygame
import random
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
    def __init__(self, width, height, collision_sprites):
        self.width = width
        self.height = height
        self.collision_sprites = collision_sprites
        self.grid = None
        self.finder = AStarFinder(diagonal_movement=DiagonalMovement.always)
        self.create_grid()

    def create_grid(self):
        matrix = [[1 for _ in range(self.width)] for _ in range(self.height)]
        for sprite in self.collision_sprites:
            # Calculate which grid cells this sprite overlaps
            left = max(0, int(sprite.hitbox.left // 64))
            right = min(self.width - 1, int(sprite.hitbox.right // 64))
            top = max(0, int(sprite.hitbox.top // 64))
            bottom = min(self.height - 1, int(sprite.hitbox.bottom // 64))

            # Mark all overlapping cells as unwalkable
            for y in range(top, bottom + 1):
                for x in range(left, right + 1):
                    matrix[y][x] = 0

        self.grid = Grid(matrix=matrix)

    def get_path(self, start_pos, end_pos):
        start_x, start_y = int(start_pos[0] // 64), int(start_pos[1] // 64)
        end_x, end_y = int(end_pos[0] // 64), int(end_pos[1] // 64)

        if not (0 <= end_x < self.width and 0 <= end_y < self.height): return []
        if self.grid.node(end_x, end_y).walkable == False: return []

        self.grid.cleanup()
        start_node = self.grid.node(start_x, start_y)
        end_node = self.grid.node(end_x, end_y)

        path, _ = self.finder.find_path(start_node, end_node, self.grid)
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
        self.pathfinder = pathfinder
        self.path = []
        self.direction = pygame.math.Vector2()
        self.speed = random.randint(160, 200)

        # State & Timers
        self.active = False
        self.path_timer = pygame.time.get_ticks() + random.randint(0, 500)
        self.last_player_tile = None

    def update(self, dt):
        if self.check_activation():
            self.handle_ai()
            self.handle_movement(dt)

    def check_activation(self):
        if not self.active:
            enemy_vec = pygame.math.Vector2(self.rect.center)
            player_vec = pygame.math.Vector2(self.player.rect.center)
            if (player_vec - enemy_vec).length() < 400:
                self.active = True
        return self.active

    def handle_ai(self):
        current_time = pygame.time.get_ticks()
        if current_time < self.path_timer:
            return

        player_vec = pygame.math.Vector2(self.player.rect.center)
        player_tile = (int(player_vec.x // 64), int(player_vec.y // 64))

        if player_tile != self.last_player_tile:
            if self.check_los():
                self.path = [player_vec]
            else:
                self.path = self.pathfinder.get_path(self.rect.center, player_vec)
                if self.path:
                    self.path.pop(0)

            self.last_player_tile = player_tile

        self.path_timer = current_time + 500 + random.randint(-100, 100)

    def handle_movement(self, dt):
        enemy_vec = pygame.math.Vector2(self.rect.center)
        player_vec = pygame.math.Vector2(self.player.rect.center)

        if (player_vec - enemy_vec).length() < 60:
            self.direction = pygame.math.Vector2()
            return

        if self.path:
            target = self.path[0]
            self.direction = (target - enemy_vec)

            if self.direction.length() > 5:
                self.direction = self.direction.normalize()

                self.hitbox.x += self.direction.x * self.speed * dt
                self.collide("horizontal")

                self.hitbox.y += self.direction.y * self.speed * dt
                self.collide("vertical")

                self.rect.midbottom = self.hitbox.midbottom
            else:
                self.path.pop(0)

    def collide(self, direction):
        for obstacle in self.collision_sprites:
            if obstacle.hitbox.colliderect(self.hitbox):
                if direction == "horizontal":
                    if self.direction.x > 0: self.hitbox.right = obstacle.hitbox.left
                    if self.direction.x < 0: self.hitbox.left = obstacle.hitbox.right
                if direction == "vertical":
                    if self.direction.y < 0: self.hitbox.top = obstacle.hitbox.bottom
                    if self.direction.y > 0: self.hitbox.bottom = obstacle.hitbox.top

    def check_los(self):
        start = self.hitbox.center
        end = self.player.hitbox.center

        for obstacle in self.collision_sprites:
            # Shrunken hitbox prevents getting stuck on wall corners
            if obstacle.hitbox.clipline(start, end):
                return False
        return True

