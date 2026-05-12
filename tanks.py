"""
Tanks — base class + player + all enemy AI tanks.

Module B: BFS (Basic), Greedy Best-First (Fast), A* (Armor)
Module C: Minimax + Alpha-Beta (Boss) — stub ready for later.
"""

import random
from collections import deque
from constants import *
from bullet import Bullet


# ─── Base Tank ────────────────────────────────────────────────────────────────

class Tank:
    def __init__(self, x, y, tank_type):
        self.x          = x
        self.y          = y
        self.tank_type  = tank_type
        self.direction  = DOWN
        self.hp         = HP[tank_type]
        self.max_hp     = HP[tank_type]
        self.alive      = True
        self.speed      = SPEED[tank_type]     # ticks per move
        self._move_tick = 0
        self._fire_cd   = 0                    # cooldown in ticks
        self.fire_rate  = 45                   # ticks between shots (default)
        self.bullets    = []                   # owned bullets

    # ── Shared helpers ────────────────────────────────────────────────────────

    def take_hit(self):
        self.hp -= 1
        if self.hp <= 0:
            self.alive = False
        return self.alive

    def try_move(self, tilemap, dx, dy, occupied=None):
        nx, ny = self.x + dx, self.y + dy
        if occupied is None:
            occupied = set()
        if (nx, ny) in occupied:
            self.direction = (dx, dy)
            return False
        if tilemap.is_passable(nx, ny):
            self.x, self.y = nx, ny
            self.direction  = (dx, dy)
            return True
        self.direction = (dx, dy)
        return False

    def try_shoot(self):
        if self._fire_cd <= 0:
            alive_bullets = [b for b in self.bullets if b.alive]
            if alive_bullets:
                return None
            bx = self.x + self.direction[0]
            by = self.y + self.direction[1]
            b  = Bullet(bx, by, self.direction, self.tank_type)
            self.bullets.append(b)
            self._fire_cd = self.fire_rate
            return b
        return None

    def tick_cooldowns(self):
        self._move_tick += 1
        if self._fire_cd > 0:
            self._fire_cd -= 1

    def can_move(self):
        return self._move_tick >= self.speed

    def reset_move_tick(self):
        self._move_tick = 0

    def line_of_sight(self, tilemap, tx, ty):
        """True if clear horizontal or vertical line of sight to (tx, ty)."""
        if self.x == tx:
            miny, maxy = sorted([self.y, ty])
            for y in range(miny + 1, maxy):
                t = tilemap.get(self.x, y)
                if t in (BRICK, STEEL, WATER):
                    return False
            return True
        if self.y == ty:
            minx, maxx = sorted([self.x, tx])
            for x in range(minx + 1, maxx):
                t = tilemap.get(x, self.y)
                if t in (BRICK, STEEL, WATER):
                    return False
            return True
        return False


# ─── Player Tank ──────────────────────────────────────────────────────────────

class PlayerTank(Tank):
    def __init__(self, x, y):
        super().__init__(x, y, TANK_PLAYER)
        self.direction  = UP
        self.fire_rate  = 64          # ticks between shots (scaled for 60 FPS)
        self.lives      = 3           # 3 lives as requested
        self._pending   = None        # direction set this frame only

    def set_direction(self, dx, dy):
        self._pending = (dx, dy)

    def update(self, tilemap, shoot=False, occupied=None):
        self.tick_cooldowns()
        # Player cannot move and shoot in the same tick
        if not shoot and self.can_move() and self._pending is not None:
            self.try_move(tilemap, *self._pending, occupied=occupied)
            self.reset_move_tick()
        # Clear pending so tank stops when key released
        self._pending = None
        if shoot:
            alive_bullets = [b for b in self.bullets if b.alive]
            if not alive_bullets:
                self.try_shoot()

    def respawn(self):
        self.x, self.y  = PLAYER_SPAWN
        self.hp          = HP[TANK_PLAYER]
        self.alive       = True
        self.direction   = UP
        self.bullets.clear()


# ─── Basic Tank (Simple Reflex + BFS) ────────────────────────────────────────

