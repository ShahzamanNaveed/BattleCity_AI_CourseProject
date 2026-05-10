"""
Renderer — draws the tile grid, tanks, bullets, and HUD panel.
Pure pygame drawing; no game logic lives here.
"""

import math
import random
import pygame
from constants import *


def _darken(col, factor=0.6):
    out = [min(255, max(0, int(c * factor))) for c in col]
    return pygame.Color(*out)

def _lighten(col, factor=1.4):
    out = [min(255, max(0, int(c * factor))) for c in col]
    return pygame.Color(*out)


class Renderer:
    def __init__(self, screen):
        self.screen = screen
        # Modern font setup
        self.font_title = pygame.font.SysFont("Trebuchet MS", 72, bold=True)
        self.font_xl = pygame.font.SysFont("Trebuchet MS", 56, bold=True)
        self.font_lg = pygame.font.SysFont("Trebuchet MS", 28, bold=True)
        self.font_md = pygame.font.SysFont("Trebuchet MS", 20, bold=True)
        self.font_sm = pygame.font.SysFont("Trebuchet MS", 16)
        self.font_xs = pygame.font.SysFont("Trebuchet MS", 13)
        self._anim   = 0
        self.particles = []

        # Start screen background particles
        self.bg_particles = []
        for _ in range(70):
            x = random.randint(0, SCREEN_W)
            y = random.randint(0, SCREEN_H)
            speed_y = random.uniform(0.3, 1.5)
            size = random.randint(1, 3)
            color = random.choice([(255, 200, 50), (50, 150, 255), (80, 90, 110)])
            self.bg_particles.append([x, y, speed_y, size, color])

    def add_explosion(self, px, py, color, count=15):
        import random
        for _ in range(count):
            dx = random.uniform(-3, 3)
            dy = random.uniform(-3, 3)
            life = random.randint(15, 40)
            self.particles.append([px, py, dx, dy, life, color])

    def tick(self):
        self._anim = (self._anim + 1) % 180

    # ── Main draw call ─────────────────────────────────────────────────────

    def draw(self, tilemap, player, enemies, bullets, level, kills_left, flip=True):
        self.screen.fill(BLACK)
        self._draw_grid(tilemap)
        self._draw_bullets(bullets)
        self._draw_enemies(enemies)
        self._draw_player(player)
        self._draw_particles()
        self._draw_hud(player, level, kills_left)
        if flip:
            pygame.display.flip()

    def draw_start_screen(self):
        # 1. Dark Gradient / Space Background
        self.screen.fill((4, 6, 12))  # Very dark indigo/black
        
        # Draw moving background particles (falling sparks / stars)
        for p in self.bg_particles:
            p[1] += p[2]
            if p[1] > SCREEN_H:
                p[1] = 0
                p[0] = random.randint(0, SCREEN_W)
            # Draw particle with a tiny glow
            pygame.draw.circle(self.screen, p[4], (int(p[0]), int(p[1])), p[3])
            
        # 2. Tech Radar / Target Grid in background
        center_x, center_y = SCREEN_W // 2, SCREEN_H // 2
        angle = self._anim * 0.015
        radar_radius = 220
        # Draw radar rings
        for r in [80, 150, 220]:
            pygame.draw.circle(self.screen, (15, 25, 40), (center_x, center_y), r, 1)
        # Radar sweep line
        pygame.draw.line(self.screen, (30, 60, 100), (center_x, center_y), 
                         (center_x + math.cos(angle)*radar_radius, center_y + math.sin(angle)*radar_radius), 2)

        # 3. Glassmorphism Center Panel
        panel_w, panel_h = 560, 380
        panel_rect = pygame.Rect(center_x - panel_w//2, center_y - panel_h//2, panel_w, panel_h)
        
        # Fake blur/transparency using a dark overlay
        overlay = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        overlay.fill((10, 15, 25, 220))  # Semi-transparent dark blue
        pygame.draw.rect(overlay, (40, 60, 90, 150), overlay.get_rect(), 2, border_radius=16)
        
        # Glowing highlight line at the top of the panel
        pygame.draw.line(overlay, (255, 170, 40, 200), (20, 0), (panel_w - 20, 0), 2)
        self.screen.blit(overlay, panel_rect.topleft)

        # 4. Cinematic Title Rendering
        title1_str = "BATTLE"
        title2_str = "CITY"
        
        t1_surf = self.font_title.render(title1_str, True, WHITE)
        t2_surf = self.font_title.render(title2_str, True, WHITE)
        
        total_w = t1_surf.get_width() + t2_surf.get_width() + 20
        start_x = center_x - total_w // 2
        title_y = panel_rect.y + 40
        
        # Deep glowing drop shadows
        for ox, oy in [(0, 4), (0, 8)]:
            s1_shadow = self.font_title.render(title1_str, True, (0, 0, 0))
            s2_shadow = self.font_title.render(title2_str, True, (0, 0, 0))
            self.screen.blit(s1_shadow, (start_x, title_y + oy))
            self.screen.blit(s2_shadow, (start_x + t1_surf.get_width() + 20, title_y + oy))
            
        # Colorful main text
        t1_main = self.font_title.render(title1_str, True, (240, 245, 255))
        t2_main = self.font_title.render(title2_str, True, (255, 180, 50)) # Bright Amber
        self.screen.blit(t1_main, (start_x, title_y))
        self.screen.blit(t2_main, (start_x + t1_surf.get_width() + 20, title_y))
        
        # Subtitle
        sub_text = self.font_xs.render("TACTICAL COMBAT SIMULATOR  //  SYSTEM ACTIVE", True, (100, 160, 255))
        self.screen.blit(sub_text, (center_x - sub_text.get_width()//2, title_y + 85))

        # 5. Animated Center Graphic (Stylized hexagon and glowing tank)
        icon_y = title_y + 145
        hover = math.sin(self._anim * 0.08) * 8
        
        # Outer Hexagon
        hex_pts = []
        hex_r = 45
        for i in range(6):
            ang = math.radians(i * 60 + 30)
            hex_pts.append((center_x + math.cos(ang)*hex_r, icon_y + hover + math.sin(ang)*hex_r))
        pygame.draw.polygon(self.screen, (15, 25, 40), hex_pts)
        pygame.draw.polygon(self.screen, (50, 150, 255), hex_pts, 2)
        
        # Inner glowing tank
        tank_color = (255, 190, 40)
        pygame.draw.rect(self.screen, tank_color, (center_x - 14, icon_y + hover - 10, 28, 24), border_radius=4)
        pygame.draw.rect(self.screen, WHITE, (center_x - 14, icon_y + hover - 10, 28, 24), 2, border_radius=4)
        pygame.draw.line(self.screen, WHITE, (center_x, icon_y + hover), (center_x, icon_y + hover - 26), 5)

        # 6. Pulsing "PRESS ENTER" Call to Action
        pulse_alpha = 90 + int((math.sin(self._anim * 0.12) + 1) * 82)
        cta_surf = self.font_lg.render("PRESS ENTER TO INITIATE", True, WHITE)
        cta_surf.set_alpha(pulse_alpha)
        self.screen.blit(cta_surf, (center_x - cta_surf.get_width()//2, panel_rect.bottom - 100))

        # 7. Modern Key Prompts
        ctrl_y = panel_rect.bottom - 45
        controls = [("WASD / ARROWS", "MOVE"), ("SPACE", "FIRE"), ("ESC", "ABORT")]
        
        # Calculate total width to center the whole block
        total_w = 0
        spacing_between_items = 40
        elements = []
        for keys, action in controls:
            k_surf = self.font_xs.render(keys, True, (255, 190, 40))
            a_surf = self.font_xs.render(action, True, (140, 160, 190))
            elements.append((k_surf, a_surf))
            total_w += k_surf.get_width() + 8 + a_surf.get_width()
            
        total_w += spacing_between_items * (len(controls) - 1)
        current_x = center_x - total_w // 2
        
        for i, (k_surf, a_surf) in enumerate(elements):
            # Key text
            self.screen.blit(k_surf, (current_x, ctrl_y))
            current_x += k_surf.get_width() + 8
            
            # Action text
            self.screen.blit(a_surf, (current_x, ctrl_y))
            current_x += a_surf.get_width()
            
            # Separator dot for next item
            if i < len(controls) - 1:
                pygame.draw.circle(self.screen, (80, 100, 140), (current_x + spacing_between_items//2, ctrl_y + 8), 2)
                current_x += spacing_between_items

        # 8. Framing elements (High-tech corner brackets)
        def draw_corner(x, y, dx, dy):
            pygame.draw.line(self.screen, (50, 140, 255), (x, y), (x + dx, y), 3)
            pygame.draw.line(self.screen, (50, 140, 255), (x, y), (x, y + dy), 3)
            
        pad = 25
        draw_corner(pad, pad, 40, 40)
        draw_corner(SCREEN_W - pad, pad, -40, 40)
        draw_corner(pad, SCREEN_H - pad, 40, -40)
        draw_corner(SCREEN_W - pad, SCREEN_H - pad, -40, -40)

        pygame.display.flip()

    def _draw_particles(self):
        for p in self.particles[:]:
            p[0] += p[2]
            p[1] += p[3]
            p[4] -= 1
            if p[4] <= 0:
                self.particles.remove(p)
                continue
            alpha = min(255, int((p[4] / 30.0) * 255))
            pygame.draw.circle(self.screen, p[5], (int(p[0]), int(p[1])), max(1, p[4]//8))
            
    # ── Grid ──────────────────────────────────────────────────────────────

    def _draw_grid(self, tm):
        T = TILE_SIZE
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                tile = tm.get(x, y)
                rx   = x * T
                ry   = y * T
                r    = pygame.Rect(rx, ry, T, T)

                if tile == EMPTY:
                    # Give empty areas a subtle very dark shading maybe (using DARK_GREY)
                    pygame.draw.rect(self.screen, DARK_GREY, r)

                elif tile == BRICK:
                    pygame.draw.rect(self.screen, BRICK_RED, r)
                    # Beveled edges
                    pygame.draw.line(self.screen, _lighten(BRICK_RED, 1.3), (rx, ry), (rx+T-1, ry), 1)
                    pygame.draw.line(self.screen, _lighten(BRICK_RED, 1.3), (rx, ry), (rx, ry+T-1), 1)
                    pygame.draw.line(self.screen, BRICK_DARK, (rx, ry+T-1), (rx+T-1, ry+T-1), 1)
                    pygame.draw.line(self.screen, BRICK_DARK, (rx+T-1, ry), (rx+T-1, ry+T-1), 1)
                    # Brick pattern
                    pygame.draw.line(self.screen, BRICK_DARK, (rx, ry + T//2), (rx + T, ry + T//2), 1)
                    pygame.draw.line(self.screen, BRICK_DARK, (rx + T//2, ry), (rx + T//2, ry + T//2), 1)
                    pygame.draw.line(self.screen, BRICK_DARK, (rx + T//4, ry + T//2), (rx + T//4, ry + T), 1)
                    pygame.draw.line(self.screen, BRICK_DARK, (rx + T//4*3, ry + T//2), (rx + T//4*3, ry + T), 1)

                elif tile == STEEL:
                    pygame.draw.rect(self.screen, STEEL_BLUE, r)
                    pygame.draw.rect(self.screen, _lighten(STEEL_BLUE, 1.4), r, 2, border_radius=2)
                    pygame.draw.rect(self.screen, _darken(STEEL_BLUE, 0.7), r.inflate(-4, -4), 1)
                    pygame.draw.line(self.screen, WHITE, (rx+4, ry+4), (rx+8, ry+4), 1)

                elif tile == WATER:
                    # Smooth wave animation using sine
                    pygame.draw.rect(self.screen, WATER_BLUE, r)
                    offset = math.sin((self._anim + x*10 + y*5) * 0.1) * 2
                    pygame.draw.line(self.screen, WATER_LIGHT, (rx+2, ry+T//3+offset), (rx+T-2, ry+T//3+offset), 2)
                    pygame.draw.line(self.screen, WATER_LIGHT, (rx+2, ry+T//3*2-offset), (rx+T-2, ry+T//3*2-offset), 2)

                elif tile == FOREST:
                    # Dark green base
                    pygame.draw.rect(self.screen, DARK_GREEN, r)
                    # Bush clusters
                    pygame.draw.circle(self.screen, GREEN, (rx + T//4+1, ry + T//2), T//3+1)
                    pygame.draw.circle(self.screen, GREEN, (rx + T//2+1, ry + T//3), T//3+1)
                    pygame.draw.circle(self.screen, GREEN, (rx + T//4*3, ry + T//2+1), T//3)

                elif tile == EAGLE:
                    pygame.draw.rect(self.screen, DARK_GREY, r)
                    # Gold base
                    pygame.draw.rect(self.screen, GOLD, (rx+4, ry+T-6, T-8, 4))
                    pygame.draw.rect(self.screen, GOLD, (rx+8, ry+T-10, T-16, 4))
                    # Eagle shape
                    pygame.draw.polygon(self.screen, GOLD, [
                        (rx + T//2, ry + 2),
                        (rx + T - 2, ry + T//2+2),
                        (rx + T//2, ry + T//2+6),
                        (rx + 2, ry + T//2+2),
                    ])
                    # Emblem
                    pygame.draw.circle(self.screen, WHITE, (rx + T//2, ry + T//2), 3)

    # ── Tanks ─────────────────────────────────────────────────────────────

    TANK_COLORS = {
        TANK_PLAYER: (YELLOW, (200, 180, 40)),
        TANK_BASIC:  ((80, 180, 80), (40, 120, 40)),
        TANK_FAST:   ((80, 200, 220), (40, 140, 160)),
        TANK_ARMOR:  ((190, 100, 60), (130, 60, 30)),
        TANK_BOSS:   (RED, (140, 20, 20)),
    }

    def _draw_tank(self, tank, color_pair):
        T      = TILE_SIZE
        body_c, dark_c = color_pair
        
        # Smooth linear interpolation for continuous visual movement
        if not hasattr(tank, 'visual_x') or abs(tank.x - tank.visual_x) > 1.5 or abs(tank.y - tank.visual_y) > 1.5:
            tank.visual_x = float(tank.x)
            tank.visual_y = float(tank.y)
            
        step = 1.0 / max(1.0, float(tank.speed) * 0.85)
        
        if tank.visual_x < tank.x:
            tank.visual_x = min(float(tank.x), tank.visual_x + step)
        elif tank.visual_x > tank.x:
            tank.visual_x = max(float(tank.x), tank.visual_x - step)
            
        if tank.visual_y < tank.y:
            tank.visual_y = min(float(tank.y), tank.visual_y + step)
        elif tank.visual_y > tank.y:
            tank.visual_y = max(float(tank.y), tank.visual_y - step)

        rx = int(tank.visual_x * T)
        ry = int(tank.visual_y * T)

        # Flicker when armor tank is hit
        if tank.tank_type == TANK_ARMOR and tank.hp < tank.max_hp:
            if (self._anim // 3) % 2 == 1:
                body_c = WHITE
        
        # Player glow effect
        if tank.tank_type == TANK_PLAYER:
            glow_r = pygame.Rect(rx, ry, T, T)
            pygame.draw.rect(self.screen, _darken(body_c, 0.4), glow_r, border_radius=6)

        # Body
        body = pygame.Rect(rx + 3, ry + 3, T - 6, T - 6)
        pygame.draw.rect(self.screen, body_c, body, border_radius=4)
        pygame.draw.rect(self.screen, dark_c, body, 2, border_radius=4)

        # Tracks (side bars)
        track_w = max(4, T // 7)
        if tank.direction[1] != 0: # Moving vertically, tracks on left/right
            pygame.draw.rect(self.screen, dark_c, (rx + 1, ry + 2, track_w, T - 4), border_radius=2)
            pygame.draw.rect(self.screen, dark_c, (rx + T - 1 - track_w, ry + 2, track_w, T - 4), border_radius=2)
        else: # Moving horizontally, tracks top/bottom
            pygame.draw.rect(self.screen, dark_c, (rx + 2, ry + 1, T - 4, track_w), border_radius=2)
            pygame.draw.rect(self.screen, dark_c, (rx + 2, ry + T - 1 - track_w, T - 4, track_w), border_radius=2)

        # Hull detail ring
        highlight = pygame.Rect(rx + 7, ry + 7, T - 14, T - 14)
        highlight_color = _lighten(body_c, 1.2)
        pygame.draw.rect(self.screen, highlight_color, highlight, border_radius=6)

        # Barrel
        dx, dy = tank.direction
        cx, cy = rx + T // 2, ry + T // 2
        barrel_length = max(10, T // 2)
        bx = cx + dx * barrel_length
        by_ = cy + dy * barrel_length
        pygame.draw.line(self.screen, WHITE, (cx, cy), (bx, by_), max(4, T // 8))
        pygame.draw.line(self.screen, dark_c, (cx, cy), (bx, by_), max(2, T // 10))

        # HP bar for boss / armor tank
        if tank.max_hp > 1:
            bar_w = T - 4
            filled = int(bar_w * tank.hp / tank.max_hp)
            pygame.draw.rect(self.screen, RED,   (rx + 2, ry - 6, bar_w, 3))
            pygame.draw.rect(self.screen, GREEN, (rx + 2, ry - 6, filled, 3))

    def _draw_player(self, player):
        if not player.alive:
            return
        self._draw_tank(player, self.TANK_COLORS[TANK_PLAYER])

    def _draw_enemies(self, enemies):
        for e in enemies:
            if e.alive:
                colors = self.TANK_COLORS.get(e.tank_type, ((150, 150, 150), (80, 80, 80)))
                self._draw_tank(e, colors)

    # ── Bullets ───────────────────────────────────────────────────────────

    def _draw_bullets(self, bullets):
        for b in bullets:
            if not getattr(b, 'visible', False):
                continue
            px, py = b.rect_xy()
            col    = YELLOW if b.is_player_bullet else ORANGE
            # Outer glow
            pygame.draw.circle(self.screen, _darken(col, 0.5), (int(px), int(py)), 6)
            pygame.draw.circle(self.screen, col, (int(px), int(py)), 3)
            pygame.draw.circle(self.screen, WHITE, (int(px), int(py)), 1)
            # Long Tracer line trailing opposite to direction
            tx = px - b.dx * 12
            ty = py - b.dy * 12
            pygame.draw.line(self.screen, col, (tx, ty), (px, py), 2)

    # ── HUD Panel ─────────────────────────────────────────────────────────

    def _draw_hud(self, player, level, kills_left):
        px = GRID_SIZE * TILE_SIZE
        pw = PANEL_WIDTH
        ph = SCREEN_H
        # Dark pane for UI with subtle gradient effect (approximated with rects)
        pygame.draw.rect(self.screen, (10, 12, 14), (px, 0, pw, ph))
        pygame.draw.line(self.screen, (30, 40, 50), (px, 0), (px, ph), 4)

        y = 20
        # Title with drop shadow
        title = self.font_lg.render("BATTLE", True, GOLD)
        shadow = self.font_lg.render("BATTLE", True, BLACK)
        self.screen.blit(shadow, (px + (pw - shadow.get_width()) // 2 + 3, y + 3))
        self.screen.blit(title, (px + (pw - title.get_width()) // 2, y))
        y += 28
        title2 = self.font_lg.render("CITY", True, ORANGE)
        shadow2 = self.font_lg.render("CITY", True, BLACK)
        self.screen.blit(shadow2, (px + (pw - shadow2.get_width()) // 2 + 3, y + 3))
        self.screen.blit(title2, (px + (pw - title2.get_width()) // 2, y))
        y += 40

        # Beautiful horizontal separator
        def draw_separator(sy):
            c1 = (30, 40, 50)
            pygame.draw.line(self.screen, c1, (px + 15, sy), (px + pw - 15, sy), 2)
            pygame.draw.line(self.screen, BLACK, (px + 15, sy+2), (px + pw - 15, sy+2), 2)

        draw_separator(y); y += 15

        def label(text, val, col=WHITE):
            nonlocal y
            # Backplate
            pygame.draw.rect(self.screen, (20, 24, 28), (px + 10, y-2, pw - 20, 26), border_radius=4)
            s1 = self.font_sm.render(text, True, (120, 130, 140))
            s2 = self.font_md.render(str(val), True, col)
            self.screen.blit(s1, (px + 16, y + 2))
            self.screen.blit(s2, (px + pw - s2.get_width() - 16, y - 2))
            y += 34

        label("LEVEL", level, YELLOW)

        diff_levels = {1: "EASY", 2: "MED", 3: "HARD"}
        diff_text   = diff_levels.get(level, "???")
        diff_col    = {1: GREEN, 2: ORANGE, 3: RED}.get(level, WHITE)
        label("DIFF", diff_text, diff_col)

        label("ENEMIES", kills_left, ORANGE)
        y += 10

        # Lives as scalable glowing hearts
        draw_separator(y); y += 15
        s = self.font_sm.render("LIVES", True, (120, 130, 140))
        self.screen.blit(s, (px + (pw - s.get_width())//2, y))
        y += 24
        
        hearts = ""
        for i in range(3):
            hearts += "♥ " if i < player.lives else "♡ "
        
        # Pulse animation if 1 life
        hcol = RED if player.lives > 1 else (255, max(80, 80 + int(math.sin(self._anim*0.1)*80)), 80)
        hs = self.font_lg.render(hearts.strip(), True, hcol)
        self.screen.blit(hs, (px + (pw - hs.get_width()) // 2, y))
        y += 40

        draw_separator(y); y += 15

        # Legend using background plates
        s = self.font_sm.render("TANKS", True, (120, 130, 140))
        self.screen.blit(s, (px + 15, y)); y += 22
        legend = [
            ("Basic",  (80, 180, 80)),
            ("Fast",   (80, 200, 220)),
            ("Armor",  (190, 100, 60)),
        ]
        for txt, col in legend:
            pygame.draw.rect(self.screen, col, (px + 16, y + 2, 10, 10), border_radius=2)
            s = self.font_xs.render(txt, True, WHITE)
            self.screen.blit(s, (px + 34, y))
            y += 18

        # Draw controls pinned to bottom
        y = ph - 65
        draw_separator(y-10)
        for line in ["[WASD] Move", "[SPACE] Fire", "[ESC] Quit"]:
            s = self.font_xs.render(line, True, (100, 110, 120))
            self.screen.blit(s, (px + 15, y))
            y += 18

    # ── Overlay screens ───────────────────────────────────────────────────

    def draw_overlay(self, text, sub="", color=GOLD):
        # Slightly blurry transparent overlay effect
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((10, 15, 20, 200))
        self.screen.blit(overlay, (0, 0))

        # Box backplate
        bw, bh = 400, 150
        box = pygame.Rect(SCREEN_W//2 - bw//2, SCREEN_H//2 - bh//2, bw, bh)
        pygame.draw.rect(self.screen, (20, 25, 30), box, border_radius=10)
        pygame.draw.rect(self.screen, color, box, 2, border_radius=10)

        big = self.font_lg.render(text, True, color)
        self.screen.blit(big, (SCREEN_W // 2 - big.get_width() // 2, SCREEN_H // 2 - 35))
        if sub:
            # Pulsing subtext alpha
            alpha = 150 + int(math.sin(self._anim * 0.1) * 105)
            sm = self.font_md.render(sub, True, WHITE)
            sm.set_alpha(alpha)
            self.screen.blit(sm, (SCREEN_W // 2 - sm.get_width() // 2, SCREEN_H // 2 + 10))
        pygame.display.flip()

    def draw_level_up_overlay(self, current_level):
        # High-tech blurred/dark overlay
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((5, 10, 15, 210))
        self.screen.blit(overlay, (0, 0))

        # Panel dimensions
        panel_w, panel_h = 580, 240
        center_x, center_y = SCREEN_W // 2, SCREEN_H // 2
        panel_rect = pygame.Rect(center_x - panel_w//2, center_y - panel_h//2, panel_w, panel_h)

        # Glassmorphism backing
        pygame.draw.rect(self.screen, (20, 30, 45, 230), panel_rect, border_radius=16)
        pygame.draw.rect(self.screen, (50, 150, 255), panel_rect, 2, border_radius=16)

        # Level text
        title_str = f"LEVEL {current_level} CLEARED"
        # If the string is too long for the panel, use a slightly smaller font size, but 580 width should handle font_xl comfortably.
        t_surf = self.font_xl.render(title_str, True, (255, 200, 50))
        
        # Title Shadow
        for ox, oy in [(0, 3), (0, 6)]:
            shadow = self.font_xl.render(title_str, True, (0, 0, 0))
            self.screen.blit(shadow, (center_x - shadow.get_width()//2, center_y - 70 + oy))
            
        self.screen.blit(t_surf, (center_x - t_surf.get_width()//2, center_y - 70))

        # Divider line
        pygame.draw.line(self.screen, (50, 150, 255), (center_x - 120, center_y + 10), (center_x + 120, center_y + 10), 2)

        # Next level subtext
        sub_str = f"PREPARING LEVEL {current_level + 1}..."
        sub_surf = self.font_md.render(sub_str, True, (150, 180, 220))
        self.screen.blit(sub_surf, (center_x - sub_surf.get_width()//2, center_y + 35))

        # Pulsing CTA
        pulse = 90 + int((math.sin(self._anim * 0.15) + 1) * 82)
        cta_surf = self.font_md.render("PRESS ENTER TO COMMENCE", True, WHITE)
        cta_surf.set_alpha(pulse)
        self.screen.blit(cta_surf, (center_x - cta_surf.get_width()//2, center_y + 75))

        pygame.display.flip()
