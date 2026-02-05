import os

from pymssql.exceptions import ProgrammingError


def in_maintenance_mode(tpp_connection):
    """TPP Specific maintenance mode query.

    A BuildProgress table with the following columns:

        Event (VARCHAR) - A description of the event
        BuildStart (DATETIME) - When the overall build started
        EventStart (DATETIME) - When the event started
        EventEnd (DATETIME) - When the event ended
        Duration (INT) - The duration in minutes

    TPP will insert events for:
    - The overall build (Event = 'OpenSAFELY') - This will span the other events
    - Swapping the main tables (Event = 'Swap Tables')
    - Building the CodedEvent_SNOMED table (Event = 'CodedEvent_SNOMED')

    Events from the same overall build will have the same BuildStart value
    A row will be inserted when the event starts with EventEnd = 31 Dec 9999
    That row will be updated when the event ends to set EventEnd and Duration
    So the trigger to kill currently running jobs and prevent more from
    starting will be the presence of a 'Swap Tables' row with a Start but
    no End.

    The trigger to exit maintenance mode is when the final OpenSAFELY event
    finishes.

    Occasionally the build is slow (usually due to intensive concurrent DB queries),
    and the previous week's build does not complete before the next build starts. In
    this case we end up with two ongoing builds, so in order to determine DB status
    we need to check for ongoing SwapTables or CodedEvent_SNOMED events since the start
    of the earlier build. The presence of two ongoing builds is a flag for something
    that we want to alert on, so we also return the build count.
    """
    cursor = tpp_connection.cursor()
    # Select the TWO most recently started overall OpenSAFELY build events
    cursor.execute(
        """
        SELECT TOP 2 EventStart, EventEnd
        FROM BuildProgress
        WHERE Event = 'OpenSAFELY'
        ORDER BY EventStart DESC
        """
    )
    latest_rebuilds = cursor.fetchall()
    if not latest_rebuilds:
        # No events at all, we can't be in maintenance mode
        return False, 0

    # Of the two most recently started builds, iddentify those that are ongoing (i.e.
    # those with an end date of 9999-12-31)
    _, most_recent_end = latest_rebuilds[0]
    if most_recent_end.year < 9999:
        # The most recent build is complete, so we're not in maintenance mode, and any
        # previous build is a historical one which we can ignore
        return False, 0

    ongoing_builds = [rebuild for rebuild in latest_rebuilds if rebuild[1].year == 9999]
    build_count = len(ongoing_builds)

    # Check for incomplete events starting after the start of the earliest ongoing build
    earliest_build_start_date = min(ongoing_builds)[0]
    cursor.execute(
        "SELECT Event, EventEnd FROM BuildProgress WHERE EventStart >= %s",
        earliest_build_start_date,
    )
    current_events = {row[0] for row in cursor.fetchall() if row[1].year == 9999}

    # Env var allows quick change of start event logic if needed
    start_events = os.environ.get(
        "TPP_MAINTENANCE_START_EVENT", "Swap Tables,CodedEvent_SNOMED"
    ).split(",")

    in_maintenance_mode = bool(current_events.intersection(start_events))

    if not in_maintenance_mode:
        # According to the events, we're not in maintenance mode. As a final check,
        # make sure that the CodedEvent_SNOMED table really is available.
        try:
            cursor.execute("SELECT TOP 1 CodedEvent_ID FROM CodedEvent_SNOMED")
        except ProgrammingError:
            in_maintenance_mode = True

    # We start maintenance mode as soon as we see any of the "trigger" events
    # and then don't exit until the entire build is finished
    return in_maintenance_mode, build_count
