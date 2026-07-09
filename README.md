*This project has been created as part of the 42 curriculum by lrain, agromano.*

# A-Maze-ing

## Description

A-Maze-ing generates a random (optionally *perfect*) maze from a configuration file,
writes it out in a hexadecimal wall format,
and renders it visually — walls, entry, exit, and the shortest solution path.
Every maze also hides a "42" pattern drawn by a block of fully closed cells.

The project is split in two, along the seam the subject defines
(see `docs/DIVISION.md`):

- **`mazegen` — the reusable engine** (`src/mazegen.py`):
  maze generation, solving, the "42" mask, braiding, and the validity guarantees.
  It is a single, standalone, `pip`-installable module
  with no dependency on the rest of the project.
- **`a_maze_ing.py` — the application**:
  the CLI, configuration parser, graceful error handling,
  hexadecimal output writer, and the interactive visual representation.
  It consumes the engine.

## Instructions

### Building & testing

Dependencies are managed with [`uv`](https://docs.astral.sh/uv/).
The `Makefile` wraps the common tasks:

```bash
make install      # install dependencies (uv sync)
make run          # run the app: python3 a_maze_ing.py config.txt
                  #   override the config with: make run CONFIG=other.txt
make run-mazegen  # run the engine standalone: python src/mazegen.py $(CONFIG)
make demo-mazegen # run the mazegen demo (tests/demo-mazegen.py)
make debug        # run the app under pdb
make test         # run the test suite (pytest)
make test-turnin  # lint-strict + tests
make test-all     # lint-all + tests
make lint         # flake8 + mypy (subject's mandatory flags)
make lint-strict  # flake8 + mypy --strict
make lint-all     # ruff + flake8 + mypy --strict
make mypy         # mypy with the subject's mandatory flags
make mypy-strict  # mypy --strict
make flake8       # flake8 (subject's required style checker)
make ruff         # ruff linter
make clean        # remove Python caches
make fclean       # clean + remove the dist/ tree
```

#### Building the reusable package

The engine ships as an installable package.
To build it from source into the repo root:

```bash
make build        # uv build, then copy the artifacts to the repo root
```

This produces `mazegen-1.0.0-py3-none-any.whl` and `mazegen-1.0.0.tar.gz`.
In a fresh virtual environment
you can then `pip install mazegen-1.0.0-py3-none-any.whl`
and `import mazegen` from anywhere.

### Usage

#### Using the `mazegen` engine

The engine is a single class, `MazeGenerator`, importable from `mazegen`.
Coordinates use `Cell(x, y)` tuples,
where `x` is the column and `y` is the row (with `y` growing downward).

```python
from mazegen import MazeGenerator, Cell

gen = MazeGenerator(
    width=20,
    height=15,
    entry=Cell(0, 0),
    exit=Cell(19, 14),
    perfect=True,   # False -> braided maze (loops, dead ends removed)
    seed=42,        # any seed reproduces the same maze; None for random
)
gen.generate()

# Access the generated structure:
grid = gen.grid          # immutable tuple-of-tuples snapshot, indexed grid[y][x]
hex_rows = gen.hex_grid  # one hex digit per cell, one string per row

# Access a solution:
path = gen.solve()       # shortest entry->exit path as "N"/"E"/"S"/"W" letters
```

##### The maze structure

Each cell stores its **closed** walls as a `Wall` bit flag:

| Bit | Direction | Value |
|-----|-----------|----------|
| 0 | North | `0b0001` |
| 1 | East | `0b0010` |
| 2 | South | `0b0100` |
| 3 | West | `0b1000` |

A bit **set** means the wall is **closed**;
a cleared bit means it is open.
Test with `Wall.<D> in cell` (e.g. `Wall.E in cell` is True when the east wall is closed).

Accessors:

- `grid` — an immutable tuple snapshot, safe for any caller
  (mutating the copy can't affect the maze).
- `live_grid` — the live backing storage, no copy (advanced / zero-copy use).
- `hex_grid` — the raw wall bits as one hexadecimal digit per cell.

The engine's internal structure is **not** the output-file format;
the application converts it (`int(cell)` → hex digit) when writing the output.

The constructor validates its parameters and raises `ValueError`
on non-positive dimensions, an out-of-bounds entry/exit, `entry == exit`,
or an entry/exit that would land on the "42" mask;
the application catches these.

#### Using a_maze_ing

##### Configuration file format

The application is run as `python3 a_maze_ing.py config.txt`.
The config file is plain text, one `KEY=VALUE` per line;
lines starting with `#` are comments and are ignored, as well as empty lines.
The mandatory keys are:

| Key | Description | Example |
|---------------|----------------------------|--------------------------|
| `WIDTH` | Maze width (cells) | `WIDTH=20` |
| `HEIGHT` | Maze height (cells) | `HEIGHT=15` |
| `ENTRY` | Entry coordinates `x,y` | `ENTRY=0,0` |
| `EXIT` | Exit coordinates `x,y` | `EXIT=19,14` |
| `OUTPUT_FILE` | Output filename | `OUTPUT_FILE=maze.txt` |
| `PERFECT` | Is the maze perfect? | `PERFECT=True` |

An additional "SEED" key can be added following the examples' format above to give a specific seed for the generator to create reproducible mazes.


Valid settings for the configuration file:
- Width and height: integers between 2 and 998.
- Entry and exit:
  Format: "x,y" where "x" can be an integer between zero and [*width* - 1] and "y" can be an integer between zero and [*height* - 1].
  Entry and exit must be different.
- Output file can have any name as far as the OS allows it.
- *Perfect* allows two options only: "True" or "False".
- Seed: Any integer.

A default configuration file is included. A backup is recommended before changing it.

##### Output file format

The maze is written with one hexadecimal digit per cell
(the wall-bit encoding above), rows one per line.
After a blank line, three lines follow:
the entry coordinates, the exit coordinates,
and the shortest entry-to-exit path as `N` / `E` / `S` / `W` letters.
All lines are `\n`-terminated.

> The output writer and its validation against `tests/output_validator.py`
> are part of the application layer.
> _To be completed by @agromano._

##### Visual representation

The visualiser simply parses the generated hexadecimal grid, translating every number to ASCII symbols, printing every cell's walls (or lack thereof) to a string. The algorithm checks which of each cell's four walls is closed or open and prints wall-like ASCII symbols or spaces respectively.

Using the shortest path string found by the generator, the visualiser can draw this solution too.
The path can be shown and hidden in the program.

There are five different colours available to choose from: red, green, yellow, blue and orange.

##### The program

How to use it:
- Customise the 'config.txt' file (optional).
- Type 'python3 a_maze_ing.py config.txt'.
- Choose one or more options.
- You can find the output file in the same directory corresponding to the latest generated maze ('output_maze.txt' by default).


Available options:
1: Generate or re-generate the maze.
  Unless there's no seed set, it will always show the same maze. It can be used after configuration file modification.
2: Toggle path.
  Shows or hides the shortest solution path.
3 to 12: Change colours.
13: Exit the program.


## Maze generation algorithm

The engine carves the maze with the **recursive backtracker**
(a randomized depth-first search),
implemented with an *explicit stack* rather than actual recursion
so deep mazes can't blow the Python call stack.

The maze starts fully walled.
From the entry cell we repeatedly:

1. look at the current cell's unvisited, in-bounds, non-masked neighbours;
1. if there is at least one, pick a random one,
   open the wall between the two cells
   (clearing the bit on **both** sides so neighbours stay coherent),
   and move there;
1. if there are none, pop the stack and backtrack
   until a cell with an unvisited neighbour is found;
1. stop when the stack is empty.

Randomness comes from a seeded `random.Random`,
so the **same seed reproduces the exact same maze**.

- **`perfect=True`** stops here:
  the carve is a spanning tree, so there is exactly one path between any two cells.
- **`perfect=False`** then runs a **braiding** pass:
  it visits dead ends in random order and opens one extra wall on each to create loops.
  After each opening it checks the affected neighbourhood
  and **reverts** the wall if it would produce a forbidden 3×3 fully-open area
  (the subject caps corridor width at 2).

The **"42" pattern** is placed as a mask before carving:
the cells forming the "4" and "2" glyphs are marked forced-closed,
and generation (and braiding) simply carve around them,
leaving them as an isolated, fully-walled block.
If the maze is too small to hold the glyphs,
the pattern is omitted and a notice is printed to stderr, as the subject allows.

The solver is a **breadth-first search** over open walls.
A FIFO queue guarantees that the first time the exit is dequeued
it was reached by a shortest path;
the path is then reconstructed from a `came_from` parent map
and encoded as direction letters.

### Why this algorithm

The recursive backtracker is simple, fast (linear in the number of cells),
and produces mazes with long, winding corridors and few short dead ends —
visually satisfying and a natural fit for a *perfect* maze,
since its carve is exactly a spanning tree.
Perfect mazes correspond directly to spanning trees in graph theory,
which makes the perfect-maze property trivial to guarantee
and easy to test (connectivity + exactly `cells − 1` open edges).
Braiding is then a small, optional post-pass
to get non-perfect mazes with loops, without changing the core generator.

## Reusability

`mazegen` is the reusable part of the project,
per Chapter VI of the documentation.
It is a **single standalone file** (`src/mazegen.py`)
with no dependency on the application,
and it builds into a standard `mazegen-*` wheel/sdist
(see *Building the reusable package* above).
Any other project can install it and use `MazeGenerator`
to generate a maze, read the structure through `grid` / `hex_grid`,
and get a shortest solution from `solve()` — the API documented above.
The output-file format is deliberately kept out of the engine
so consumers are free to serialise the structure however they need.

### Tests

The engine is covered by property-based tests (`pytest` + Hypothesis)
in `tests/test_mazegen.py`,
run over many random widths, heights, and seeds:

- **spanning tree** (perfect): flood-fill reaches every free cell,
  and the open edge count is exactly `free − 1` (connected, no cycles);
- **braided** (non-perfect): still fully connected,
  but with more edges than a tree (loops exist);
- **no 3×3 open area** anywhere;
- **wall coherence**: every shared wall agrees on both sides;
- **closed borders**: the external border stays walled;
- **reproducibility**: the same seed yields an identical grid;
- **valid solution**: `solve()` returns a path that only crosses open walls,
  reaches the exit, and is a shortest one.

The tests use an **independent** direction map (not the engine's `_DELTA`) on purpose,
so a bug in the engine's neighbour logic can't hide inside its own verifier.

## Team and project management

### Division of labor

Two-person team, split along the engine/application seam defined by the subject
(see `docs/DIVISION.md`):

**lrain:**

- the `mazegen` engine (`src/mazegen.py`)

  - generation
  - solving
  - the "42" mask
  - braiding + the 3×3 rule

- the mazegen test suite (`tests/test_mazegen.py`):

  - validity guarantees

- packaging

- Makefile.

**agromano:**

- the `a_maze_ing.py` application:
  - CLI
  - config parser
  - error handling
  - hexadecimal output writer
  - visual representation

The split was chosen so both halves can be built and tested independently
and only converge at integration:
the application can be developed against a hand-written maze fixture,
and the engine is self-contained
behind the `MazeGenerator` API and its own ASCII debug printer.

### Planning

Planning involved the technical discussion of how the project would be realized,
division of labor,
discussion of the milestones and timeline
and discussion of mazegen's API contract.

### After Action Review

#### Intent

- Regularly sync progress
- Clean split of labor,
  use of `mazegen` as the seam of the split
- No unnecessary duplication/reimplementations
- Completion of project on time
  with buffer for corrections
- Implementation of all requested features
- Adherence to coding standards as per the documentation

#### Performance

- Project was finished ahead of requested deadline,
  with more time to spare than even expected
- Testing didn't reveal any bugs before turn-in
- Codebase adhered to required guidelines
- Areas of work were split as intended,
  however code initially didn't work together
  and some features were implemented twice.
  This needed intervention across the agreed-upon work boundary

#### Learnings

- Timelining, sync meetings and rigorous project split all were good ideas
  that prevented frustration,
  time crunch
  and minimized unnecessary extra work.
- Some practices and design decisions —
  like how `mazegen`'s API was meant to be used,
  or the purpose and format of the config file —
  went unspoken because we each assumed they were self-evident.
  They weren't:
  group members came in with differing mental models
  and levels of programming familiarity.

#### Future Improvements

- More explicit defining of APIs and contracts
- Increased documenting and codifying of EXACT API usage into documentation
  at the start of the project
- Optionally: increased frequency of syncs to tighten up development cycle

### Tools used

- **uv** —
  project manager:
  drop in replacement for pip,
  while being more modern and
  faster.
  Eliminates the need for manually setting up and using virtual envs
- **hatchling** (build backend) —
  minimal, `pyproject.toml`-only backend with precise per-target file
  selection: it lets the wheel ship exactly `mazegen.py` (`only-include`)
  imported as top-level `mazegen` (`sources = ["src"]`), while the sdist
  bundles the pyproject separately — satisfying the single-file packaging
  requirement without `setup.py` boilerplate.
- **pytest** —
  low-boilerplate test runner: plain `assert` statements, automatic test
  discovery, and readable failure output, with `make test` wrapping it.
- **hypothesis** —
  property-based testing: instead of hand-picking cases, it generates many
  random widths, heights, and seeds and checks invariants (spanning tree,
  wall coherence, closed borders, valid solution), shrinking any failure to a
  minimal reproducing example.
- **ruff** —
  formatter and linter:
  additional checks,
  faster and more versatile than comparable tools

## Resources

### References

[1] Astral Software Inc., astral-sh/ruff. (Jul. 05, 2026). Rust. Astral.
Accessed: Jul. 05, 2026. [Online]. Available:
https://github.com/astral-sh/ruff

[2] Astral Software Inc., astral-sh/uv. (Jul. 05, 2026). Rust. Astral.
Accessed: Jul. 05, 2026. [Online]. Available: https://github.com/astral-sh/uv

[3] O. Lev, hatchling: Modern, extensible Python build backend. Python.
Accessed: Jul. 05, 2026. [OS Independent]. Available:
https://hatch.pypa.io/latest/

[4] D. R. MacIver, Z. Hatfield-Dodds, and many other contributors,
Hypothesis: A new approach to property-based testing. (Nov. 2019). Python.
doi: 10.21105/joss.01891.

[5] H. Krekel and pytest-dev team, "pytest documentation," pytest
documentation. Accessed: Jul. 05, 2026. [Online]. Available:
https://docs.pytest.org/en/stable/

[6] F. Bruhin, F. Bruynooghe, H. Krekel, B. Laugher, B. Oliveira, and
R. Pfannschmidt, pytest-dev/pytest. (Jul. 05, 2026). Python. pytest-dev.
Accessed: Jul. 05, 2026. [Online]. Available:
https://github.com/pytest-dev/pytest

[7] Hypothesis team, "Quickstart - Hypothesis 6.156.1 documentation,"
Hypothesis 6.156.1 documentation. Accessed: Jul. 05, 2026. [Online].
Available: https://hypothesis.readthedocs.io/en/latest/quickstart.html

[8] Hypothesis team, "Strategies Reference - Hypothesis 6.156.1
documentation," Hypothesis 6.156.1 documentation. Accessed: Jul. 05, 2026.
[Online]. Available:
https://hypothesis.readthedocs.io/en/latest/reference/strategies.html#hypothesis.strategies.integers

[9] TextToolbox, "Line & box drawing symbols"
Convenient website to copy ASCII characters. Accessed: Jun. 27, 2026. [Online] Available:
https://texttoolbox.net/line-box-drawing-symbols/

[10] GitHub, Inc., "Choose an open source license"
Accessed: Jul. 09, 2026. [Online]. Available:
https://choosealicense.com/

### AI usage

Claude Opus 4.8, Duck AI and Perplexity
were used mainly for gruntwork tasks, like:

- Refactoring (e.g. update argument structures of functions across files)
- Editing/correcting sections of the README
- Convert Zotero's reference formatting to markdown
- General concept explanations.
