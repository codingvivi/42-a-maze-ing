#!/usr/bin/env python3


from typing import NamedTuple


NORTH = 1  # 0001
EAST = 2   # 0010
SOUTH = 4  # 0100
WEST = 8   # 1000

RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


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

            # the following line should be deleted not before
            # the next commented out chunk is complete
            output[y_char].append(" ")
#           if y_cell == 0:
#               if x_cell == 0:
#                   pass  # does this work as intended?
#               elif cell & WEST:
#                   output[x_char].append("┳")
#               else:
#                   output[x_char].append("━")
#           elif x_cell == 0:
#               if cell & NORTH:
#                   output[x_char].append("┣")
#               else:
#                   output[x_char].append("┃")
#           elif maze.cells[x_cell - 1][y_cell - 1] & EAST:

            if cell & NORTH:
                output[y_char].append("━━━")
            else:
                output[y_char].append("   ")

            if cell & WEST:
                output[y_char + 1].append("┃")
            else:
                output[y_char + 1].append(" ")
            output[y_char + 1].append("   ")
# not sure what i wanted to do here:
#           if y_cell == 0:
#               if x_char == maze.width - 1:
#                   output[x_char].append("┓")
#               elif cell & EAST:
#                   output[x_char].append("┳")
#               else:
#                   output[x_char].append("━")

#           if x_char == maze.width - 1:

#           if y_char == maze.height - 1:

        output[y_char].append("\n")
        output[y_char + 1].append("┃\n")
        y_char += 2
    output[y_char].append("┗━━━")
    # missing last char row connectors
    output[y_char].append("┛")

    return output


if __name__ == "__main__":
    print()
    maze = load_output("output_maze.txt")
    print(maze)
    print()
    raw_maze = gen_vis(maze)
    solved_maze = draw_path(maze, raw_maze)
    str_maze = ''.join(string for row in solved_maze for string in row)
    # we just merged everything into a single string
    print(str_maze)
    print()
