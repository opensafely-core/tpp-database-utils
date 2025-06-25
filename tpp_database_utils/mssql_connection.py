import os
from urllib.parse import unquote, urlparse

import pymssql


def mssql_connection_params_from_url(url):
    parsed = urlparse(url)
    if parsed.scheme != "mssql" and not parsed.scheme.startswith("mssql+"):
        raise ValueError(f"Wrong scheme for MS-SQL URL: {url}")
    return {
        "server": parsed.hostname,
        "port": parsed.port or 1433,
        "database": parsed.path.lstrip("/"),
        "user": unquote(parsed.username),
        "password": unquote(parsed.password),
    }


def pymssql_connect(database_url=None):
    database_url = os.environ.get("DATABASE_URL", database_url)
    if not database_url:
        raise ValueError("No DATABASE_URL configured")
    params = mssql_connection_params_from_url(database_url)
    return pymssql.connect(**params)
