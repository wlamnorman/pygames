import pygame

pygame.init()
WINDOW_WIDTH, WINDOW_HEIGHT = 1280, 720
SCREEN = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
CLOCK = pygame.time.Clock()
FPS = 60
IS_RUNNING = True

PLAYER_WIDTH = 50
PLAYER_HEIGHT = 150

BALL_MOVE_SPEED = 11
PLAYERS_MOVE_SPEED = 10


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((PLAYER_WIDTH, PLAYER_HEIGHT))
        self.image.fill("blue")
        self.rect = self.image.get_rect(
            left=PLAYER_WIDTH,
            top=SCREEN.get_height() // 2,
            width=PLAYER_WIDTH,
            height=PLAYER_HEIGHT,
        )

    def update(self):
        self.handle_input()

    def handle_input(self):
        assert self.rect is not None
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            self.rect.y -= PLAYERS_MOVE_SPEED
        elif keys[pygame.K_s]:
            self.rect.y += PLAYERS_MOVE_SPEED


class Opponent(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((PLAYER_WIDTH, PLAYER_HEIGHT))
        self.image.fill("red")
        self.rect = self.image.get_rect(
            left=SCREEN.get_width() - 2 * PLAYER_WIDTH,
            top=SCREEN.get_height() // 2,
            width=PLAYER_WIDTH,
            height=PLAYER_HEIGHT,
        )

    def update(self):
        assert self.rect is not None
        if BALL.sprite.rect.centery > self.rect.centery and self.rect.bottom < SCREEN.get_height():
            self.rect.y += PLAYERS_MOVE_SPEED
        elif BALL.sprite.rect.centery < self.rect.centery and self.rect.top > 0:
            self.rect.y -= PLAYERS_MOVE_SPEED


class Ball(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((25, 25))
        self.image.fill("white")
        self.rect = self.image.get_rect(
            left=SCREEN.get_width() // 2,
            top=SCREEN.get_height() // 2,
            width=self.image.get_width(),
            height=self.image.get_height(),
        )

        self.dx = -BALL_MOVE_SPEED
        self.dy = -BALL_MOVE_SPEED

    def update(self):
        assert self.rect is not None
        self.rect.x += self.dx
        self.rect.y += self.dy

        if self.rect.top <= 0 or self.rect.bottom >= SCREEN.get_height():
            self.dy *= -1

        if self.rect.colliderect(PLAYER.sprite.rect) or self.rect.colliderect(OPPONENT.sprite.rect):
            self.dx *= -1

        if self.rect.left <= 0 or self.rect.right >= SCREEN.get_width():
            self.rect.center = (SCREEN.get_width() // 2, SCREEN.get_height() // 2)
            self.dx *= -1


PLAYER = pygame.sprite.GroupSingle()
PLAYER.add(Player())

OPPONENT = pygame.sprite.GroupSingle()
OPPONENT.add(Opponent())

BALL = pygame.sprite.GroupSingle()
BALL.add(Ball())

while IS_RUNNING:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            IS_RUNNING = False

    SCREEN.fill("black")

    PLAYER.draw(SCREEN)
    PLAYER.update()

    OPPONENT.draw(SCREEN)
    OPPONENT.update()

    BALL.draw(SCREEN)
    BALL.update()

    pygame.display.flip()
    CLOCK.tick(FPS)


pygame.quit()
