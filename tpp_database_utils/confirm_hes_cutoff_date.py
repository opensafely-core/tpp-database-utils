def check(tpp_connection, expected_activity_month):
    """
    Check that all of the HES tables contain at least one row of data from the expected
    "activity month" (which is a string in YYYYMM format). The HES tables are split into
    live and archived tables, using this column to partition on. If the live/archive
    cutoff date changes such that the live table no longer contains data from the
    expected month we want to know about it.

    To minimise any possibility of data leakage via this method we expose only a single
    boolean result.
    """
    cursor = tpp_connection.cursor()
    for table in ["APCS", "EC", "OPA"]:
        cursor.execute(
            f"""
            SELECT
              CASE
                WHEN EXISTS (SELECT 1 FROM {table} WHERE Der_Activity_Month=%s)
                THEN 1
                ELSE 0
              END AS result
            """,
            [expected_activity_month],
        )
        result = cursor.fetchall()[0][0]
        if result == 0:
            return False
    return True
