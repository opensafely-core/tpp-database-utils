set dotenv-load := true

# list available commands
default:
    @"{{ just_executable() }}" --list

# clean up temporary files
clean:
    uv clean

# ensure valid virtualenv
virtualenv:
    uv venv

# ensure precommit is installed
install-precommit:
    uv run pre-commit install

# Upgrade all dev and prod dependencies.
# This is the default input command to update-dependencies action
# https://github.com/bennettoxford/update-dependencies-action
update-dependencies:
    uv sync

# *args is variadic, 0 or more. This allows us to do `just test -k match`, for example.
# Run the tests
test *args:
    uv run coverage run --module pytest {{ args }}
    uv run coverage report || uv run coverage html


format *args=".":
    uv run ruff format --check {{ args }}

lint *args=".":
    uv run ruff check {{ args }}

# run the various dev checks but does not change any files
check: format lint

# fix formatting and import sort ordering
fix:
    uv run ruff check --fix .
    uv run ruff format .

# Run the project locally
# Nb. you will probably need a relevant database server for this to be useful
run *args="":
    uv run tpp_database_utils/main.py {{ args }}
