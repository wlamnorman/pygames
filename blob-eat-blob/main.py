from __future__ import annotations

import math
import random

from typing_extensions import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from _typeshed import SupportsRichComparison
import pygame

T = TypeVar("T", bound="SupportsRichComparison")
Color = tuple[int, int, int] | str

EPSILON = 1e-9
WINDOW_WIDTH, WINDOW_HEIGHT = 1920, 1080
FPS = 60

N_START_ENEMY_BLOBS = 120


def clamp(val: T, min_val: T, max_val: T) -> T:
    return max(min_val, min(val, max_val))


class GameEngine:
    @staticmethod
    def set_enemy_blob_respawn_timer() -> float:
        return random.randint(5, 25)

    def __init__(self, n_enemies: int):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.FULLSCREEN)
        pygame.display.set_caption("Blob Eat Blob")

        self.player_blob = PlayerBlob(
            x_pos=self.screen.get_width() // 2,
            y_pos=self.screen.get_height() // 2,
            radius=15,
            color="black",
        )
        self.enemy_blobs: list[EnemyBlob] = []
        for _ in range(n_enemies):
            self.enemy_blobs.append(EnemyBlob(self.screen))

        self.is_running = True
        self.clock = pygame.time.Clock()
        self.enemy_blob_respawn_timer = GameEngine.set_enemy_blob_respawn_timer()

        self.font = pygame.font.Font(None, 100)

    def display_score(self):
        surf = self.font.render(
            f"Player radius: {round(self.player_blob.radius, 2)}", True, "purple"
        )
        rect = surf.get_frect(center=(self.screen.get_width() // 2, 100))
        self.screen.blit(surf, rect)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
                pygame.quit()

    def update(self):
        self.player_blob.update()
        self.handle_player_collison_update()
        self.update_enemy_blobs()

        all_blobs = [self.player_blob] + self.enemy_blobs
        for blob in all_blobs:
            blob.ensure_within_screen(self.screen)

        self.handle_enemy_blob_respawns()

    def handle_enemy_blob_respawns(self):
        self.enemy_blob_respawn_timer -= 1
        if self.enemy_blob_respawn_timer == 0:
            self.enemy_blobs.append(EnemyBlob(self.screen))
            self.enemy_blob_respawn_timer = GameEngine.set_enemy_blob_respawn_timer()

    def update_enemy_blobs(self):
        blobs_to_remove = []
        all_blobs = self.enemy_blobs + [self.player_blob]
        for blob in self.enemy_blobs:
            closest_blob = None
            min_distance = float("inf")
            for other in all_blobs:
                if blob == other:
                    continue

                distance = blob.distance_to(other)
                if distance < min_distance and blob.vision_radius > distance:
                    min_distance = distance
                    closest_blob = other

            if not closest_blob:
                continue

            if blob.radius > closest_blob.radius + clamp(
                random.normalvariate(mu=0, sigma=1), min_val=-2, max_val=2
            ):
                blob.move_towards(closest_blob)

                if isinstance(closest_blob, EnemyBlob):
                    if blob.is_collision(closest_blob):
                        blob.eat_blob(closest_blob)
                        blobs_to_remove.append(closest_blob.id)
            else:
                blob.move_away_from(closest_blob)

        self.enemy_blobs = [b for b in self.enemy_blobs if b.id not in blobs_to_remove]

    def handle_player_collison_update(self):
        for idx, blob in enumerate(self.enemy_blobs):
            if self.player_blob.is_collision(blob):
                if self.player_blob.radius > blob.radius:
                    self.player_blob.eat_blob(blob)
                    del self.enemy_blobs[idx]
                else:
                    self.is_running = False

    def draw(self):
        self.screen.fill((230, 255, 230))

        self.player_blob.draw(self.screen)
        for blob in self.enemy_blobs:
            blob.draw(self.screen)

        self.display_score()
        pygame.display.flip()

    def run(self):
        while self.is_running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)


class AbstractBlob:
    BASE_MOVEMENT_SPEED = 4

    @staticmethod
    def calculate_movement_speed(radius: float) -> float:
        return AbstractBlob.BASE_MOVEMENT_SPEED - 0.7 * math.log(1 + radius)

    def __init__(self, x_pos: int, y_pos: int, radius: float, color: Color):
        self.x = x_pos
        self.y = y_pos
        self.radius = radius
        self.color = color
        self.movement_speed = AbstractBlob.calculate_movement_speed(self.radius)

    def draw(self, screen: pygame.Surface):
        pygame.draw.circle(screen, color=self.color, center=(self.x, self.y), radius=self.radius)

    def eat_blob(self, blob: AbstractBlob):
        self_new_area = math.pi * (self.radius**2 + blob.radius**2)
        self.radius = math.sqrt(self_new_area / math.pi)
        self.update_movement_speed()

    def update_movement_speed(self):
        self.movement_speed = AbstractBlob.calculate_movement_speed(self.radius)

    def is_collision(self, blob: AbstractBlob) -> bool:
        return self.radius + blob.radius >= self.distance_to(blob)

    def distance_to(self, blob: AbstractBlob) -> float:
        return math.sqrt((self.x - blob.x) ** 2 + (self.y - blob.y) ** 2)

    def safe_distance_to(self, blob: AbstractBlob) -> float:
        return self.distance_to(blob) + EPSILON

    def ensure_within_screen(self, screen: pygame.Surface):
        self.x = clamp(self.x, min_val=self.radius, max_val=screen.get_width() - self.radius)
        self.y = clamp(self.y, min_val=self.radius, max_val=screen.get_height() - self.radius)


class PlayerBlob(AbstractBlob):
    def handle_input(self):
        k = pygame.key.get_pressed()

        if k[pygame.K_w]:
            self.y -= self.movement_speed
        if k[pygame.K_s]:
            self.y += self.movement_speed
        if k[pygame.K_a]:
            self.x -= self.movement_speed
        if k[pygame.K_d]:
            self.x += self.movement_speed

    def update(self):
        self.handle_input()


class EnemyBlob(AbstractBlob):
    BASE_VISION_RADIUS = 35
    MIN_RADIUS = 3
    EXPECTED_RADIUS = 7
    EXPECTED_RADIUS_GROWTH_RATE = 0.05
    id = 0

    def __init__(self, screen: pygame.Surface):
        self.id = EnemyBlob.id
        EnemyBlob.id += 1
        if EnemyBlob.id >= N_START_ENEMY_BLOBS:
            EnemyBlob.EXPECTED_RADIUS += EnemyBlob.EXPECTED_RADIUS_GROWTH_RATE

        radius = max(EnemyBlob.MIN_RADIUS, int(random.expovariate(1 / EnemyBlob.EXPECTED_RADIUS)))
        self.vision_radius = EnemyBlob.BASE_VISION_RADIUS + 5 * radius
        super().__init__(
            x_pos=random.randint(radius, screen.get_width() - radius),
            y_pos=random.randint(radius, screen.get_height() - radius),
            radius=radius,
            color=(random.randint(75, 255), random.randint(25, 200), random.randint(25, 230)),
        )

    def move_towards(self, other: AbstractBlob):
        self.move_with_randomness(other, moving_towards=True)

    def move_away_from(self, other: AbstractBlob):
        self.move_with_randomness(other, moving_towards=False)

    def move_with_randomness(self, other: AbstractBlob, moving_towards: bool):
        direction_x = other.x - self.x if moving_towards else self.x - other.x
        direction_y = other.y - self.y if moving_towards else self.y - other.y

        angle_to_other = math.atan2(direction_y, direction_x)
        movement_angle = angle_to_other + random.uniform(-math.pi / 4, math.pi / 4)

        self.x += math.cos(movement_angle) * self.movement_speed
        self.y += math.sin(movement_angle) * self.movement_speed


if __name__ == "__main__":
    game = GameEngine(n_enemies=N_START_ENEMY_BLOBS)
    game.run()
