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

from collections.abc import Mapping
from enum import IntFlag
from typing import NamedTuple


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
        as read-only unless you know what you're doing; for a safe copy, use
        :attr:`grid`. Index as ``raw_grid[y][x]``.
        """
        return self._grid

    def _in_bounds(self, cell: Cell) -> bool:
        """Return True if ``cell`` lies inside the maze bounds."""
        return 0 <= cell.x < self.width and 0 <= cell.y < self.height

    def _dump(self) -> None:
        """Print raw wall-bit values, one hex digit per cell."""
        for row in self._grid:
            print("".join(f"{int(c):x}" for c in row))

    def generate(self) -> None:
        """Carve the maze in place. (Not yet implemented.)"""
        raise NotImplementedError

    def ascii_debug(self) -> str:
        """Return an ASCII rendering of the maze. (Not yet implemented.)"""
        raise NotImplementedError


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
    gen.generate()
    print(gen.ascii_debug())


if __name__ == "__main__":
    gen = MazeGenerator(
        width=8, height=5, entry=Cell(0, 0), exit=Cell(7, 4), perfect=True
    )
    gen._dump()
    # _demo()
