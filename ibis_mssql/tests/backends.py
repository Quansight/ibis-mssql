import os

import pytest
from ibis.tests.backend import Backend, RoundAwayFromZero

import ibis_mssql


class MSSQL(Backend, RoundAwayFromZero):
    check_dtype = False
    supports_window_operations = False

    @staticmethod
    def skip_if_missing_dependencies() -> None:
        pytest.importorskip('pyodbc')

    @staticmethod
    def connect(data_directory: Path) -> ibis.client.Client:
        user = os.environ.get('IBIS_TEST_MSSQL_USER', 'sa')
        password = os.environ.get(
            'IBIS_TEST_MSSQL_PASSWORD', 'Ibis_MSSQL_2017'
        )
        host = os.environ.get('IBIS_TEST_MSSQL_HOST', 'mssql')
        port = os.environ.get('IBIS_TEST_MSSQL_PORT', 1433)
        database = os.environ.get('IBIS_TEST_MSSQL_DATABASE', 'master')
        return ibis_mssql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
        )
