# Division of Work — A-Maze-ing

Two-person split along the seam the subject already defines: the reusable
`mazegen` engine (Chapter VI) vs. the `a_maze_ing.py` application that consumes
it (CLI, config, output file, visual representation).

## Shared — agree to be able for each other's code to interface

- **`MazeGenerator` API**: constructor params (`width, height, entry, exit, perfect, seed`) and accessors for the grid structure + the solution path.
- **Wall-bit convention**: bit 0 = N, 1 = E, 2 = S, 3 = W; closed = 1, open = 0.
- The engine's internal structure is *not* the hex output format — Person B
  converts.
- The "42" pattern and corridor-width ≤ 2 rules live with **Person A** (engine
  generates them); **Person B's** visual is the acceptance check.

## Person A — Engine / `mazegen` package

**Core generation**

- `MazeGenerator` class in a standalone, importable module.
- Recursive Backtracker generation (explicit stack, not recursion).
- Seeded reproducibility.
- `PERFECT=True` → single-path spanning tree.
- `PERFECT=False` → braiding / dead-end removal **with the 3×3 open-area
  rejection check**.
- "42" pattern via masking (forced-closed cells, carve around them) + the
  "maze too small, skip 42" error case.

**Solving & validity**

- BFS shortest-path solver, returning path as a list of cells/directions.
- Internal validity guarantees: full connectivity, no isolated cells, walls
  coherent between neighbours, border walls closed.

**Dev tooling or foundation**

- ASCII debug printer to eyeball mazes + overlay the solution while building.
  Coould be used as foundation for actual graphics

**Packaging**

- `pyproject.toml`, build `.tar.gz` + `.whl` as `mazegen-*` at repo root.
- Module-level docs + usage example (instantiate, custom params/seed, access
  structure + solution).

**Repo polish**

- README (description, instructions, resources/AI use, config format,
  algorithm + why, team roles/management).
- Makefile rules: install, run, debug, clean, lint (+ optional lint-strict).

## Person B — App / `a_maze_ing.py` program

**CLI & config**

- `a_maze_ing.py` entry point: `python3 a_maze_ing.py config.txt`.
- Config parser: KEY=VALUE, `#` comments ignored, the 6 mandatory keys.
- A default config file committed to the repo.

**Robustness**

- Graceful error handling end-to-end: file-not-found, bad syntax, impossible
  params, invalid entry/exit — clear messages, never crash.

**Output**

- Hex-per-cell output writer: grid rows → blank line → entry / exit / `NESW`
  path lines, all `\n`-terminated.
- Verify against `tests/output_validator.py`.

**Visual representation**

- Terminal ASCII
- Required interactions: regenerate, show/hide path, change wall colours,
  optional "42" colours.
- Clearly show walls, entry, exit, solution path.

## Independence check

- Person B can build and test the **config parser, error handling, and output
  writer** against a hand-written maze fixture — no dependency on A's finished
  engine.
- Person A is unblocked by owning the ASCII debug printer. Both only
  converge at the end, when B's visualizer + output writer plug into A's real
  engine.
