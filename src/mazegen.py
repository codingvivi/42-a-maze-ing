"""Reusable maze generation and solving on a rectangular grid.

This module exposes MazeGenerator, an importable maze engine that
carves a maze over a grid of wall-bit cells and solves it. Each cell stores
its closed walls as a Wall bit flag; coordinates use Cell
(x, y) tuples, with y growing downward (so North is y - 1).

Example:
    >>> from mazegen import MazeGenerator, Cell
    >>> gen = MazeGenerator(
    ...     width=20, height=15,
    ...     entry=Cell(0, 0), exit=Cell(19, 14),
    ...     perfect=True, seed=42,
    ... )
    >>> gen.generate()
"""

import random
import sys
from collections import deque
from collections.abc import Mapping
from enum import IntFlag
from itertools import pairwise
from typing import NamedTuple

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
#                                                                             #
#  Public types                                                               #
#                                                                             #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #


# Note:
# x first, then y
class Cell(NamedTuple):
    """A point in the grid; x is the column, y is the row."""

    x: int
    y: int


class Wall(IntFlag):
    """Bit flags for the walls a cell can have, one bit per direction."""

    N = 0b0001
    E = 0b0010
    S = 0b0100
    W = 0b1000


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
#                                                                             #
#  Lookup tables                                                              #
#                                                                             #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
#
# For debugging
ALL_CLOSED = Wall.N | Wall.E | Wall.S | Wall.W

# Wall a neighbor shares
_OPPOSITE: Mapping[Wall, Wall] = {
    Wall.N: Wall.S,
    Wall.E: Wall.W,
    Wall.S: Wall.N,
    Wall.W: Wall.E,
}

# Offset used in calculating neighbor
# Represents a vector, so i didnt use Cell
_DELTA: Mapping[Wall, tuple[int, int]] = {
    Wall.N: (0, -1),
    Wall.E: (1, 0),
    Wall.S: (0, 1),
    Wall.W: (-1, 0),
}

# Reverse of _DELTA:
# which wall does a given step vector cross?
_WALL_FROM_DELTA: Mapping[tuple[int, int], Wall] = {
    delta: wall for wall, delta in _DELTA.items()
}

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
#                                                                             #
#  42 Mask                                                                    #
#                                                                             #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

Glyph = tuple[str, ...]

_FOUR: Glyph = (
    "X..",
    "X..",
    "XXX",
    "..X",
    "..X",
)

_TWO: Glyph = (
    "XXX",
    "..X",
    "XXX",
    "X..",
    "XXX",
)

_FONT: Mapping[str, Glyph] = {"4": _FOUR, "2": _TWO}


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
#                                                                             #
#  MazeGenerator                                                              #
#                                                                             #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #


