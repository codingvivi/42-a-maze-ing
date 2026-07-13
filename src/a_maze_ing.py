#!/usr/bin/env python3

from mazegen import Cell, MazeGenerator
from visual import Maze, draw_path, gen_vis, colourify, Mask
from typing import NamedTuple
import sys
import os


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
        with open(filename, "r") as file:
            i = 0
            for line in file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                i += 1
                try:
                    key, value = line.split("=")
                    key = key.strip()
                    value = value.strip()
                    if key == "WIDTH":
                        width = int(value)
                        limit_checker(key, width, 2, 999)
                    elif key == "HEIGHT":
                        height = int(value)
                        limit_checker(key, height, 2, 999)
                    elif key == "ENTRY":
                        x = value.split(",")[0]
                        y = value.split(",")[1]
                        entry = Cell(int(x), int(y))
                    elif key == "EXIT":
                        x = value.split(",")[0]
                        y = value.split(",")[1]
                        exitc = Cell(int(x), int(y))
                    elif key == "OUTPUT_FILE":
                        output = value
                    elif key == "PERFECT":
                        if value == "True":
                            perfect = True
                        elif value == "False":
                            perfect = False
                        else:
                            raise ValueError("Invalid value!")
                    elif key == "SEED":
                        seed = int(value)
                    else:
                        raise ValueError("Invalid key!")
                except ValueError as e:
                    print(error_msg)
                    print(f"Couldn't understand {line!r}.")
                    sys.exit(f"({e!r})")
            expected_lines = 7
            if seed is None:
                expected_lines = 6
            if i > expected_lines:
                sys.exit(f"Configuration file has too many lines ({i}).")
    except FileNotFoundError:
        sys.exit(f"Error: Configuration file {filename!r} not found.")
    except Exception as e:
        sys.exit(f"Error while trying to read the configuration file: {e}")
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


def show_options() -> str:
    """Prints the available options to the standard output.
    Returns user's input as a string.
    """
    print()
    print("regen:       1")
    print("toggle path: 2")
    print()
    print("colour:  walls:  pattern:")
    print("red:         3       8")
    print("green:       4       9")
    print("yellow:      5       10")
    print("blue:        6       11")
    print("orange:      7       12")
    print()
    print("exit:        13")
    print()

    usr_i = input("Type your choice >> ")

    return usr_i


def input_handler(
    maze: Maze, usr_i: int, path: int, colours: tuple[int, int]
) -> Maze:
    """Does what the user commands (see show_options())."""
    maze_colour, mask_colour = colours
    mask = Mask()
    if usr_i == 1:
        maze = create()
    elif usr_i in range(3, 8):
        maze_colour = usr_i
    elif usr_i in range(8, 13):
        mask_colour = usr_i
    elif usr_i == 13:
        print("bye")
        sys.exit(0)

    solved_maze = colourify(gen_vis(maze), maze_colour)
    solved_maze = mask.paint(maze.cells, solved_maze, mask_colour)
    if path == 1:
        solved_maze = draw_path(maze, solved_maze)
    os.system("clear")

    print("".join(string for row in solved_maze for string in row))
    return maze


def create() -> Maze:
    """Loads config file, generates and
    sets the maze ready to print and
    creates the output file.
    """

    try:
        cfg = load_config(sys.argv[1])
    except FileNotFoundError:
        sys.exit(f"Error: Configuration file {sys.argv[1]!r} not found.")
    except Exception as e:
        sys.exit(f"Error while trying to read the configuration file: {e}")

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
    except Exception as e:
        sys.exit(f"Error while trying to load configuration: {e}")

    gen.generate()

    maze = Maze(
        width=cfg.wid,
        height=cfg.hei,
        entry_coor=cfg.ent,
        exit_coor=cfg.exi,
        cells=gen.hex_grid,
        shortest_path=gen.solve(),
    )

    try:
        with open(cfg.out, "w") as o:
            for row in gen.hex_grid:
                o.write(row.upper() + "\n")
            o.write("\n")
            o.write(str(cfg.ent[0]) + "," + str(cfg.ent[1]) + "\n")
            o.write(str(cfg.exi[0]) + "," + str(cfg.exi[1]) + "\n")
            o.write(gen.solve())
            o.write("\n")
    except Exception as e:
        print(f"There was an issue trying to create the output file:\n{e}")

    return maze


def main() -> None:
    """Orchestrator"""
    path: int = -1  # path isn't shown by default
    maze_colour: int = 7  # orange is the default colour because.
    mask_colour: int = 9  # green is mask's default colour
    print()
    print("   === A-MAZE-ING ===")
    print(">>> This is the way! <<<")
    print()
    if len(sys.argv) != 2:
        sys.exit("Correct syntax: 'a_maze_ing.py <config_file>'")
    maze = create()
    print("".join(string for row in gen_vis(maze) for string in row))
    while True:
        try:
            usr_i = int(show_options())
            if usr_i not in range(1, 14):
                raise ValueError("number not in valid range")
                continue
            if usr_i == 2:
                path *= -1
            elif usr_i in range(3, 8):
                maze_colour = usr_i
            elif usr_i in range(8, 13):
                mask_colour = usr_i
        except ValueError:
            print("Enter a valid number!")
            continue
        maze = input_handler(maze, usr_i, path, (maze_colour, mask_colour))


if __name__ == "__main__":
    main()
