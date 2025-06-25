# All Dockerfiles should start from this base image
# Provide the TAG environment variable, or replace with the image version required
FROM ghcr.io/opensafely-core/base-docker:22.04 AS tpp-database-utils

# install uv
# https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
COPY --from=ghcr.io/astral-sh/uv:0.7.13 /uv /uvx /bin/

WORKDIR /app
# RUN mkdir /app

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

# copy the app into the docker image
COPY . /app

ENV UV_LINK_MODE=copy
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

ENTRYPOINT ["uv", "run", "tpp_database_utils/main.py"]