class BasicTank(Tank):
    """
    Simple Reflex Agent — no memory, no planning, pure reaction.
    Primary Rule: IF player is in same row OR column AND no wall between
                  THEN shoot.
    Movement Rule: IF path to Eagle exists via BFS THEN follow next BFS step.
                   ELSE turn to a random free direction.
    Wall Rule: IF next tile in current direction is Brick THEN shoot to
               destroy it, THEN resume movement.
    BFS treats only passable tiles (Empty, Forest) as cost = 1.
    Re-run BFS: (a) at spawn, (b) when path tile is blocked, (c) every 5s.
    """

    def __init__(self, x, y, level=1):
        super().__init__(x, y, TANK_BASIC)
        self.direction  = DOWN
        self.fire_rate  = 120 if level == 1 else 90
        self.speed      = SPEED[TANK_BASIC] + (8 if level == 1 else 0)
        self._path      = []
        self._replan_cd = 0          # triggers BFS recompute
        self._sight_ticks = 0

    def update(self, tilemap, player, occupied=None):
        self.tick_cooldowns()

        # ── Primary Rule (Simple Reflex): shoot player if in LoS ──────────
        if self.line_of_sight(tilemap, player.x, player.y):
            self._sight_ticks += 1
            if self._sight_ticks >= 60:
                dx = player.x - self.x
                dy = player.y - self.y
                if dx != 0:
                    self.direction = (1 if dx > 0 else -1, 0)
                else:
                    self.direction = (0, 1 if dy > 0 else -1)
                self.try_shoot()
        else:
            self._sight_ticks = 0

        # ── BFS replan timer: at spawn, when blocked, every 5 seconds ─────
        self._replan_cd -= 1
        if self._replan_cd <= 0 or not self._path:
            self._path      = tilemap.bfs_path((self.x, self.y), EAGLE_POS)
            self._replan_cd = FPS * 5

        # ── Wall Rule: if next tile in current direction is Brick → shoot ─
        look_x = self.x + self.direction[0]
        look_y = self.y + self.direction[1]
        if tilemap.get(look_x, look_y) == BRICK:
            self.try_shoot()
            return   # wait for wall to be destroyed before moving

        # ── Movement Rule: follow BFS path or random fallback ─────────────
        if self.can_move():
            if self._path:
                nx, ny = self._path[0]
                if self.try_move(tilemap, nx - self.x, ny - self.y, occupied=occupied):
                    self._path.pop(0)
                else:
                    # Path blocked — replan next tick
                    self._path = []
                    self.try_move(tilemap, *random.choice(DIRS), occupied=occupied)
            else:
                # No BFS path exists — turn to a random free direction
                d = random.choice(DIRS)
                self.try_move(tilemap, *d, occupied=occupied)
            self.reset_move_tick()


# ─── Fast Tank (Goal-Based + Greedy Best-First) ───────────────────────────────

class FastTank(Tank):
    """
    Goal-Based Agent — single goal: reach and destroy the Eagle.
    Ignores player completely.
    Movement: Greedy Best-First single-step decision — on every tick, pick
              the neighbour tile with the lowest Manhattan distance to Eagle.
    Wall Rule: IF next tile is Brick THEN shoot it to clear the path.
               Do NOT detour — push straight through.
    Can get stuck in local minima — this is intentional.
    """

    def __init__(self, x, y, level=1):
        super().__init__(x, y, TANK_FAST)
        self.direction = DOWN
        self.fire_rate = 100 if level == 1 else 80
        self.speed     = max(1, SPEED[TANK_FAST] - 4)

    def update(self, tilemap, player, occupied=None):
        self.tick_cooldowns()

        # ── Greedy Best-First: recompute single step every tick ────────────
        # No full path — just pick the neighbour with lowest h(n)
        next_step = tilemap.greedy_next_step((self.x, self.y), EAGLE_POS)

        # ── Wall Rule: shoot brick to push straight through ───────────────
        if next_step:
            nx, ny = next_step[0]
            if tilemap.get(nx, ny) == BRICK:
                self.direction = (nx - self.x, ny - self.y)
                self.try_shoot()
                return   # wait for brick to break

        # ── Movement: follow the greedy step ──────────────────────────────
        if self.can_move():
            if next_step:
                nx, ny = next_step[0]
                if not self.try_move(tilemap, nx - self.x, ny - self.y, occupied=occupied):
                    # Stuck (occupied by another tank) — wait, don't detour
                    pass
            else:
                # Local minimum — no valid neighbour, random fallback
                self.try_move(tilemap, *random.choice(DIRS), occupied=occupied)
            self.reset_move_tick()



# ─── Armor Tank (Model-Based Reflex + A*) ─────────────────────────────────────

