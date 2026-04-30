import pygame
import math
import sys

WIDTH, HEIGHT = 1000, 600
FPS = 60
GRAVITY = 0.55
GROUND_Y = HEIGHT - 80

SLING_X, SLING_Y = 160, GROUND_Y - 140  # lifted up by ~100 pixels
MAX_DRAG = 140

WHITE = (245, 245, 245)
BLACK = (30, 30, 30)
BROWN = (120, 70, 15)
GREEN = (30, 160, 40)
RED = (200, 40, 40)
GRAY = (150, 150, 150)
SKY = (135, 206, 235)
YELLOW = (255, 220, 40)
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Angry Birds — Reachable Pigs Fix")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 20)
bigfont = pygame.font.SysFont("Arial", 36)
def clamp(v, a, b):
    return max(a, min(b, v))

class Bird:
    def __init__(self, x, y, radius=14):
        self.init_x, self.init_y = x, y
        self.x, self.y = x, y
        self.radius = radius
        self.vx = 0
        self.vy = 0
        self.launched = False
        self.stuck = True
        self.dead = False
    def reset(self):
        self.x, self.y = self.init_x, self.init_y
        self.vx = self.vy = 0
        self.launched = False
        self.stuck = True
        self.dead = False
    def update(self):
        if self.launched:
            self.vy += GRAVITY
            self.x += self.vx
            self.y += self.vy
            if self.y + self.radius > GROUND_Y:
                self.y = GROUND_Y - self.radius
                if abs(self.vy) > 6:
                    self.vy = -self.vy * 0.35
                    self.vx *= 0.7
                else:
                    self.vy = 0
                    self.vx = 0
                    self.launched = False
                    self.dead = True
    def draw(self, surf):
        pygame.draw.circle(surf, RED, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surf, WHITE, (int(self.x + 5), int(self.y - 3)), 4)
        pygame.draw.circle(surf, BLACK, (int(self.x + 6), int(self.y - 3)), 2)

class Block:
    def __init__(self, x, y, w, h, hp=3):
        self.x, self.y = x, y
        self.w, self.h = w, h
        self.hp = hp
    def rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)
    def hit(self, impulse):
        self.hp -= impulse / 10.0
    def draw(self, surf):
        color = (clamp(int(200 - (3 - self.hp) * 40), 60, 200),
                 clamp(int(120 - (3 - self.hp) * 30), 40, 150),
                 50)
        pygame.draw.rect(surf, color, self.rect())
        pygame.draw.rect(surf, BLACK, self.rect(), 2)

