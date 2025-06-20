#!/bin/bash
#
# This is the same as `just test` but doesn't require `just` inside the container

uv run coverage run --module pytest
uv run coverage report || uv run coverage html
