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


@pytest.fixture
def cleanup_coded_event_snomed_table(tpp_connection):
    yield
    with tpp_connection.cursor() as cursor:
        table = "CodedEvent_SNOMED"
        cursor.execute(
            f"""
                IF OBJECT_ID('{table}', 'U') IS NOT NULL
                    DROP TABLE {table}
                """
        )


def create_coded_event_snomed_table(tpp_connection):
    with tpp_connection.cursor() as cursor:
        table = "CodedEvent_SNOMED"
        cursor.execute(
            f"""
                IF OBJECT_ID('{table}', 'U') IS NOT NULL
                    DROP TABLE {table}

                CREATE TABLE {table} (
                    CodedEvent_ID INT,
                )
                """
        )


@pytest.mark.parametrize(
    "description,events,is_in_maintenance_mode,expected_build_count",
    [
        ("No events", [], False, 0),
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
            0,
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
            0,
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
            1,
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
            1,
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
            1,
        ),
        (
            "Multiple ongoing builds",
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
                (
                    "OpenSAFELY",
                    "2026-02-01T14:25:10",
                    "2026-02-01T14:25:10",
                    "9999-12-31T00:00:00",
                    None,
                ),
            ],
            True,
            2,
        ),
    ],
)
def test_in_maintenance_mode(
    tpp_connection,
    build_progress_factory,
    cleanup_coded_event_snomed_table,
    description,
    events,
    is_in_maintenance_mode,
    expected_build_count,
):
    create_coded_event_snomed_table(tpp_connection)
    for event in events:
        build_progress_factory(event)
    verify_build_progress_count(tpp_connection, events)

    mode, build_count = in_maintenance_mode(tpp_connection)
    assert mode is is_in_maintenance_mode, description
    assert build_count == expected_build_count


@pytest.mark.parametrize(
    "table_available,is_in_maintenance_mode", [(True, False), (False, True)]
)
def test_in_maintenance_mode_checks_coded_event_snomed_availability(
    tpp_connection,
    build_progress_factory,
    cleanup_coded_event_snomed_table,
    table_available,
    is_in_maintenance_mode,
):
    # Main build has started, SwapTables and CodedEvent_SNOMED events have not started yet
    # We are not in maintenance mode according to the BuildProgress table, but the final
    # check to ensure availability of the CodedEvent_SNOMED table can override this
    events = [
        (
            "OpenSAFELY",
            "2025-06-12T14:25:10",
            "2025-06-12T14:25:10",
            "9999-12-31T00:00:00",
            None,
        )
    ]
    for event in events:
        build_progress_factory(event)
    verify_build_progress_count(tpp_connection, events)

    if table_available:
        create_coded_event_snomed_table(tpp_connection)

    assert in_maintenance_mode(tpp_connection)[0] == is_in_maintenance_mode


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

    assert in_maintenance_mode(tpp_connection)[0] is True


def verify_build_progress_count(tpp_connection, events):
    cursor = tpp_connection.cursor()
    cursor.execute("select * from BuildProgress")
    cursor.fetchall()
    assert cursor.rowcount == len(events)
