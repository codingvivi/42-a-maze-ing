"""Reusable maze generation and solving on a rectangular grid.

This module exposes :class:`MazeGenerator`, an importable maze engine that
carves a maze over a grid of wall-bit cells and solves it. Each cell stores
its closed walls as a :class:`Wall` bit flag; coordinates use :class:`Cell`
``(x, y)`` tuples, with ``y`` growing downward (so North is ``y - 1``).

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
    """A point in the grid; ``x`` is the column, ``y`` is the row."""

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
#  MazeGenerator                                                              #
#                                                                             #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #


class MazeGenerator:
    """Generate and solve mazes on a rectangular grid of wall-bit cells.

    The maze starts fully walled and passages are carved by opening walls.
    Coordinates use :class:`Cell` ``(x, y)`` with ``y`` growing downward.

    Attributes:
        width: Maze width in cells.
        height: Maze height in cells.
        entry: Entry cell.
        exit: Exit cell.
        perfect: Whether the maze has exactly one path between any two cells.
        seed: Seed for reproducible generation, or ``None`` for random.
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
            entry: Entry cell; must be in bounds and differ from ``exit``.
            exit: Exit cell; must be in bounds and differ from ``entry``.
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

        self.entry: Cell = entry
        self.exit: Cell = exit
        if self.entry == self.exit:
            raise ValueError("Entry and exit must differ!")
        if not self._in_bounds(entry):
            raise ValueError(f"entry {entry} must be within bounds")
        if not self._in_bounds(exit):
            raise ValueError(f"exit {exit} must be within bounds")

        self._grid = [
            [ALL_CLOSED for _ in range(width)] for _ in range(height)
        ]

        self.perfect: bool = perfect
        self.seed: int | None = seed
        self._rng = random.Random(seed)

    @property
    def grid(self) -> tuple[tuple[Wall, ...], ...]:
        """Immutable snapshot of the maze grid (safe for any caller).

        Returns a fresh tuple-of-tuples copy, so mutating the result cannot
        affect the maze. Index it as ``grid[y][x]``. For zero-copy access,
        see :attr:`raw_grid`.
        """
        return tuple(tuple(row) for row in self._grid)

    @property
    def raw_grid(self) -> list[list[Wall]]:
        """The live internal grid, no copy.

        Returns the maze's actual backing storage for performance. Mutating
        it may break maze invariants (wall coherence, closed borders). Treat
        as read-only unless you know what you're doing! For a safe copy use
        :attr:`grid`. Index as ``raw_grid[y][x]``.
        """
        return self._grid

    # checks
    def _in_bounds(self, cell: Cell) -> bool:
        """Return True if ``cell`` lies inside the maze bounds."""
        return 0 <= cell.x < self.width and 0 <= cell.y < self.height

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
        assert self._in_bounds(neighbor), (
            f"_open_wall toward edge: {cell} -> {direction}"
        )
        self._grid[cell.y][cell.x] &= ~direction
        self._grid[neighbor.y][neighbor.x] &= ~_OPPOSITE[direction]

    # returns
    def _dump(self) -> None:
        """Print raw wall-bit values, one hex digit per cell."""
        for row in self._grid:
            print("".join(f"{int(c):x}" for c in row))

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
                if self._in_bounds(
                    neighbor := self._get_neighbor(curr_cell, direction)
                )
                and neighbor not in visited
            ]

            if not candidates:
                _ = current_path.pop()
                continue

            next_cell, direction = self._rng.choice(candidates)
            self._open_wall(curr_cell, direction)
            current_path.append(next_cell)
            visited.add(next_cell)

        # once done i should have traversed everything
        def _all_cells() -> set[Cell]:
            "Returns set of all cells, for checking"
            return {
                Cell(x, y)
                for y in range(self.height)
                for x in range(self.width)
            }

        assert len(visited) == self.width * self.height, (
            f"unvisited cells: {_all_cells() - visited}"
        )

    def solve(self) -> str:
        queue = deque([self.entry])
        came_from: dict[Cell, Cell | None] = {
            self.exit: None,
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


def _demo() -> None:
    """Build a maze and print it. Used for debugging purposes."""
    gen = MazeGenerator(
        width=20,
        height=15,
        entry=Cell(0, 0),
        exit=Cell(19, 14),
        perfect=True,
        seed=42,
    )
    gen._dump()
    gen.generate()
    print(gen._ascii_debug())


if __name__ == "__main__":
    _demo()
