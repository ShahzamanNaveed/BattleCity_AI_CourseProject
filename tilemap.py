"""
Module A (lite) — Map representation + simple procedural generator.
Full CSP backtracking can be wired in later; this version uses
a seeded random fill that respects the hard constraints.
"""

import random
from collections import deque
from constants import *


# ─── Tilemap ──────────────────────────────────────────────────────────────────

class Tilemap:
    """Holds the 26×26 grid and exposes helpers used by AI modules."""

    def __init__(self, grid=None):
        if grid is None:
            self.grid = [[EMPTY] * GRID_SIZE for _ in range(GRID_SIZE)]
        else:
            self.grid = [row[:] for row in grid]  # copy

    # ── accessors ─────────────────────────────────────────────────────────────

    def get(self, x, y):
        if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
            return self.grid[y][x]
        return STEEL  # treat OOB as impassable

    def set(self, x, y, tile):
        if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
            self.grid[y][x] = tile

    def is_passable(self, x, y):
        t = self.get(x, y)
        return t in (EMPTY, FOREST)

    def destroy_brick(self, x, y):
        if self.get(x, y) == BRICK:
            self.set(x, y, EMPTY)
            return True
        return False

    # ── BFS reachability ──────────────────────────────────────────────────────

    def bfs_path(self, start, goal):
        """
        Standard queue-based BFS.
        Returns list of (x,y) steps from start→goal, or [] if unreachable.
        Treats all passable tiles (Empty, Forest) as equal cost = 1.
        Does NOT consider shooting through brick — only open paths.
        """
        sx, sy = start
        gx, gy = goal
        if (sx, sy) == (gx, gy):
            return []
        visited = {(sx, sy)}
        queue   = deque([((sx, sy), [])])
        while queue:
            (cx, cy), path = queue.popleft()
            for dx, dy in DIRS:
                nx, ny = cx + dx, cy + dy
                if (nx, ny) in visited:
                    continue
                visited.add((nx, ny))
                new_path = path + [(nx, ny)]
                if (nx, ny) == (gx, gy):
                    return new_path
                # BFS only traverses passable tiles (EMPTY, FOREST)
                if self.is_passable(nx, ny):
                    queue.append(((nx, ny), new_path))
        return []

    def reachable(self, start, goal):
        return len(self.bfs_path(start, goal)) > 0 or start == goal

    # ── A* pathfinding ────────────────────────────────────────────────────────

    def astar_path(self, start, goal):
        """
        A* with per-tile g-costs (cost-aware pathfinding):
            Empty = 1, Forest = 1, Brick = 3 (shoot + wait penalty),
            Steel = ∞ (blocked), Water = ∞ (blocked).
        Heuristic h(n): Manhattan distance to Eagle — admissible.
        Returns list of (x,y) steps or [].
        """
        import heapq

        # g(n) costs per tile type
        TILE_COST = {EMPTY: 1, FOREST: 1, BRICK: 3}
        # Steel and Water are impassable (infinite cost) — not in dict

        def h(x, y):
            """Manhattan distance heuristic — admissible, never overestimates."""
            return abs(x - goal[0]) + abs(y - goal[1])

        # Priority queue: (f, g, position, path)
        open_set = [(h(*start), 0, start, [])]
        visited  = {}  # maps (x,y) → best g cost seen

        while open_set:
            f, g, (cx, cy), path = heapq.heappop(open_set)
            if (cx, cy) in visited:
                continue
            visited[(cx, cy)] = g
            if (cx, cy) == goal:
                return path
            for dx, dy in DIRS:
                nx, ny = cx + dx, cy + dy
                if not (0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE):
                    continue
                if (nx, ny) in visited:
                    continue
                # Goal tile is always reachable
                if (nx, ny) == goal:
                    return path + [(nx, ny)]
                tile = self.get(nx, ny)
                cost = TILE_COST.get(tile)
                if cost is None:
                    continue          # Steel/Water → impassable, skip
                ng    = g + cost
                npath = path + [(nx, ny)]
                heapq.heappush(open_set, (ng + h(nx, ny), ng, (nx, ny), npath))
        return []

    def greedy_next_step(self, start, goal):
        """
        Greedy Best-First single-step decision.
        Does NOT compute a full path — simply picks the neighbour tile
        with the lowest Manhattan distance h(n) to the goal.
        Returns a 1-element list [(nx, ny)] or [] if stuck.
        
        Consequence: Can get stuck in local minima (e.g., surrounded by
        walls with one opening behind it). This is intentional — it shows
        WHY greedy search is not optimal.
        """
        sx, sy = start
        gx, gy = goal
        if (sx, sy) == (gx, gy):
            return []

        best_tile = None
        best_h    = float('inf')

        for dx, dy in DIRS:
            nx, ny = sx + dx, sy + dy
            if not (0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE):
                continue
            tile = self.get(nx, ny)
            # Can move through passable tiles or shoot through brick
            if tile in (EMPTY, FOREST, BRICK) or (nx, ny) == (gx, gy):
                h = abs(nx - gx) + abs(ny - gy)
                if h < best_h:
                    best_h    = h
                    best_tile = (nx, ny)

        if best_tile is not None:
            return [best_tile]
        return []  # stuck — no valid neighbours


