default:
    @just --list

update:
    uv sync --upgrade --all-groups

format:
    uv run ruff format
    uv run ruff check --fix

lint:
    uv run ruff format --check
    uv run ruff check
    uv run ty check

test:
    uv run pytest

check: lint test

build:
    uv build