class ArmorTank(Tank):
    """
    Model-Based Reflex Agent — maintains internal state (hitCount).
    Changes behavior when damaged.
    State Variable: hitCount (0 to 3). Tracks hits. Persists across ticks.
    Rule 1 (0-2 hits): Navigate toward Eagle using A*. If player in LoS, shoot.
    Rule 2 (3rd hit):  RETREAT. Abandon A* path. Find nearest Steel Wall via
                       BFS and move behind it for cover.
    Rule 3 (after retreat): Wait 2s behind cover, then recompute A* to Eagle.
    A* details:
      h(n) = Manhattan distance to Eagle (admissible).
      g(n) costs: Empty=1, Forest=1, Brick=3, Steel=∞, Water=∞.
      Re-run A* at spawn, after retreating to cover, and on map changes.
    """

    def __init__(self, x, y, level=1):
        super().__init__(x, y, TANK_ARMOR)
        self.direction   = DOWN
        self.fire_rate   = 90   # fires every ~1.5s at 60 FPS
        self._path       = []
        self._state      = "attack"    # "attack" | "retreat" | "cover"
        self._cover_cd   = 0
        self._hit_count  = 0           # Model-based state variable
        self._sight_ticks = 0

    def take_hit(self):
        super().take_hit()
        self._hit_count += 1
        # Rule 2: on 3rd hit → RETREAT to steel cover
        if self._hit_count >= 3 and self._state == "attack":
            self._state = "retreat"
            self._path  = []           # abandon current A* path
        return self.alive

    def _find_cover(self, tilemap):
        """BFS to nearest steel wall tile (park adjacent to it)."""
        visited = {(self.x, self.y)}
        queue   = deque([((self.x, self.y), [])])
        while queue:
            (cx, cy), path = queue.popleft()
            for dx, dy in DIRS:
                nx, ny = cx + dx, cy + dy
                if (nx, ny) in visited:
                    continue
                visited.add((nx, ny))
                if tilemap.get(nx, ny) == STEEL:
                    return path   # park on the tile before steel
                if tilemap.is_passable(nx, ny):
                    queue.append(((nx, ny), path + [(nx, ny)]))
        return []

    def update(self, tilemap, player, occupied=None):
        self.tick_cooldowns()

        # ── Rule 1: Shoot player if in line-of-sight (attack & retreat) ───
        if self.line_of_sight(tilemap, player.x, player.y):
            self._sight_ticks += 1
            if self._sight_ticks >= 60:
                dx = player.x - self.x
                dy = player.y - self.y
                self.direction = (1 if dx > 0 else -1, 0) if dx != 0 else (0, 1 if dy > 0 else -1)
                self.try_shoot()
        else:
            self._sight_ticks = 0

        # ── Rule 2: RETREAT — find nearest steel wall for cover ───────────
        if self._state == "retreat":
            if not self._path:
                self._path = self._find_cover(tilemap)
                if not self._path:
                    self._state = "attack"
            if self._path and self.can_move():
                nx, ny = self._path[0]
                if self.try_move(tilemap, nx - self.x, ny - self.y, occupied=occupied):
                    self._path.pop(0)
                    if not self._path:
                        self._state  = "cover"
                        self._cover_cd = FPS * 2    # wait 2 seconds
                self.reset_move_tick()

        # ── Rule 3: COVER — wait 2s then recompute A* and resume attack ──
        elif self._state == "cover":
            self._cover_cd -= 1
            if self._cover_cd <= 0:
                self._state = "attack"
                self._path  = tilemap.astar_path((self.x, self.y), EAGLE_POS)

        # ── ATTACK — A* navigation to Eagle ──────────────────────────────
        else:
            if not self._path:
                self._path = tilemap.astar_path((self.x, self.y), EAGLE_POS)

            # A* wall rule: shoot through brick strategically (cost 3 < detour)
            if self._path:
                nx, ny = self._path[0]
                if tilemap.get(nx, ny) == BRICK:
                    self.direction = (nx - self.x, ny - self.y)
                    self.try_shoot()
                    return

            if self.can_move() and self._path:
                nx, ny = self._path[0]
                if self.try_move(tilemap, nx - self.x, ny - self.y, occupied=occupied):
                    self._path.pop(0)
                else:
                    self._path = []   # replan next tick
                    self.try_move(tilemap, *random.choice(DIRS), occupied=occupied)
                self.reset_move_tick()


# ─── Boss Tank (Minimax + Alpha-Beta) ─────────────────────────────────────────

