
root-dir := justfile_directory()

name := "42-a-maze-ing"


src-dir := root-dir / "src"
dist-dir := root-dir / "dist"
stage-dir := dist-dir / name + "_turnin"


_default:
    @just -l


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# run
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# run the project entry point (defaults to src/a_maze_ing.py)
[group('run')]
run file="a_maze_ing.py":
    uv run python {{src-dir}}/{{file}}

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# dist
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# package a release tarball tagged with the given version
[group('dist')]
publish tag msg:
    just dist {{tag}}
    just tag {{tag}} {{msg}}
    git push origin HEAD:refs/heads/main --tags
    gh release create {{tag}} {{dist-dir}}/{{name}}_turnin_{{tag}}.tar.gz


# checks then stage + tarball
[group('dist')]
dist tag="":
    just checks-dist
    just stage
    tar -czf {{dist-dir}}/{{name}}_turnin_{{tag}}.tar.gz -C {{stage-dir}} .

# rsync turnin files
[group('dist')]
stage:
    mkdir -p {{stage-dir}}
    rsync -vhacP --filter=':- .gitignore' src/ {{stage-dir}}/


# create tag for latest commit
[group('dist')]
tag name msg:
    #!/usr/bin/env nu
    if (git tag -l {{name}}| is-empty) {git tag {{name}} -m "{{msg}}"}

# type-check + style
[group('dist')]
checks-dist:
    just test-mypy
    just test-lint
    @printf '\033[1;32m✓ all checks passed! Ready for submission\n\033[0m\n'


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# test
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


# run mypy across src/
[group('test')]
test-mypy:
    uv run mypy --check-untyped-defs {{src-dir}}

# run ruff/flake8 across src/
[group('test')]
test-lint *args:
    uv run ruff check {{src-dir}} {{args}}

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# clean
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# remove python caches
[group('clean')]
clean:
    find {{src-dir}} -type d -name '__pycache__' -exec rm -rf {} +
    find {{src-dir}} -type f -name '*.pyc' -delete
    rm -rf {{root-dir}}/.mypy_cache {{root-dir}}/.ruff_cache 

# clean + remove dist tree
[group('clean')]
fclean: clean
    rm -rf {{dist-dir}}


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# tools
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

