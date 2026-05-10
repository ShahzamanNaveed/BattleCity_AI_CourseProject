# Battle City — AL2002 AI Lab Project
### Spring 2026 | Sections 6A & 6B

---

## How to Run

```bash
cd battle_city
python main.py
```

**Requires Python 3.10+ and pygame:**
```bash
pip install pygame
```

---

## Controls

| Key       | Action       |
|-----------|-------------|
| W / ↑     | Move Up     |
| S / ↓     | Move Down   |
| A / ←     | Move Left   |
| D / →     | Move Right  |
| SPACE     | Fire bullet |
| ESC       | Quit        |
| ENTER     | Restart (on game over) |

---

## Project Structure

```
battle_city/
├── main.py         ← Game loop, spawning, collision resolution
├── constants.py    ← All config: tile types, speeds, colours, positions
├── tilemap.py      ← Module A: Map representation + BFS + A* + Map Generator
├── tanks.py        ← Module B: All tank types with AI agents
├── bullet.py       ← Bullet movement and wall collision
├── renderer.py     ← Pygame drawing: grid, tanks, bullets, HUD
└── README.md
```

---

## What's Implemented

### Module A — Map (CSP with Backtracking)
- 26×26 tile grid with 6 tile types: Empty, Brick, Steel, Water, Forest, Eagle
- CSP approach with backtracking attempts:
  - Variables: tiles assigned via random selection
  - Domains: {Empty, Brick, Steel, Water, Forest}
  - Backtracking: Retry if constraints violated (up to 200 attempts)
  - Forward checking: Density constraint checked during generation
  - Final BFS validation for reachability
  - ≤40% wall density
  - Protected spawn corridors

### Module B — Search & Agents

| Tank     | Agent Model      | Algorithm         | Behaviour                        |
|----------|-----------------|-------------------|----------------------------------|
| Basic    | Simple Reflex   | BFS               | Shortest open path to Eagle      |
| Fast     | Goal-Based      | Greedy Best-First | Rushes Eagle; may hit local minima |
| Armor    | Model-Based     | A*                | Cost-aware; retreats on 3rd hit  |
| Boss     | Adversarial     | Minimax + A-B     | Optimal play vs simulated player |

### Module C — Adversarial (completed)
- Boss tank uses Minimax with Alpha-Beta Pruning
- Depth 2-4 based on HP phases
- Simulates player responses for challenging gameplay

---

## What to Add Next

- [ ] Power Tank type (utility-based agent)
- [ ] Sprite assets / sound effects
- [ ] Power-ups (shield, speed boost, etc.)
- [ ] Score tracking and high-score persistence
- [ ] Level 3 Boss arena (12×12)
- [ ] Minimax performance report (node count with/without pruning)
