# Notes for developers

## System requirements

### just

Follow installation instructions from the [Just Programmer's Manual](https://just.systems/man/en/chapter_4.html) for your OS.

Add completion for your shell. E.g. for bash:
```bash
source <(just --completions bash)
```

Show all available commands
```bash
just
```

## Production environment

At the time of writing, the required environment variables will be provided by
the job-runner agent's [inject_db_secrets()](https://github.com/opensafely-core/job-runner/blob/a62ce3cc7277cfdbf689bea2e31d0123227a403c/jobrunner/agent/main.py#L336).

## Tests

Run the tests locally with:
```bash
docker compose up -d mssql
just test <args>
docker compose down mssql
```

Or run the tests in a local docker container with:
```bash
just test-docker
```

## Running locally

To run the commands as they would be run in production, you could:

```bash
# build the image
just build-docker

# start a db server:
docker compose up mssql

# run a command
export DATABASE_URL='mssql://SA:Your_password123!@localhost:15785/Test_OpenCorona'
export TEMP_DATABASE_NAME="OPENCoronaTempTables"
docker run --rm -e DATABASE_URL -e TEMP_DATABASE_NAME -t --network=host tpp-database-utils in_maintenance_mode
```
