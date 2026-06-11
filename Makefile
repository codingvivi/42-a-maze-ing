SRC_DIR := src
MAIN    := $(SRC_DIR)/a_maze_ing.py
MODULE  := $(SRC_DIR)/mazegen.py
CONFIG  ?= config.txt

MYPY_FLAGS := --warn-return-any --warn-unused-ignores --ignore-missing-imports \
              --disallow-untyped-defs --check-untyped-defs

.PHONY: install run debug \
        ruff flake8 mypy mypy-strict \
        lint lint-strict lint-all \
        clean fclean

# install project dependencies
install:
	uv sync

# run the main script (override the config with: make run CONFIG=other.txt)
run:
	uv run python $(MAIN) $(CONFIG)

# run module as a standalone file (for debugging purposes)
run-mazegen:
	uv run python $(MODULE) $(CONFIG)

# run the main script under the pdb debugger
debug:
	uv run python -m pdb $(MAIN) $(CONFIG)

# mypy with the subject's mandatory flags
mypy:
	uv run mypy $(MYPY_FLAGS) $(SRC_DIR)

# mypy in strict mode
mypy-strict:
	uv run mypy --strict $(SRC_DIR)

# flake8 (the subject's required style checker; run ephemerally via uvx)
flake8:
	uvx flake8 $(SRC_DIR)

# ruff linter
# (more throrough than flake8,
# and I (lrain) need it for my code editor anyway,
# so i might as well include optionally)
ruff:
	uv run ruff check $(SRC_DIR)


# subject's mandatory lint rule
lint: flake8 mypy

# subject's optional lint rule: flake8 + mypy --strict
lint-strict: flake8 mypy-strict

# run every linter we have: ruff + flake8 + mypy --strict
lint-all: ruff flake8 mypy-strict

# remove python caches
clean:
	find $(SRC_DIR) -type d -name '__pycache__' -exec rm -rf {} +
	find $(SRC_DIR) -type f -name '*.pyc' -delete
	rm -rf .mypy_cache .ruff_cache

# clean + remove the dist tree
fclean: clean
	rm -rf dist
