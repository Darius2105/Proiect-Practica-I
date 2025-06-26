import pygame
import sys
import math
import random

pygame.init()
pygame.mixer.init()

# === SUNETE ===
bounce_sound = pygame.mixer.Sound("bounce1.wav")
brick_break_sound = pygame.mixer.Sound("brick_break1.wav")
brick_restore_sound = pygame.mixer.Sound("brick_restore1.wav")
game_over_sound = pygame.mixer.Sound("game_over1.wav")
winner_sound = pygame.mixer.Sound("winner1.wav")
pygame.mixer.music.load("bg_music1.mp3")
pygame.mixer.music.play(-1)

# === ECRAN ===
WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Break IT - Jocul Contelui")

pygame.mouse.set_visible(False)
clock = pygame.time.Clock()

# === OBIECTE ===
paddle = pygame.Rect(WIDTH // 2 - 100, HEIGHT - 40, 200, 20)
BALL_SIZE = 20
ball = pygame.Rect(paddle.centerx - BALL_SIZE // 2, paddle.top - BALL_SIZE, BALL_SIZE, BALL_SIZE)
ball_speed = 400
ball_direction = pygame.Vector2(0, -1).normalize()
ball_attached = True

# === CĂRĂMIZI ===
brick_rows, brick_cols = 4, 6
brick_width = 100  # 2x mai mic decât paddle-ul
brick_height = 20
brick_margin = 10

# Calcul centrare pe ecran
total_width = brick_cols * (brick_width + brick_margin) - brick_margin
x_offset = (WIDTH - total_width) // 2
y_offset = 50

all_bricks = []
for row in range(brick_rows):
    for col in range(brick_cols):
        x = x_offset + col * (brick_width + brick_margin)
        y = y_offset + row * (brick_height + brick_margin)
        brick = pygame.Rect(x, y, brick_width, brick_height)
        all_bricks.append(brick)

active_bricks = all_bricks.copy()
inactive_bricks = []

wall_hit_counter = 0

# === SCÂNTEI ===
class Particle:
    def __init__(self, pos):
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(random.uniform(-2, 2), random.uniform(-2, 2))
        self.lifetime = random.uniform(0.3, 0.7)
        self.radius = random.randint(2, 4)
        self.color = random.choice([(255, 255, 100), (255, 150, 50), (255, 255, 255)])

    def update(self, dt):
        self.pos += self.vel * 60 * dt
        self.lifetime -= dt

    def draw(self, surface):
        if self.lifetime > 0:
            pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), self.radius)

particles = []
def spawn_particles(pos, count=10):
    for _ in range(count):
        particles.append(Particle(pos))

# === TIMER ===
start_ticks = pygame.time.get_ticks()
game_over = False
game_over_img = pygame.image.load("game_over.png")
game_over_img_rect = game_over_img.get_rect(center=(WIDTH // 2, HEIGHT // 2))

winner_img = pygame.image.load("winner.png")
winner_img_rect = winner_img.get_rect(center=(WIDTH // 2, HEIGHT // 2))

# === LOOP ===
running = True
while running:
    dt = clock.tick(60) / 1000

    if not game_over:
        seconds_passed = (pygame.time.get_ticks() - start_ticks) / 1000
        time_left = max(0, 60 - int(seconds_passed))

        if time_left <= 0:
            game_over = True
            pygame.mixer.music.stop()
            game_over_sound.play()
        elif len(active_bricks) == 0:
            game_over = True
            pygame.mixer.music.stop()
            winner_sound.play()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if not game_over and event.type == pygame.MOUSEBUTTONDOWN and ball_attached:
            ball_attached = False
            ball_direction = pygame.Vector2(0, -1)

    # === UPDATE ===
    if not game_over:
        mouse_x, _ = pygame.mouse.get_pos()
        paddle.centerx = mouse_x
        paddle.clamp_ip(screen.get_rect())

        if ball_attached:
            ball.centerx = paddle.centerx
            ball.bottom = paddle.top
        else:
            ball.x += ball_direction.x * ball_speed * dt
            ball.y += ball_direction.y * ball_speed * dt

            hit_wall = False
            if ball.left <= 0 or ball.right >= WIDTH:
                ball_direction.x *= -1
                hit_wall = True
            if ball.top <= 0:
                ball_direction.y *= -1
                hit_wall = True
            if ball.bottom >= HEIGHT:
                ball_attached = True

            if hit_wall:
                wall_hit_counter += 1
                if wall_hit_counter >= 5:
                    wall_hit_counter = 0
                    if inactive_bricks:
                        new_brick = random.choice(inactive_bricks)
                        inactive_bricks.remove(new_brick)
                        active_bricks.append(new_brick)
                        brick_restore_sound.play()
                        spawn_particles(new_brick.center)

            if ball.colliderect(paddle) and ball_direction.y > 0:
                wall_hit_counter = 0  # Resetăm reapariția la atingere cu paddle
                bounce_sound.play()
                offset = (ball.centerx - paddle.centerx) / (paddle.width / 2)
                angle = offset * 75
                radians = angle * (math.pi / 180)
                ball_direction = pygame.Vector2(math.sin(radians), -math.cos(radians)).normalize()
                spawn_particles(ball.center)

            for brick in active_bricks[:]:
                if ball.colliderect(brick):
                    active_bricks.remove(brick)
                    inactive_bricks.append(brick)
                    brick_break_sound.play()
                    spawn_particles(brick.center)

                    dx = ball.centerx - brick.centerx
                    dy = ball.centery - brick.centery
                    if abs(dx) > abs(dy):
                        ball_direction.x *= -1
                    else:
                        ball_direction.y *= -1
                    break

    # === PARTICULE ===
    for p in particles[:]:
        p.update(dt)
        if p.lifetime <= 0:
            particles.remove(p)

    # === RANDĂRI ===
    screen.fill((0, 0, 0))
    if not game_over:
        pygame.draw.rect(screen, (0, 255, 0), paddle)
        pygame.draw.ellipse(screen, (255, 255, 255), ball)
        for brick in active_bricks:
            pygame.draw.rect(screen, (255, 0, 0), brick)
        for p in particles:
            p.draw(screen)

        font = pygame.font.SysFont(None, 36)
        timer_text = font.render(f"Time: {time_left}s", True, (255, 255, 255))
        screen.blit(timer_text, (20, 20))
    else:
        if len(active_bricks) == 0:
            screen.blit(winner_img, winner_img_rect)
        else:
            screen.blit(game_over_img, game_over_img_rect)

    pygame.display.flip()

pygame.quit()
sys.exit()
