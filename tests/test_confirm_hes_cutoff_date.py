import pytest

from tpp_database_utils import confirm_hes_cutoff_date


TABLES = ["APCS", "EC", "OPA"]


@pytest.fixture(scope="module")
def create_tables(tpp_connection):
    cursor = tpp_connection.cursor()
    for table in TABLES:
        cursor.execute(
            f"""
            IF OBJECT_ID('{table}', 'U') IS NOT NULL
                DROP TABLE {table}

            CREATE TABLE {table} (
                Der_Activity_Month VARCHAR(6)
            )
            """
        )
    yield
    for table in TABLES:
        cursor.execute(f"DROP TABLE {table}")


@pytest.fixture
def populate_tables(tpp_connection, create_tables):
    def _populate_tables(**kwargs):
        cursor = tpp_connection.cursor()
        for table, values in kwargs.items():
            assert table in TABLES
            cursor.executemany(
                f"INSERT INTO {table} VALUES (%s)",
                values,
            )

    yield _populate_tables

    cursor = tpp_connection.cursor()
    for table in TABLES:
        cursor.execute(f"TRUNCATE TABLE {table}")


@pytest.mark.parametrize(
    "expected,table_data",
    [
        (
            # True when all tables contain at least one instance of target month
            True,
            {
                "APCS": ["202301", "202304", "202305"],
                "EC": ["202301", "202304", "202305"],
                "OPA": ["202301", "202304", "202305"],
            },
        ),
        (
            # False if a single table does not contain the target month
            False,
            {
                "APCS": ["202301", "202304", "202305"],
                "EC": ["202301", "202304", "202305"],
                "OPA": ["202301", "202305"],
            },
        ),
        (
            # False if all tables empty
            False,
            {
                "APCS": [],
                "EC": [],
                "OPA": [],
            },
        ),
    ],
)
def test_confirm_hes_cutoff_date_check(
    tpp_connection, populate_tables, expected, table_data
):
    populate_tables(**table_data)
    assert confirm_hes_cutoff_date.check(tpp_connection, "202304") == expected
