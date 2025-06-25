import os

import pytest

from tpp_database_utils.maintenance_mode import in_maintenance_mode


@pytest.fixture(scope="module")
def build_progress_table(tpp_connection):
    table = "BuildProgress"

    cursor = tpp_connection.cursor()
    cursor.execute(
        f"""
        IF OBJECT_ID('{table}', 'U') IS NOT NULL
            DROP TABLE {table}

        CREATE TABLE {table} (
            Event VARCHAR(50) COLLATE Latin1_General_CI_AS,
            BuildStart DATETIME,
            EventStart DATETIME,
            EventEnd DATETIME,
            Duration INT,
        )
        """
    )
    yield
    cursor.execute(f"""DROP TABLE {table}""")


@pytest.fixture
def build_progress_factory(tpp_connection, build_progress_table):
    def _build_progress(values):
        cursor = tpp_connection.cursor()
        cursor.executemany(
            "INSERT INTO BuildProgress VALUES (%s, %s, %s, %s, %s)",
            [values],
        )

    yield _build_progress

    tpp_connection.cursor().execute("DELETE FROM BuildProgress")


@pytest.mark.parametrize(
    "description,events,is_in_maintenance_mode",
    [
        ("No events", [], False),
        (
            "Historical finished maintenance mode",
            [
                (
                    "OpenSAFELY",
                    "2004-05-23T14:25:10",
                    "2004-05-23T14:25:10",
                    "2004-05-23T15:25:10",
                    60,
                ),
                (
                    "Swap Tables",
                    "2004-05-23T14:35:10",
                    "2004-05-23T14:35:10",
                    "2004-05-23T15:15:10",
                    40,
                ),
                (
                    "CodedEvent_SNOMED",
                    "2004-05-23T15:15:10",
                    "2004-05-23T15:15:10",
                    "2004-05-23T15:25:10",
                    10,
                ),
            ],
            False,
        ),
        (
            "Historical unfinished maintenance mode",
            [
                (
                    "OpenSAFELY",
                    "2005-06-12T14:25:10",
                    "2005-06-12T14:25:10",
                    "9999-12-31T00:00:00",
                    None,
                ),
                (
                    "Swap Tables",
                    "2005-06-12T14:25:10",
                    "2005-06-12T14:25:10",
                    "9999-12-31T00:00:00",
                    None,
                ),
                (
                    "OpenSAFELY",
                    "2024-05-23T14:25:10",
                    "2024-05-23T14:25:10",
                    "2004-05-23T15:25:10",
                    60,
                ),
                (
                    "Swap Tables",
                    "2024-05-23T14:35:10",
                    "2024-05-23T14:35:10",
                    "2024-05-23T15:15:10",
                    40,
                ),
                (
                    "CodedEvent_SNOMED",
                    "2024-05-23T15:15:10",
                    "2024-05-23T15:15:10",
                    "2024-05-23T15:25:10",
                    10,
                ),
            ],
            False,
        ),
        (
            "Inconsistent entries, assume maintenance for safety",
            [
                (
                    "OpenSAFELY",
                    "2024-05-23T14:25:10",
                    "2024-05-23T14:25:10",
                    "2004-05-23T15:25:10",
                    60,
                ),
                (
                    "Swap Tables",
                    "2024-05-23T14:35:10",
                    "2024-05-23T14:35:10",
                    "2024-05-23T15:15:10",
                    40,
                ),
                (
                    "CodedEvent_SNOMED",
                    "2024-05-23T15:15:10",
                    "2024-05-23T15:15:10",
                    "2024-05-23T15:25:10",
                    10,
                ),
                (
                    "OpenSAFELY",
                    "2024-05-23T14:25:10",
                    "2024-05-23T14:25:10",
                    "9999-12-31T00:00:00",
                    None,
                ),
                (
                    "Swap Tables",
                    "2024-05-23T14:25:10",
                    "2024-05-23T14:25:10",
                    "9999-12-31T00:00:00",
                    None,
                ),
            ],
            True,
        ),
        (
            "Swapping tables",
            [
                (
                    "OpenSAFELY",
                    "2025-06-12T14:25:10",
                    "2025-06-12T14:25:10",
                    "9999-12-31T00:00:00",
                    None,
                ),
                (
                    "Swap Tables",
                    "2025-06-12T14:25:10",
                    "2025-06-12T14:25:10",
                    "9999-12-31T00:00:00",
                    None,
                ),
            ],
            True,
        ),
        (
            "Building CodedEvent_SNOMED",
            [
                (
                    "OpenSAFELY",
                    "2025-06-12T14:25:10",
                    "2025-06-12T14:25:10",
                    "9999-12-31T00:00:00",
                    None,
                ),
                (
                    "Swap Tables",
                    "2025-06-12T14:25:10",
                    "2025-06-12T14:25:10",
                    "2025-06-12T15:00:00",
                    35,
                ),
                (
                    "CodedEvent_SNOMED",
                    "2025-06-12T15:00:00",
                    "2025-06-12T15:00:00",
                    "9999-12-31T00:00:00",
                    None,
                ),
            ],
            True,
        ),
    ],
)
def test_in_maintenance_mode(
    tpp_connection, build_progress_factory, description, events, is_in_maintenance_mode
):
    for event in events:
        build_progress_factory(event)
    verify_build_progress_count(tpp_connection, events)

    mode = in_maintenance_mode(tpp_connection)
    assert mode is is_in_maintenance_mode, description


def test_in_maintenance_mode_custom_event(tpp_connection, build_progress_factory):
    os.environ["TPP_MAINTENANCE_START_EVENT"] = "Custom event,Other"

    events = [
        (
            "OpenSAFELY",
            "2025-06-12T14:25:10",
            "2025-06-12T14:25:10",
            "9999-12-31T00:00:00",
            None,
        ),
        (
            "Custom event",
            "2025-06-12T14:25:10",
            "2025-06-12T14:25:10",
            "9999-12-31T00:00:00",
            None,
        ),
    ]

    for event in events:
        build_progress_factory(event)
    verify_build_progress_count(tpp_connection, events)

    assert in_maintenance_mode(tpp_connection) is True


def verify_build_progress_count(tpp_connection, events):
    cursor = tpp_connection.cursor()
    cursor.execute("select * from BuildProgress")
    cursor.fetchall()
    assert cursor.rowcount == len(events)
