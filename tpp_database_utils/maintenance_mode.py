import os


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
    """

    cursor = tpp_connection.cursor()
    cursor.execute(
        """
        SELECT TOP 1 EventStart, EventEnd
        FROM BuildProgress
        WHERE Event = 'OpenSAFELY'
        ORDER BY EventStart DESC
        """
    )
    latest_rebuild = cursor.fetchone()
    if not latest_rebuild:
        # No events at all, we can't be in maintenance mode
        return False

    rebuild_start, rebuild_end = latest_rebuild
    if rebuild_end.year < 9999:
        # Rebuild has completed therefore we aren't in maintenance mode
        return False

    cursor.execute(
        "SELECT Event FROM BuildProgress WHERE EventStart >= %s",
        rebuild_start,
    )
    current_events = {row[0] for row in cursor.fetchall()}

    # Env var allows quick change of start event logic if needed
    start_events = os.environ.get(
        "TPP_MAINTENANCE_START_EVENT", "Swap Tables,CodedEvent_SNOMED"
    ).split(",")

    # We start maintenance mode as soon as we see any of the "trigger" events
    # and then don't exit until the entire build is finished
    return bool(current_events.intersection(start_events))
