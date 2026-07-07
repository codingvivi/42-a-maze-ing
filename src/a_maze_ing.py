#!/usr/bin/env python3

from mazegen import Cell, MazeGenerator
from visual import Maze, draw_path, gen_vis, colourify
from typing import NamedTuple
import sys


class Config(NamedTuple):
    wid: int
    hei: int
    ent: Cell
    exi: Cell
    out: str
    perf: bool
    seed: int | None


def limit_checker(key: str, n: int, min: int, max: int) -> None:
    """Checks for a number to be within given limits."""
    if n not in range(min, max + 1):
        sys.exit(f"Impossible maze parameter for {key}.")


def load_config(filename: str) -> Config:
    """Reads the config file and assigns the values to a usable tuple."""
    error_msg = "Configuration file has an invalid format."
    seed = None
    try:
        with open(filename, 'r') as file:
            i = 0
            for line in file:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                i += 1
                try:
                    key, value = line.split('=')
                    key = key.strip()
                    value = value.strip()
                    if key == "WIDTH":
                        width = int(value)
                        limit_checker(key, width, 2, 999)
                    elif key == 'HEIGHT':
                        height = int(value)
                        limit_checker(key, height, 2, 999)
                    elif key == 'ENTRY':
                        x = value.split(',')[0]
                        y = value.split(',')[1]
                        entry = Cell(int(x), int(y))
                    elif key == 'EXIT':
                        x = value.split(',')[0]
                        y = value.split(',')[1]
                        exitc = Cell(int(x), int(y))
                    elif key == 'OUTPUT_FILE':
                        output = value
                    elif key == 'PERFECT':
                        if value == "True":
                            perfect = True
                        elif value == "False":
                            perfect = False
                        else:
                            raise ValueError("Invalid value!")
                    elif key == 'SEED':
                        seed = int(value)
                    else:
                        raise ValueError("Invalid key!")
                except ValueError as e:
                    print(error_msg)
                    print(f"Couldn't understand {line!r}.")
                    sys.exit(f"({e!r})")
            expected_lines = 7
            if seed == None:
                expected_lines = 6
            if i > expected_lines:
                sys.exit(f"Configuration file has too many lines ({i}).")
    except FileNotFoundError:
        sys.exit(f"Error: Configuration file {filename!r} not found.")
    try:
        cfg = Config(width, height, entry, exitc, output, perfect, seed)
    except UnboundLocalError as e:
        sys.exit(f"There's at least one missing line in the config file: {e}")
    limit_checker("x-ENTRY", entry[0], 0, width - 1)
    limit_checker("y-ENTRY", entry[1], 0, height - 1)
    limit_checker("x-EXIT", exitc[0], 0, width - 1)
    limit_checker("y-EXIT", exitc[1], 0, height - 1)
    if entry == exitc:
        sys.exit("Start must be different than end.")
    return cfg


def show_options(maze: Maze) -> str:
    """Prints the available options to the standard output.
     Returns user's input as a string.
    """
    print()
    print("1: regen")
    print("2: toggle path")
    print(" walls colour:")
    print("3: red - 4: green - 5: yellow - 6: blue - 7: orange")
    print(" '42' colour:")
    print("8: red - 9: green - 10: yellow - 11: blue - 12: orange")
    print("13: exit")
    print()

    usr_i = input()

    return usr_i


def input_handler(maze: Maze, usr_i: int, path: int, colour: int) -> Maze:
    """Does what the user commands (see show_options())."""
    if usr_i == 1:
        maze = create()
    elif usr_i in range(8,13):
        exit("wip") # tbc
    elif usr_i == 13:
        exit("bye")

    solved_maze = colourify(gen_vis(maze), colour)
    if path == 1:
        solved_maze = draw_path(maze, solved_maze)

    print("".join(string for row in solved_maze for string in row))
    return maze


def create() -> Maze:
    """Loads config file, generates and
     sets the maze ready to print and
     creates the output file.
    """
    cfg = load_config(sys.argv[1])

    try:
        gen = MazeGenerator(
            width=cfg.wid,
            height=cfg.hei,
            entry=cfg.ent,
            exit=cfg.exi,
            perfect=cfg.perf,
            seed=cfg.seed,
        )
    except ValueError as e:
        sys.exit(f"Impossible maze parameter: {e}")
    
    gen.generate()

    maze = Maze(
        width=cfg.wid,
        height=cfg.hei,
        entry_coor=cfg.ent,
        exit_coor=cfg.exi,
        cells=gen.hex_grid,
        shortest_path=gen.solve(),
    )

    with open(cfg.out, "w") as o:
        for row in gen.hex_grid:
            o.write(row.upper() + "\n")
        o.write("\n")
        o.write(str(cfg.ent[0]) + "," + str(cfg.ent[1]) + "\n")
        o.write(str(cfg.exi[0]) + "," + str(cfg.exi[1]) + "\n")
        o.write(gen.solve())

    return maze


def main() -> None:
    """Orchestrator"""
    path = -1  # path isn't shown by default
    colour = 7 # orange is the default colour because.
    print()
    print("   === A-MAZE-ING ===")
    print(">>> This is the way! <<<")
    print()
    maze = create()
    while True:
        try:
            usr_i = int(show_options(maze))
            if usr_i not in range(1, 14):
                raise ValueError("number not in valid range")
                continue
            if usr_i == 2:
                path *= -1
            elif usr_i in range(3,8):
                colour = usr_i
        except ValueError as e:
            print("Enter a valid number!")
            continue
        maze = input_handler(maze, usr_i, path, colour)


if __name__ == "__main__":
    """"""

    main()