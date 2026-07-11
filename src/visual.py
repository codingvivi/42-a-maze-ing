#!/usr/bin/env python3

import time
import os
from typing import NamedTuple
from mazegen import Cell


NORTH = 1  # 0001
EAST = 2  # 0010
SOUTH = 4  # 0100
WEST = 8  # 1000


class Maze(NamedTuple):
    width: int
    height: int
    entry_coor: Cell
    exit_coor: Cell
    cells: tuple[str, ...]
    shortest_path: str


# def load_output(path: str) -> Maze:
#     """Reads "output_maze.txt" and
#     loads the information into a tuple
#     to conveniently work with it.
#     """

#     with open(path) as o:
#         lines = tuple(line.rstrip("\n") for line in o)

#     blank_line = lines.index("")

#     grid_lines = lines[:blank_line]
#     width = len(lines[0])
#     height = blank_line
#     x, y = (int(axis) for axis in (lines[blank_line + 1].split(",")))
#     entry_coor = Cell(x, y)
#     x, y = (int(axis) for axis in (lines[blank_line + 2].split(",")))
#     exit_coor = Cell(x, y)
#     cells = tuple(list(row for row in grid_lines))
#     shortest_path = lines[blank_line + 3]

#     return Maze(width, height, entry_coor, exit_coor, cells, shortest_path)


def path_parser(
    shortest_path: str, col: int, row: int, maze_drawing: list[list[str]]
) -> list[list[str]]:
    """Walk the solution string, marking each step into the drawing.

    col/row start at the entry interior.
    North/South move the row (two char-rows per cell),
    East/West move the column;
    the index order is always maze_drawing[row][col].
    """

    for i, direction in enumerate(shortest_path):
        if direction == "N":
            for _ in range(2):
                row -= 1
                maze_drawing[row][col] = " ■ "
        elif direction == "S":
            for _ in range(2):
                row += 1
                maze_drawing[row][col] = " ■ "
        elif direction == "E":
            col += 1
            maze_drawing[row][col] = "■"
            col += 1
            maze_drawing[row][col] = " ■ "
        elif direction == "W":
            col -= 1
            maze_drawing[row][col] = "■"
            col -= 1
            maze_drawing[row][col] = " ■ "
        os.system('clear')
        print("".join(string for row in maze_drawing for string in row))
        time.sleep(0.02)
    return maze_drawing


def draw_path(
    maze: Maze, maze_drawing: list[list[str]]
) -> list[list[str]]:
    """Draw the solution path into the maze.

    Cell (x, y) lives at maze_drawing[2*y + 1][2*x + 1]:
    row first, column second,
    matching the engine's grid[y][x].
    """
    start_col = maze.entry_coor.x * 2 + 1
    start_row = maze.entry_coor.y * 2 + 1
    end_col = maze.exit_coor.x * 2 + 1
    end_row = maze.exit_coor.y * 2 + 1

    solved_maze = path_parser(
        maze.shortest_path, start_col, start_row, maze_drawing
    )
    solved_maze[end_row][end_col] = " E "
    solved_maze[start_row][start_col] = " S "

    return solved_maze


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

    maze_drawing = output

    start_col = maze.entry_coor.x * 2 + 1
    start_row = maze.entry_coor.y * 2 + 1
    end_col = maze.exit_coor.x * 2 + 1
    end_row = maze.exit_coor.y * 2 + 1

    maze_drawing[start_row][start_col] = " S "
    maze_drawing[end_row][end_col] = " E "

    return maze_drawing


def colourify(raw_maze: list[list[str]], colour: int) -> list[list[str]]:
    """Gives colour to the maze."""
    colours = (
        "\033[0m", "", "",
        "\033[91m",
        "\033[92m",
        "\033[93m",
        "\033[94m",
        "\033[38;2;255;165;0m",
    )
    #    RED = '\033[91m'
    #    GREEN = '\033[92m'
    #    YELLOW = '\033[93m'
    #    BLUE = '\033[94m'
    #    ORANGE = '\033[38;2;255;165;0m'
    #    RESET = '\033[0m'
    colourful_maze = [
        [f"{colours[colour]}{wall}{colours[0]}" for wall in row]
        for row in raw_maze
    ]
    return colourful_maze


class Mask:
    """Contains methods related to the painting and colouting of the mask."""
    #def __init__(self, cells: list[Cell], colour: int) -> None:
        #self.first_cell: tuple[int, int] = find_mask(
        #self.colour: int = colour


    def _find_mask(self, cells: tuple[str, ...]) -> tuple[int, int]:
        """Finds the first closed cell, which corresponds to the mask."""
        row: int = 0

        for row_of_cells in cells:
            col = 0
            for cell in row_of_cells:
                if cell == "F" or cell == "f":
                    return [row * 2 + 1, col * 2 + 1]
                col += 1
            row += 1
        return [-1, -1]


    def _fill_cells(self, first_cell: tuple[int, int], maze_drawing: list[list[str]]) -> list[list[str]]:
        """'Fills' the closed cells corresponding to the mask.
         Walks a path that goes inside each cell that is part of the mask,
         changing its content. 'J' is the jump the parser has to do
         from the '4' to the '2'.
        """
        row = first_cell[0]
        col = first_cell[1]

        maze_drawing[row][col] = "███"
        for direction in "SSEESSJWWNNEENNWW":
            if direction == "N":
                    row -= 2
                    maze_drawing[row][col] = "███"
            elif direction == "S":
                    row += 2
                    maze_drawing[row][col] = "███"
            elif direction == "E":
                col += 2
                maze_drawing[row][col] = "███"
            elif direction == "W":
                col -= 2
                maze_drawing[row][col] = "███"
            elif direction == "J":
                col += 8
                maze_drawing[row][col] = "███"
        return maze_drawing

    def paint(self, cells: tuple[str, ...], maze_drawing: list[list[str]], mask_colour: int) -> list[list[str]]:
        """Paints the mask with the specified colour.
         It must be done after the rest of
         the maze has already been painted.
        """
        colours = (
            "\033[0m", "", "", "", "", "", "", "",
            "\033[91m",
            "\033[92m",
            "\033[93m",
            "\033[94m",
            "\033[38;2;255;165;0m",
        )
        #    RED = '\033[91m'
        #    GREEN = '\033[92m'
        #    YELLOW = '\033[93m'
        #    BLUE = '\033[94m'
        #    ORANGE = '\033[38;2;255;165;0m'
        #    RESET = '\033[0m'

        first_cell = self._find_mask(cells)
        if first_cell == [-1, -1]:
            return maze_drawing

        colourful_maze = self._fill_cells(first_cell, maze_drawing)
        colourful_mask = [
                [f"{colours[mask_colour]}{string}{colours[0]}" if string == "███"
                else string
                for string in row]
                for row in colourful_maze
        ]
        return colourful_mask


if __name__ == "__main__":
    print()
    maze = load_output("output_maze.txt")
    print(maze)
    print()
    str_maze = show_options(maze)
    print(str_maze)
    print()