# ─── Map Generator (CSP with Backtracking Attempts) ─────────────────────────────────────

class MapGenerator:
    """
    Generates a level map using CSP approach with backtracking attempts.
    Variables: tiles assigned via random selection with constraint checks.
    Backtracking: Retry generation if constraints violated.
    """

    def generate(self, level=1, seed=None):
        self.level = level
        self.rng = random.Random(seed)
        
        # Try backtracking attempts (up to 200)
        for attempt in range(200):
            tm = self._try_generate()
            if tm is not None:
                return tm
        
        # Fallback: open map
        tm = Tilemap()
        self._place_eagle_and_protection(tm)
        return tm

    def _try_generate(self):
        tm = Tilemap()

        # Level density parameters
        brick_prob  = 0.18 + self.level * 0.04   # more brick each level
        steel_prob  = 0.04 + self.level * 0.03
        water_prob  = 0.03
        forest_prob = 0.06

        # Clear area near spawn points and player
        protected = set()
        for sx, sy in ENEMY_SPAWNS:
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    protected.add((sx + dx, sy + dy))
        px, py = PLAYER_SPAWN
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                protected.add((px + dx, py + dy))

        # Fill grid randomly (CSP variable assignment)
        wall_count = 0
        total      = GRID_SIZE * GRID_SIZE
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if (x, y) in protected:
                    continue
                if (x, y) == EAGLE_POS:
                    continue
                r = self.rng.random()
                if r < brick_prob:
                    tm.set(x, y, BRICK);  wall_count += 1
                elif r < brick_prob + steel_prob:
                    tm.set(x, y, STEEL);  wall_count += 1
                elif r < brick_prob + steel_prob + water_prob:
                    tm.set(x, y, WATER)
                elif r < brick_prob + steel_prob + water_prob + forest_prob:
                    tm.set(x, y, FOREST)

        # Forward checking: density constraint
        if wall_count / total > 0.40:
            return None  # backtrack (try again)

        # Place Eagle and protect it
        self._place_eagle_and_protection(tm)

        # Final BFS reachability check
        for sp in ENEMY_SPAWNS:
            if not tm.reachable(sp, EAGLE_POS):
                return None  # backtrack

        return tm

    def _place_eagle_and_protection(self, tm):
        ex, ey = EAGLE_POS
        tm.set(ex, ey, EAGLE)
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                nx, ny = ex + dx, ey + dy
                if (nx, ny) != (ex, ey) and 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                    if tm.get(nx, ny) == EMPTY:
                        tm.set(nx, ny, BRICK)
