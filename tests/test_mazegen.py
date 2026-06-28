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


def bfs_distance(gen: MazeGenerator) -> int:
    """Shortest hop count entry->exit through open walls (independent BFS)."""
    grid = gen.grid
    dist = {gen.entry: 0}
    q = deque([gen.entry])
    while q:
        c = q.popleft()
        if c == gen.exit:
            return dist[c]
        for wall, (dx, dy) in DELTA.items():
            if wall not in grid[c.y][c.x]:  # passage open this way
                n = Cell(c.x + dx, c.y + dy)
                if (
                    n not in dist
                    and 0 <= n.x < gen.width
                    and 0 <= n.y < gen.height
                ):
                    dist[n] = dist[c] + 1
                    q.append(n)
    raise AssertionError("exit unreachable")  # connectivity is tested apart


@given(
    w=strat.integers(min_value=9, max_value=100),
    h=strat.integers(min_value=7, max_value=100),
    seed=strat.integers(min_value=0, max_value=10**6),
)
def test_is_perfect(w: int, h: int, seed: int) -> None:
    gen = build(w, h, seed)

    # masked cells aren't carved, so the tree spans only the free cells
    free = w * h - len(gen.mask)
    # if and only if both of these are true do we have a spanning tree
    assert reachable_count(gen) == free
    assert edge_count(gen) == free - 1


@given(
    w=strat.integers(min_value=9, max_value=100),
    h=strat.integers(min_value=7, max_value=100),
    seed=strat.integers(min_value=0, max_value=10**6),
)
def test_is_imperfect(w: int, h: int, seed: int) -> None:
    gen = build(w, h, seed, perfect=False)

    free = w * h - len(gen.mask)
    # braiding never disconnects: still fully reachable
    assert reachable_count(gen) == free
    # braiding adds edges -> cycles -> more than a spanning tree
    assert edge_count(gen) > free - 1


@given(
    w=strat.integers(min_value=9, max_value=100),
    h=strat.integers(min_value=7, max_value=100),
    seed=strat.integers(min_value=0, max_value=10**6),
    perfect=strat.booleans(),
)
def test_no_3x3_open(w: int, h: int, seed: int, perfect: bool) -> None:
    grid = build(w, h, seed, perfect=perfect).grid
    for cy in range(h - 2):
        for cx in range(w - 2):
            # fully open iff no internal wall set anywhere in the block
            internal_open = all(
                (Wall.E not in grid[cy + j][cx + i] or i == 2)
                and (Wall.S not in grid[cy + j][cx + i] or j == 2)
                for j in range(3)
                for i in range(3)
            )
            assert not internal_open


@given(seed=strat.integers(min_value=0, max_value=10**6))
def test_reproducible(seed: int) -> None:
    assert build(20, 15, seed).grid == build(20, 15, seed).grid


@given(
    w=strat.integers(min_value=9, max_value=100),
    h=strat.integers(min_value=7, max_value=100),
    seed=strat.integers(min_value=0, max_value=10**6),
    perfect=strat.booleans(),
)
def test_wall_coherence(w: int, h: int, seed: int, perfect: bool) -> None:
    gen = build(w, h, seed, perfect=perfect)
    grid = gen.grid
    for y in range(h):
        for x in range(w):
            cell = grid[y][x]
            if x + 1 < w:  # my E wall must equal neighbour's W wall
                assert (Wall.E in cell) == (Wall.W in grid[y][x + 1])
            if y + 1 < h:  # my S wall must equal neighbour's N wall
                assert (Wall.S in cell) == (Wall.N in grid[y + 1][x])


@given(
    w=strat.integers(min_value=9, max_value=100),
    h=strat.integers(min_value=7, max_value=100),
    seed=strat.integers(min_value=0, max_value=10**6),
    perfect=strat.booleans(),
)
def test_closed_borders(w: int, h: int, seed: int, perfect: bool) -> None:
    # subject: entry/exit are cells, so the external border stays walled
    grid = build(w, h, seed, perfect=perfect).grid
    for x in range(w):
        assert Wall.N in grid[0][x]  # top edge
        assert Wall.S in grid[h - 1][x]  # bottom edge
    for y in range(h):
        assert Wall.W in grid[y][0]  # left edge
        assert Wall.E in grid[y][w - 1]  # right edge


@given(
    w=strat.integers(min_value=9, max_value=100),
    h=strat.integers(min_value=7, max_value=100),
    seed=strat.integers(min_value=0, max_value=10**6),
    perfect=strat.booleans(),
)
def test_valid_solution(w: int, h: int, seed: int, perfect: bool) -> None:
    gen = build(w, h, seed, perfect=perfect)
    grid = gen.grid
    path = gen.solve()

    # letter -> (wall, delta), derived from the independent DELTA map
    step = {wall.name: (wall, d) for wall, d in DELTA.items()}

    cur = gen.entry
    for letter in path:
        wall, (dx, dy) = step[letter]
        # every step must cross an OPEN wall of the current cell
        assert wall not in grid[cur.y][cur.x]
        cur = Cell(cur.x + dx, cur.y + dy)
        # and never leave the grid
        assert 0 <= cur.x < w and 0 <= cur.y < h

    # the path must actually arrive at the exit...
    assert cur == gen.exit
    # ...and be a SHORTEST one (subject requires the shortest valid path)
    assert len(path) == bfs_distance(gen)