class MazeGenerator:
    """Generate and solve mazes on a rectangular grid of wall-bit cells.

    The maze starts fully walled and passages are carved by opening walls.
    Coordinates use Cell (x, y) with y growing downward.

    Attributes:
        width: Maze width in cells.
        height: Maze height in cells.
        entry: Entry cell.
        exit: Exit cell.
        perfect: Whether the maze has exactly one path between any two cells.
        seed: Seed for reproducible generation, or None for random.
    """

    def __init__(
        self,
        width: int,
        height: int,
        entry: Cell,
        exit: Cell,
        perfect: bool,
        seed: int | None = None,
    ) -> None:
        """Build an empty, fully-walled maze and validate its parameters.

        Args:
            width: Number of cells horizontally; must be >= 1.
            height: Number of cells vertically; must be >= 1.
            entry: Entry cell; must be in bounds and differ from exit.
            exit: Exit cell; must be in bounds and differ from entry.
            perfect: If True, generate a perfect maze (single path).
            seed: Optional seed for reproducible generation.

        Raises:
            ValueError: If dimensions are non-positive, entry/exit are out
                of bounds, or entry equals exit.
        """
        self.width: int = width
        self.height: int = height
        if self.width < 1 or self.height < 1:
            raise ValueError(
                f"dimensions must be positive, got {self.width}x{self.height}"
            )

        self._mask_label: str = "42"
        self.mask: set[Cell] = self._build_mask()

        self.entry: Cell = entry
        self.exit: Cell = exit
        self._validate_entry_and_exit()

        self._grid: list[list[Wall]] = [
            [ALL_CLOSED for _ in range(width)] for _ in range(height)
        ]
        self._all_cells: set[Cell] = {
            Cell(x, y) for y in range(self.height) for x in range(self.width)
        }

        self.perfect: bool = perfect
        self.seed: int | None = seed
        self._rng = random.Random(seed)

    @property
    def grid(self) -> tuple[tuple[Wall, ...], ...]:
        """Immutable snapshot of the maze grid (safe for any caller).

        Returns a fresh tuple-of-tuples copy, so mutating the result cannot
        affect the maze. Index it as grid[y][x]. For zero-copy access,
        see live_grid.
        """
        return tuple(tuple(row) for row in self._grid)

    @property
    def live_grid(self) -> list[list[Wall]]:
        """The live internal grid, no copy.

        Returns the maze's actual backing storage for performance. Mutating
        it may break maze invariants (wall coherence, closed borders). Treat
        as read-only unless you know what you're doing! For a safe copy use
        grid. Index as live_grid[y][x].
        """
        return self._grid

    @property
    def hex_grid(self) -> tuple[str, ...]:
        """Get raw wall-bit values, one hex digit per cell."""
        rows: list[str] = [
            "".join(f"{int(cell):x}" for cell in row) for row in self._grid
        ]
        return tuple(rows)

    # checks
    def _is_in_bounds(self, cell: Cell) -> bool:
        """Return True if cell lies inside the maze bounds."""
        return 0 <= cell.x < self.width and 0 <= cell.y < self.height

    def _is_in_mask(self, cell: Cell) -> bool:
        """Return True if cell lies inside the maze mask."""
        return cell in self.mask

    def _validate_entry_and_exit(self) -> None:
        """Validate that entry and exit are usable cells.

        Raises:
            ValueError: If entry equals exit, either lies out of bounds, or
                either overlaps the maze mask.
        """
        if self.entry == self.exit:
            raise ValueError("Entry and exit must differ!")

        for name, cell in (("entry", self.entry), ("exit", self.exit)):
            if not self._is_in_bounds(cell):
                raise ValueError(f"{name} ({cell}) must be within bounds")
            if self._is_in_mask(cell):
                raise ValueError(
                    f"{name} ({cell}) overlaps the maze mask "
                    f"({self._mask_label})"
                )

    @staticmethod
    def _get_neighbor(cell: Cell, direction: Wall) -> Cell:
        "Return neighboring cell for given direction"
        dx, dy = _DELTA[direction]
        return Cell(cell.x + dx, cell.y + dy)

    @staticmethod
    def _get_direction(cell: Cell, neighbor: Cell) -> Wall:
        "Return the wall of cell that faces neighbor."
        delta = (neighbor.x - cell.x, neighbor.y - cell.y)
        direction = _WALL_FROM_DELTA.get(delta)
        assert direction is not None, f"{cell} and {neighbor} are not adjacent"
        return direction

    @staticmethod
    def _direction_letter(cell: Cell, neighbor: Cell) -> str:
        "Return the N/E/S/W letter of the step from cell to neighbor."
        name = MazeGenerator._get_direction(cell, neighbor).name
        assert name is not None  # a single wall member always has a name
        return name

    # methods

    def _open_wall(self, cell: Cell, direction: Wall) -> None:
        neighbor: Cell = self._get_neighbor(cell, direction)
        assert self._is_in_bounds(neighbor), (
            f"_open_wall toward edge: {cell} -> {direction}"
        )
        self._grid[cell.y][cell.x] &= ~direction
        self._grid[neighbor.y][neighbor.x] &= ~_OPPOSITE[direction]

    def _close_wall(self, cell: Cell, direction: Wall) -> None:
        """Re-close the wall on both sides (exact inverse of _open_wall).

        Used to revert a braid that opened a forbidden 3x3 area.
        """
        neighbor: Cell = self._get_neighbor(cell, direction)
        assert self._is_in_bounds(neighbor), (
            f"_close_wall toward edge: {cell} -> {direction}"
        )
        self._grid[cell.y][cell.x] |= direction
        self._grid[neighbor.y][neighbor.x] |= _OPPOSITE[direction]

    @staticmethod
    def _glyph_cells(glyph: Glyph, ox: int, oy: int) -> set[Cell]:
        "Return the glyph's 'X' cells offset to origin (ox, oy)."
        return {
            Cell(ox + gx, oy + gy)
            for gy, row in enumerate(glyph)  # {index, row} in glyph
            for gx, char in enumerate(row)  # {index, char} in row
            if char == "X"  # only the lit cells join the set
        }

    def _build_mask(self) -> set[Cell]:
        """Return the label's glyph cells, centered in this maze.

        When the maze is too small to hold the label, the pattern is
        omitted: an empty set is returned (so generation proceeds as a
        normal maze) and a notice is printed to stderr, per the subject.
        """
        label = self._mask_label

        glyphs: list[Glyph] = [_FONT[ch] for ch in label]
        gap: int = 1

        height_glyphs: int = max(len(g) for g in glyphs)
        widths_glyphs: list[int] = [len(g[0]) for g in glyphs]
        total_width: int = sum(widths_glyphs) + gap * (len(glyphs) - 1)

        min_w = total_width + 2
        min_h = height_glyphs + 2
        if self.width < min_w or self.height < min_h:
            print(
                f"maze too small for the {label!r} pattern "
                f"(needs at least {min_w}x{min_h}); "
                f"generating without it",
                file=sys.stderr,
            )
            return set()
        ox = (self.width - total_width) // 2
        oy = (self.height - height_glyphs) // 2

        mask: set[Cell] = set()
        x = ox
        for glyph, gw in zip(glyphs, widths_glyphs, strict=False):
            mask |= self._glyph_cells(glyph, x, oy)
            x += gw + gap

        return mask

    def generate(self) -> None:
        """Carve maze using "recursive" backtracking (stack based)."""
        current_path: list[Cell] = [self.entry]
        visited: set[Cell] = {self.entry}
        # explore a path with cells that have neighbors
        # if cell without neighbors is hit, backtrack until one is found
        # if no such cells exist, done.
        while current_path:
            curr_cell = current_path[-1]
            # get candidates and their dir
            candidates: list[tuple[Cell, Wall]] = [
                (neighbor, direction)
                for direction in Wall
                if self._is_in_bounds(
                    neighbor := self._get_neighbor(curr_cell, direction)
                )
                and neighbor not in visited
                and neighbor not in self.mask
            ]

            if not candidates:
                _ = current_path.pop()
                continue

            next_cell, direction = self._rng.choice(candidates)
            self._open_wall(curr_cell, direction)
            current_path.append(next_cell)
            visited.add(next_cell)

        if not self.perfect:
            self._braid()

    def _is_dead_end(self, cell: Cell) -> bool:
        "A cell with exactly one open wall (three closed)."
        return self._grid[cell.y][cell.x].bit_count() == 3

    def _is_3x3(self, cx: int, cy: int) -> bool:
        """Return True if the 3x3 block at top-left (cx, cy) is fully open.

        Tests all 12 internal walls of the block; the block is assumed to
        lie on-grid.
        """
        for y in range(cy, cy + 3):
            for x in range(cx, cx + 3):
                cell = self._grid[y][x]
                if x < cx + 2 and Wall.E in cell:  # edge to E neighbour closed
                    return False
                if y < cy + 2 and Wall.S in cell:  # edge to S neighbour closed
                    return False
        return True

    def _makes_3x3(self, a: Cell, b: Cell) -> bool:
        """Any on-grid 3x3 open block now containing cell a or b."""
        origins = {
            (cx, cy)
            for c in (a, b)
            for cx in range(c.x - 2, c.x + 1)
            for cy in range(c.y - 2, c.y + 1)
            if 0 <= cx <= self.width - 3
            if 0 <= cy <= self.height - 3
        }
        return any(self._is_3x3(cx, cy) for cx, cy in origins)  # . . . . .

    # . . n . .
    # . w a e .
    # . . s . .
    # . . . . .

    # s s s . . . .
    # s s s . . . .
    # s s S s X x .
    # s s s x x x .
    # x x X x X x .
    # x x x . . . .
    #
    # if s, then 0, 0
    # if e, then 0, -3
    # if w, then -3, -3
    # if n, then

    def _is_braidable(self, cell: Cell, direction: Wall) -> bool:
        """Return True if cell's wall toward direction may be opened.

        The neighbour must be in bounds, outside the mask, and the wall
        must still be closed.
        """
        neighbor = self._get_neighbor(cell, direction)

        return (
            self._is_in_bounds(neighbor)
            and neighbor not in self.mask
            and direction in self._grid[cell.y][cell.x]  # wall still closed
        )

    def _braid(self) -> None:
        """Open dead ends into loops, reverting any forbidden 3x3 area.

        Visits dead ends in random order; for each it opens one valid wall,
        then re-closes it if doing so created a 3x3 open area.
        """
        dead_ends: list[Cell] = [
            cell
            for cell in self._all_cells
            if self._is_dead_end(cell)
            if cell not in self.mask
        ]
        self._rng.shuffle(dead_ends)

        for cell in dead_ends:
            valid: list[Wall] = [
                direction
                for direction in Wall
                if self._is_braidable(cell, direction)
            ]
            if not valid:
                continue  # boxed in by border/mask: leave it a dead end

            target: Wall = self._rng.choice(valid)
            neighbor = self._get_neighbor(cell, target)

            self._open_wall(cell, target)

            if self._makes_3x3(cell, neighbor):
                self._close_wall(cell, target)  # revert

    def solve(self) -> str:
        """Return the shortest entry-to-exit path as N/E/S/W letters.

        Runs a breadth-first search over open walls (FIFO queue, so the
        first time exit is reached is via a shortest path), reconstructs
        the path from exit back to entry, and encodes each step.

        Returns:
            The direction letters from entry to exit, in order.
        """
        queue = deque([self.entry])
        came_from: dict[Cell, Cell | None] = {
            self.entry: None,
        }
        grid = self._grid
        while queue:
            curr = queue.popleft()
            if curr == self.exit:
                break
            for w, (dx, dy) in _DELTA.items():
                if w not in grid[curr.y][curr.x]:
                    next = Cell(curr.x + dx, curr.y + dy)
                    if (
                        next not in came_from
                        and 0 <= next.x < self.width
                        and 0 <= next.y < self.height
                    ):
                        came_from[next] = curr
                        if next == self.exit:
                            break
                        queue.append(next)
        # deque better for repeated prepends
        solution_cells: deque[Cell] = deque([self.exit])
        previous: Cell | None = came_from[self.exit]
        # trace steps from exit to entry
        while previous is not None:
            solution_cells.appendleft(previous)
            previous = came_from[previous]
        # write steps into string
        # name is attribute of an enum member. convenient!
        solution_str: str = "".join(
            self._direction_letter(curr, next)
            for curr, next in pairwise(solution_cells)
        )
        return solution_str

    def _ascii_debug(self) -> str:
        """Return an ASCII rendering of the maze. (debug version)"""

        lines: list[str] = []
        # for each cell vertically
        for y in range(self.height):
            # cel:
            #  +---+
            #  |   |
            #  +---+
            # Line spacing makes up for the missing two vertical chars.
            # After removing elements cells share:
            #  +---
            #  |
            roof = ""
            body = ""
            for x in range(self.width):
                cell = self._grid[y][x]
                roof += "+" + ("---" if Wall.N in cell else "   ")
                body += ("|" if Wall.W in cell else " ") + "   "
            # eastmost cell has no neighbors
            # add edge
            roof += "+"
            # and east wall
            last = self._grid[y][self.width - 1]
            body += "|" if Wall.E in last else " "
            # add to printout
            lines.append(roof)
            lines.append(body)

        # last line doesnt have neighbor cells bellow, thus:
        floor = ""
        for x in range(self.width):
            cell = self._grid[self.height - 1][x]
            floor += "+" + ("---" if Wall.S in cell else "   ")
        floor += "+"
        lines.append(floor)

        return "\n".join(lines)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
#                                                                             #
#  Entry point                                                                #
#                                                                             #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