class Pig:
    def __init__(self, x, y, radius=18):
        self.x, self.y = x, y
        self.radius = radius
        self.alive = True
        self.hit_timer = 0
    def draw(self, surf):
        if self.alive:
            pygame.draw.circle(surf, GREEN, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(surf, BLACK, (int(self.x - 5), int(self.y - 5)), 3)
        elif self.hit_timer > 0:
            pygame.draw.circle(surf, YELLOW, (int(self.x), int(self.y)), int(self.radius * 1.5))
            self.hit_timer -= 1

class Level:
    def __init__(self):
        self.blocks = []
        self.pigs = []
        self.create_demo()
    def create_demo(self):
        self.blocks.clear()
        self.pigs.clear()
        base_x = 600
        base_y = GROUND_Y - 60
        # simple tower
        self.blocks.append(Block(base_x, base_y + 40, 120, 20, hp=4))
        self.blocks.append(Block(base_x + 20, base_y - 20, 80, 20, hp=3))
        self.blocks.append(Block(base_x + 40, base_y - 60, 40, 20, hp=2))
        # lowered pigs — easier hits
        self.pigs.append(Pig(base_x + 60, base_y + 40, radius=18))
        self.pigs.append(Pig(base_x + 60, base_y - 10, radius=18))
    def draw(self, surf):
        for b in self.blocks:
            b.draw(surf)
        for p in self.pigs:
            p.draw(surf)
    def check_collisions(self, bird):
        for pig in self.pigs:
            if not pig.alive:
                continue
            dx = pig.x - bird.x
            dy = pig.y - bird.y
            dist = math.hypot(dx, dy)
            if dist < pig.radius + bird.radius:
                rel_speed = math.hypot(bird.vx, bird.vy)
                impulse = rel_speed * bird.radius
                if impulse > 3.5:
                    pig.alive = False
                    pig.hit_timer = 25
        for b in self.blocks:
            rect = b.rect()
            cx = clamp(bird.x, rect.left, rect.right)
            cy = clamp(bird.y, rect.top, rect.bottom)
            dx = bird.x - cx
            dy = bird.y - cy
            if dx * dx + dy * dy < bird.radius * bird.radius:
                rel_speed = math.hypot(bird.vx, bird.vy)
                impulse = rel_speed * bird.radius * 0.6
                b.hit(impulse)
                if abs(dx) > abs(dy):
                    bird.vx = -bird.vx * 0.6
                else:
                    bird.vy = -bird.vy * 0.6
                bird.x += clamp(dx, -10, 10)
                bird.y += clamp(dy, -10, 10)
        self.blocks = [b for b in self.blocks if b.hp > 0.5]
    def pigs_remaining(self):
        return sum(1 for p in self.pigs if p.alive)

class Game:
    def __init__(self):
        self.level = Level()
        self.bird = Bird(SLING_X - 10, SLING_Y + 2)
        self.score = 0
        self.dragging = False
    def reset_level(self):
        self.level = Level()
        self.bird.reset()
        self.score = 0
        self.dragging = False
    def update(self):
        self.bird.update()
        if self.bird.launched:
            self.level.check_collisions(self.bird)
        alive = self.level.pigs_remaining()
        dead_pigs = 2 - alive
        self.score = dead_pigs * 100
    def draw_ground(self, surf):
        pygame.draw.rect(surf, (100, 60, 20), (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
        pygame.draw.rect(surf, (40, 180, 60), (0, GROUND_Y - 4, WIDTH, 8))
    def draw_slingshot(self, surf):
        # taller poles now
        pygame.draw.rect(surf, BROWN, (SLING_X - 10, SLING_Y - 80, 12, 140))
        pygame.draw.rect(surf, BROWN, (SLING_X + 10, SLING_Y - 80, 12, 140))
        pygame.draw.line(surf, BLACK, (SLING_X - 10, SLING_Y + 80), (SLING_X + 30, SLING_Y + 80), 4)
    def draw_ui(self, surf):
        score_surf = font.render(f"Score: {self.score}", True, BLACK)
        pigs_surf = font.render(f"Pigs Remaining: {self.level.pigs_remaining()}", True, BLACK)
        instr = font.render("R: Restart   ESC: Menu/Quit", True, BLACK)
        surf.blit(score_surf, (20, 10))
        surf.blit(pigs_surf, (20, 36))
        surf.blit(instr, (WIDTH - 300, 10))
    def draw(self, surf):
        surf.fill(SKY)
        self.draw_ground(surf)
        self.draw_slingshot(surf)
        self.level.draw(surf)
        if self.dragging and not self.bird.launched:
            mx, my = pygame.mouse.get_pos()
            dx = mx - SLING_X
            dy = my - SLING_Y
            dist = math.hypot(dx, dy)
            if dist > MAX_DRAG:
                scale = MAX_DRAG / dist
                dx *= scale
                dy *= scale
            pygame.draw.line(surf, (50, 20, 10), (SLING_X - 6, SLING_Y - 4), (SLING_X + dx, SLING_Y + dy), 6)
            pygame.draw.line(surf, (50, 20, 10), (SLING_X + 22, SLING_Y - 4), (SLING_X + dx, SLING_Y + dy), 6)
        self.bird.draw(surf)
        self.draw_ui(surf)
        pigs_left = self.level.pigs_remaining()
        if pigs_left == 0:
            win = bigfont.render("Level Cleared! Press R to play again.", True, BLACK)
            surf.blit(win, (WIDTH // 2 - win.get_width() // 2, 200))
        elif self.bird.dead:
            lose = bigfont.render("Try Again! Press R to restart.", True, BLACK)
            surf.blit(lose, (WIDTH // 2 - lose.get_width() // 2, 200))
    # ---------- Input ----------
    def handle_mouse_down(self, pos):
        bx, by = self.bird.x, self.bird.y
        if math.hypot(pos[0] - bx, pos[1] - by) <= self.bird.radius + 6 and self.bird.stuck:
            self.dragging = True
    def handle_mouse_up(self, pos):
        if self.dragging:
            mx, my = pos
            dx = mx - SLING_X
            dy = my - SLING_Y
            dist = math.hypot(dx, dy)
            if dist > MAX_DRAG and dist != 0:
                scale = MAX_DRAG / dist
                dx *= scale
                dy *= scale
            force_multiplier = 0.24  # slightly more power
            self.bird.vx = -dx * force_multiplier
            self.bird.vy = -dy * force_multiplier
            self.bird.launched = True
            self.bird.stuck = False
        self.dragging = False
    def handle_mouse_motion(self, pos):
        if self.dragging and self.bird.stuck:
            mx, my = pos
            dx = mx - SLING_X
            dy = my - SLING_Y
            dist = math.hypot(dx, dy)
            if dist > MAX_DRAG and dist != 0:
                scale = MAX_DRAG / dist
                dx *= scale
                dy *= scale
            self.bird.x = SLING_X + dx
            self.bird.y = SLING_Y + dy

def draw_button(surf, rect, text, active=False):
    color = (70, 160, 70) if active else (50, 140, 50)
    pygame.draw.rect(surf, color, rect, border_radius=8)
    pygame.draw.rect(surf, BLACK, rect, 2, border_radius=8)
    txt = bigfont.render(text, True, WHITE)
    surf.blit(txt, (rect.x + (rect.w - txt.get_width()) // 2,
                    rect.y + (rect.h - txt.get_height()) // 2))
def menu_loop():
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()

        screen.fill(SKY)
        title = bigfont.render("Angry Birds — Raised Slingshot", True, BLACK)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 60))
        sub = font.render("Click & drag to shoot the bird at the pigs!", True, BLACK)
        screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 110))
        play_rect = pygame.Rect(WIDTH // 2 - 160, 250, 320, 60)
        quit_rect = pygame.Rect(WIDTH // 2 - 160, 340, 320, 60)
        mx, my = pygame.mouse.get_pos()
        draw_button(screen, play_rect, "Play", play_rect.collidepoint(mx, my))
        draw_button(screen, quit_rect, "Quit", quit_rect.collidepoint(mx, my))
        if pygame.mouse.get_pressed()[0]:
            if play_rect.collidepoint(mx, my):
                return
            if quit_rect.collidepoint(mx, my):
                pygame.quit(); sys.exit()
        pygame.display.flip()
        clock.tick(FPS)

def main():
    while True:
        menu_loop()
        game = Game()
        running = True
        while running:
            dt = clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        game.reset_level()
                    if event.key == pygame.K_ESCAPE:
                        running = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    game.handle_mouse_down(event.pos)
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    game.handle_mouse_up(event.pos)
                if event.type == pygame.MOUSEMOTION:
                    game.handle_mouse_motion(event.pos)
            game.update()
            game.draw(screen)
            pygame.display.flip()
if __name__ == "__main__":
    main()