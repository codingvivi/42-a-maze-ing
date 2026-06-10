from typing import NamedTuple


class Cell(NamedTuple):
    x: int
    y: int


class MazeGenerator:
    def __init__(
        self,
        width: int,
        height: int,
        entry: Cell,
        exit: Cell,
        perfect: bool,
        seed: int | None = None,
    ) -> None:
        self.width: int = width
        self.height: int = height
        self.entry: Cell = entry
        self.exit: Cell = exit
        self.perfect: bool = perfect
        self.seed: int | None = seed

        if not self._in_bounds(entry):
            raise ValueError(f"entry {entry} must be within bounds")
        if not self._in_bounds(exit):
            raise ValueError(f"exit {exit} must be within bounds")
        if self.entry == self.exit:
            raise ValueError("Entry and exit must differ!")

    def _in_bounds(self, cell: Cell) -> bool:
        return 0 <= cell.x < self.width and 0 <= cell.x < self.height

    def generate(self):
        pass

    def ascii_debug(self):
        pass


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
    print(gen.ascii_debug())  # your debug printer


if __name__ == "__main__":
    _demo()
