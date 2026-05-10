"""Bullet — moves 1 tile per tick, resolves collisions in game loop."""

from constants import *


class Bullet:
    def __init__(self, x, y, direction, owner_type):
        self.x           = x
        self.y           = y
        self.dx, self.dy = direction
        self.owner_type  = owner_type   # TANK_PLAYER or enemy type
        self.alive       = True
        self.visible     = True
        self._move_tick  = 0
        self.speed       = 4            # ticks per tile move

    def update(self, tilemap, player, enemies):
        """Advance bullet one tile per speed tick, stopping on first collision."""
        if not self.alive:
            return
            
        self._move_tick += 1
        if self._move_tick >= self.speed:
            self._move_tick = 0
            if self._check_current(tilemap, player, enemies):
                return
            self._step(tilemap, player, enemies)

    def _check_current(self, tilemap, player, enemies):
        # Check collision at the current bullet position before moving.
        if self.owner_type == TANK_PLAYER:
            for e in enemies:
                if e.alive and e.x == self.x and e.y == self.y:
                    e.take_hit()
                    self.alive = False
                    self.visible = True
                    return True
        else:
            if player.alive and player.x == self.x and player.y == self.y:
                player.take_hit()
                self.alive = False
                self.visible = True
                return True

        t = tilemap.get(self.x, self.y)
        if t == BRICK:
            tilemap.destroy_brick(self.x, self.y)
            self.alive = False
            self.visible = True
            return True
        if t == STEEL or t == WATER or t == EAGLE:
            self.alive = False
            self.visible = True
            return True
        return False

    def _step(self, tilemap, player, enemies):
        nx = self.x + self.dx
        ny = self.y + self.dy
        t  = tilemap.get(nx, ny)

        # Bullet hits a tank first, before terrain rules
        if self.owner_type == TANK_PLAYER:
            for e in enemies:
                if e.alive and e.x == nx and e.y == ny:
                    e.take_hit()
                    self.x, self.y = nx, ny
                    self.alive = False
                    self.visible = True
                    return False
        else:
            if player.alive and player.x == nx and player.y == ny:
                player.take_hit()
                self.x, self.y = nx, ny
                self.alive = False
                self.visible = True
                return False

        if t == BRICK:
            tilemap.destroy_brick(nx, ny)
            self.x, self.y = nx, ny
            self.alive = False
            self.visible = True
            return False
        elif t == STEEL or t == WATER:
            self.x, self.y = nx, ny
            self.alive = False
            self.visible = True
            return False
        elif t == EAGLE:
            self.x, self.y = nx, ny
            self.alive = False
            self.visible = True
            return False
        elif t in (EMPTY, FOREST):
            self.x, self.y = nx, ny
            return True
        else:
            self.alive = False   # OOB or unknown
            return False

    @property
    def is_player_bullet(self):
        return self.owner_type == TANK_PLAYER

    def rect_xy(self):
        """Returns pixel centre for drawing."""
        px = self.x * TILE_SIZE + TILE_SIZE // 2
        py = self.y * TILE_SIZE + TILE_SIZE // 2
        
        # Smooth interpolation to next tile for visual flair
        if self._move_tick > 0 and self.speed > 0:
            px += int((self.dx * TILE_SIZE) * (self._move_tick / self.speed))
            py += int((self.dy * TILE_SIZE) * (self._move_tick / self.speed))
            
        return px, py
