from collections import deque

from hypothesis import given
from hypothesis import strategies as strat

from mazegen import Cell, MazeGenerator, Wall

# Independent direction map, deliberately NOT mazegen's _DELTA
# bug in the engine's neighbour logic wont't hide inside test checking it
DELTA: dict[Wall, tuple[int, int]] = {
    Wall.N: (0, -1),
    Wall.E: (1, 0),
    Wall.S: (0, 1),
    Wall.W: (-1, 0),
}


def build(w: int, h: int, seed: int, perfect: bool = True) -> MazeGenerator:
    "Build generator for testing"
    gen = MazeGenerator(w, h, Cell(0, 0), Cell(w - 1, h - 1), perfect, seed)
    gen.generate()
    return gen


def reachable_count(gen: MazeGenerator) -> int:
    """Flood-fill through open walls, should reach same count."""
    seen = {gen.entry}
    q = deque([gen.entry])
    grid = gen.grid
    while q:
        c = q.popleft()
        for w, (dx, dy) in DELTA.items():
            if w not in grid[c.y][c.x]:  # passage open this way
                n = Cell(c.x + dx, c.y + dy)
                if (
                    n not in seen
                    and 0 <= n.x < gen.width
                    and 0 <= n.y < gen.height
                ):
                    seen.add(n)
                    q.append(n)
    return len(seen)


def edge_count(gen: MazeGenerator) -> int:
    """Count open passages (once, via E and S only)."""
    return sum(
        (Wall.E not in cell) + (Wall.S not in cell)
        for row in gen.grid
        for cell in row
    )


@given(
    w=strat.integers(min_value=9, max_value=100),
    h=strat.integers(min_value=7, max_value=100),
    seed=strat.integers(min_value=0, max_value=10**6),
)
def test_perfect_is_spanning_tree(w: int, h: int, seed: int) -> None:
    gen = build(w, h, seed)

    # masked cells aren't carved, so the tree spans only the free cells
    free = w * h - len(gen.mask)
    # if and only if both of these are true do we have a spanning tree
    assert reachable_count(gen) == free
    assert edge_count(gen) == free - 1


@given(seed=strat.integers(min_value=0, max_value=10**6))
def test_reproducible(seed: int) -> None:
    assert build(20, 15, seed).grid == build(20, 15, seed).grid
