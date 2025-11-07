#!/bin/bash
#
# Run without uv to avoid re-syncing. Dependencies are installed in the
# docker image
coverage run --module pytest
coverage report || coverage html
