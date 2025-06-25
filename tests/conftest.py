import pytest

from tpp_database_utils.mssql_connection import pymssql_connect


@pytest.fixture(scope="module")
def tpp_connection():
    tpp_connection = pymssql_connect()
    yield tpp_connection
    tpp_connection.close()
