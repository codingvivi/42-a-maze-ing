#!/usr/bin/env python3


from typing import NamedTuple


NORTH = 1  # 0001
EAST = 2   # 0010
SOUTH = 4  # 0100
WEST = 8   # 1000


class Maze(NamedTuple):
    width: int
    height: int
    entry_coor: tuple[int, int]
    exit_coor: tuple[int, int]
    cells: tuple[str, ...]
    shortest_path: str


def load_output(path: str) -> Maze:
    """Reads "output_maze.txt" and
     loads the information into a tuple
     to conveniently work with it.
    """

    with open(path) as o:
        lines = tuple(line.rstrip("\n") for line in o)

    blank_line = lines.index("")

    grid_lines = lines[:blank_line]
    width = len(lines[0])
    height = blank_line
    x, y = (int(axis) for axis in (
        lines[blank_line + 1].split(",")
    ))
    entry_coor = (x, y)
    x, y = (int(axis) for axis in (
        lines[blank_line + 2].split(",")
    ))
    exit_coor = (x, y)
    cells = tuple(list(row for row in grid_lines))
    shortest_path = lines[blank_line + 3]

    return Maze(
            width,
            height,
            entry_coor,
            exit_coor,
            cells,
            shortest_path
    )


def path_parser(
        shortest_path: str,
        x_path: int,
        y_path: int,
        maze_drawing: list[list[str]]
) -> list[list[str]]:
    """Parser logic for path drawing."""

    for direction in shortest_path:
        if direction == "N":
            for _ in range(2):
                y_path -= 1
                maze_drawing[y_path][x_path] = " ■ "
        elif direction == "E":
            x_path += 1
            maze_drawing[y_path][x_path] = "■"
            x_path += 1
            maze_drawing[y_path][x_path] = " ■ "
        elif direction == "S":
            for _ in range(2):
                y_path += 1
                maze_drawing[y_path][x_path] = " ■ "
        elif direction == "W":
            x_path -= 1
            maze_drawing[y_path][x_path] = "■"
            x_path -= 1
            maze_drawing[y_path][x_path] = " ■ "
    maze_drawing[y_path][x_path] = " E "
    return maze_drawing


def draw_path(
        maze_data: Maze,
        maze_drawing: list[list[str]]
) -> list[list[str]]:
    """Draws the solution path into the maze."""

    y_start = maze_data.entry_coor[0] * 2 + 1
    x_start = maze_data.entry_coor[1] * 2 + 1
    y_end = maze_data.exit_coor[0] * 2 + 1
    x_end = maze_data.exit_coor[1] * 2 + 1

    maze_drawing[x_start][y_start] = " S "
    maze_drawing[x_end][y_end] = " E "

    maze_drawing = path_parser(
            maze_data.shortest_path, x_start, y_start, maze_drawing
    )
    return maze_drawing


def gen_vis(maze: Maze) -> list[list[str]]:
    """Generates the visualisation.
    Every iteration loads the characters for
     a single cell's top left corner, north and west
     walls into a list of lists of strings.
    """

    x_cell: int = 0
    y_cell: int = 0
    y_char: int = 0
    height_in_chars = maze.height * 2 + 1
    output: list[list[str]] = [[] for _ in range(height_in_chars)]

    # x and y order is inverted
    for y_cell in range(maze.height):
        for x_cell in range(maze.width):
            cell: int = int(maze.cells[y_cell][x_cell], 16)

# this big chunk is JUST for junctions to look better
            if y_cell == 0:
                if x_cell == 0:
                    output[y_char].append("┏")
                elif cell & WEST:
                    output[y_char].append("┳")
                else:
                    output[y_char].append("━")
            elif x_cell == 0:
                if cell & NORTH:
                    output[y_char].append("┣")
                else:
                    output[y_char].append("┃")
            elif int(maze.cells[y_cell - 1][x_cell - 1], 16) & EAST:
                if int(maze.cells[y_cell - 1][x_cell - 1], 16) & SOUTH:
                    if cell & NORTH:
                        if cell & WEST:
                            output[y_char].append("╋")
                        else:
                            output[y_char].append("┻")
                    elif cell & WEST:
                        output[y_char].append("┫")
                    else:
                        output[y_char].append("┛")
                elif cell & NORTH:
                    if cell & WEST:
                        output[y_char].append("┣")
                    else:
                        output[y_char].append("┗")
                elif cell & WEST:
                    output[y_char].append("┃")
                else:
                    output[y_char].append(" ")
            elif int(maze.cells[y_cell - 1][x_cell - 1], 16) & SOUTH:
                if cell & NORTH:
                    if cell & WEST:
                        output[y_char].append("┳")
                    else:
                        output[y_char].append("━")
                elif cell & WEST:
                    output[y_char].append("┓")
                else:
                    output[y_char].append(" ")
            elif cell & NORTH:
                if cell & WEST:
                    output[y_char].append("┏")
                else:
                    output[y_char].append(" ")
            else:
                output[y_char].append(" ")

# top wall
            if cell & NORTH:
                output[y_char].append("━━━")
            else:
                output[y_char].append("   ")

# left wall
            if cell & WEST:
                output[y_char + 1].append("┃")
            else:
                output[y_char + 1].append(" ")
            output[y_char + 1].append("   ")

# maze's bottom walls
            if y_cell == maze.height - 1:
                if x_cell == 0:
                    output[y_char + 2].append("┗━━━")
                if x_cell == maze.width - 1:
                    output[y_char + 2].append("┛")
                elif cell & EAST:
                    output[y_char + 2].append("┻━━━")
                else:
                    output[y_char + 2].append("━━━━")

# maze's right walls
        if y_cell == 0:
            output[y_char].append("┓\n")
        elif cell & NORTH:
            output[y_char].append("┫\n")
        else:
            output[y_char].append("┃\n")
        output[y_char + 1].append("┃\n")

        y_char += 2

    return output


def colourify(raw_maze: list[list[str]], colour: int) -> list[list[str]]:
    """Gives colour to the maze."""
    colours = (
        '\033[0m',
        '\033[91m',
        '\033[92m',
        '\033[93m',
        '\033[94m',
        '\033[38;2;255;165;0m'
    )
#    RED = '\033[91m'
#    GREEN = '\033[92m'
#    YELLOW = '\033[93m'
#    BLUE = '\033[94m'
#    ORANGE = '\033[38;2;255;165;0m'
#    RESET = '\033[0m'
    colourful_maze = [[f"{colours[colour]}{wall}{colours[0]}" for wall in row] for row in raw_maze]

    return colourful_maze

def show_options(maze: Maze) -> str:
    """Wrapping function that takes input from user
     to choose a colour for the maze.
    """
    print("Choose a maze colour:")
    colour = int(input("1: RED - 2: GREEN - 3: YELLOW - 4: BLUE - 5: ORANGE\n"))
    solved_maze = draw_path(maze, colourify(gen_vis(maze), colour))
    return ''.join(string for row in solved_maze for string in row)
    # we just merged everything into a single string


if __name__ == "__main__":
    print()
    maze = load_output("output_maze.txt")
    print(maze)
    print()
    str_maze = show_options(maze)
    print(str_maze)
    print()
