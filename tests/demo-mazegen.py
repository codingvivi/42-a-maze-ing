import visualisation
from mazegen import Cell, MazeGenerator


def _demo() -> None:
    """Build a maze and print it. Used for debugging purposes."""

    width = 20
    height = 15
    entry = Cell(1, 0)
    exit = Cell(19, 14)

    gen = MazeGenerator(
        width=width,
        height=height,
        entry=entry,
        exit=exit,
        perfect=True,
        seed=42,
    )
    gen.generate()

    maze = visualisation.Maze(
        width=width,
        height=height,
        entry_coor=entry,
        exit_coor=exit,
        cells=gen.hex_grid,
        shortest_path=gen.solve(),
    )

    str_maze = visualisation.show_options(maze)
    print(str_maze)


if __name__ == "__main__":
    _demo()