class BossTank(Tank):
    """
    Boss Tank using Minimax with Alpha-Beta Pruning.
    Simulates player responses to choose optimal actions.
    Depth varies by HP: 10-7:2, 6-4:3, 3-1:4
    """

    def __init__(self, x, y):
        super().__init__(x, y, TANK_BOSS)
        self.direction = DOWN
        self.fire_rate = 60  # fires every ~1s
        self.actions = ['up', 'down', 'left', 'right', 'shoot']
        self.dir_map = {'up': UP, 'down': DOWN, 'left': LEFT, 'right': RIGHT}
        self._sight_ticks = 0

    def get_depth(self):
        if self.hp >= 7: return 2
        elif self.hp >= 4: return 3
        else: return 4

    def update(self, tilemap, player, occupied=None):
        self.tick_cooldowns()

        # Use minimax to choose best action
        best_action = self._choose_action(tilemap, player)
        
        if best_action == 'shoot':
            # Check line of sight
            if self.line_of_sight(tilemap, player.x, player.y):
                self._sight_ticks += 1
                if self._sight_ticks >= 60:
                    dx = player.x - self.x
                    dy = player.y - self.y
                    self.direction = (1 if dx > 0 else -1, 0) if dx != 0 else (0, 1 if dy > 0 else -1)
                    self.try_shoot()
            else:
                self._sight_ticks = 0
        else:
            self._sight_ticks = 0
            # Move
            dx, dy = self.dir_map[best_action]
            if self.can_move():
                self.try_move(tilemap, dx, dy, occupied=occupied)
                self.reset_move_tick()

    def _choose_action(self, tilemap, player):
        """Choose action using minimax."""
        import math
        
        def evaluate_state(boss_pos, boss_hp, player_pos, player_hp):
            if boss_hp <= 0: return -1000
            if player_hp <= 0: return 1000
            # Heuristic: HP difference + distance
            hp_diff = boss_hp - player_hp
            dist = abs(boss_pos[0] - player_pos[0]) + abs(boss_pos[1] - player_pos[1])
            return hp_diff * 10 - dist
        
        def simulate_action(state, action, is_boss):
            boss_pos, boss_hp, player_pos, player_hp = state
            if action == 'shoot':
                if self._line_of_sight_sim(tilemap, boss_pos if is_boss else player_pos, player_pos if is_boss else boss_pos):
                    if is_boss:
                        player_hp -= 1
                    else:
                        boss_hp -= 1
            else:
                dx, dy = self.dir_map[action]
                new_pos = (boss_pos[0] + dx, boss_pos[1] + dy) if is_boss else (player_pos[0] + dx, player_pos[1] + dy)
                if tilemap.is_passable(*new_pos):
                    if is_boss:
                        boss_pos = new_pos
                    else:
                        player_pos = new_pos
            return (boss_pos, boss_hp, player_pos, player_hp)
        
        def minimax(state, depth, alpha, beta, maximizing):
            if depth == 0 or state[1] <= 0 or state[3] <= 0:
                return evaluate_state(*state)
            
            if maximizing:  # boss turn
                max_eval = -math.inf
                for action in self.actions:
                    new_state = simulate_action(state, action, True)
                    eval = minimax(new_state, depth - 1, alpha, beta, False)
                    max_eval = max(max_eval, eval)
                    alpha = max(alpha, eval)
                    if beta <= alpha:
                        break
                return max_eval
            else:  # player turn
                min_eval = math.inf
                for action in self.actions:
                    new_state = simulate_action(state, action, False)
                    eval = minimax(new_state, depth - 1, alpha, beta, True)
                    min_eval = min(min_eval, eval)
                    beta = min(beta, eval)
                    if beta <= alpha:
                        break
                return min_eval
        
        # Current state
        state = ((self.x, self.y), self.hp, (player.x, player.y), player.hp)
        depth = self.get_depth()
        
        best_eval = -math.inf
        best_action = 'shoot'  # default
        
        for action in self.actions:
            new_state = simulate_action(state, action, True)
            eval = minimax(new_state, depth - 1, -math.inf, math.inf, False)
            if eval > best_eval:
                best_eval = eval
                best_action = action
        
        return best_action

    def _line_of_sight_sim(self, tilemap, start, end):
        """Simplified line of sight for simulation."""
        sx, sy = start
        ex, ey = end
        if sx == ex:
            miny, maxy = sorted([sy, ey])
            for y in range(miny + 1, maxy):
                if tilemap.get(sx, y) in (BRICK, STEEL, WATER):
                    return False
            return True
        elif sy == ey:
            minx, maxx = sorted([sx, ex])
            for x in range(minx + 1, maxx):
                if tilemap.get(x, sy) in (BRICK, STEEL, WATER):
                    return False
            return True
        return False


# ─── Factory ──────────────────────────────────────────────────────────────────

def make_enemy(tank_type, x, y, level=1):
    if tank_type == TANK_BASIC:
        return BasicTank(x, y, level=level)
    if tank_type == TANK_FAST:
        return FastTank(x, y, level=level)
    if tank_type == TANK_ARMOR:
        return ArmorTank(x, y, level=level)
    if tank_type == TANK_BOSS:
        return BossTank(x, y)
    raise ValueError(f"Unknown tank type: {tank_type}")
