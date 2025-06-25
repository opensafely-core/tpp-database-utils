import os

import pytest

from tpp_database_utils.mssql_connection import (
    mssql_connection_params_from_url,
    pymssql_connect,
)


def test_mssql_connection_params_from_url():
    url = "mssql://SA:Your_password123!@localhost:15785/Test_OpenCorona"
    params = mssql_connection_params_from_url(url)

    assert params["server"] == "localhost"
    assert params["port"] == 15785
    assert params["database"] == "Test_OpenCorona"
    assert params["user"] == "SA"
    assert params["password"] == "Your_password123!"


def test_mssql_connection_params_from_url_bad_url():
    url = "psql://user:password@opensafely.org:5432/corona"
    with pytest.raises(ValueError):
        mssql_connection_params_from_url(url)


def test_pymssql_connect_no_url(monkeypatch):
    os.environ.pop("DATABASE_URL")

    with pytest.raises(ValueError):
        pymssql_connect()
