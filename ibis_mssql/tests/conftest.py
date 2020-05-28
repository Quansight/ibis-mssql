import os

import pytest

import ibis_mssql


@pytest.fixture(scope='session')
def backend():
    user = os.environ.get('IBIS_TEST_MSSQL_USER', 'sa')
    password = os.environ.get('IBIS_TEST_MSSQL_PASSWORD', 'Ibis_MSSQL_2017')
    host = os.environ.get('IBIS_TEST_MSSQL_HOST', 'mssql')
    port = os.environ.get('IBIS_TEST_MSSQL_PORT', 1433)
    database = os.environ.get('IBIS_TEST_MSSQL_DATABASE', 'master')
    return ibis_mssql.connect(
        host=host, port=port, user=user, password=password, database=database,
    )


@pytest.fixture(scope='session')
def con(backend):
    return backend.connection


@pytest.fixture
def alltypes(backend):
    return backend.functional_alltypes


@pytest.fixture(scope='session')
def sorted_alltypes(alltypes):
    return alltypes.sort_by('id')


@pytest.fixture(scope='session')
def batting(backend):
    return backend.batting


@pytest.fixture(scope='session')
def awards_players(backend):
    return backend.awards_players


@pytest.fixture(scope='session')
def df(alltypes):
    return alltypes.execute()


@pytest.fixture(scope='session')
def sorted_df(df):
    return df.sort_values('id').reset_index(drop=True)


@pytest.fixture(scope='session')
def batting_df(batting):
    return batting.execute(limit=None)


@pytest.fixture(scope='session')
def awards_players_df(awards_players):
    return awards_players.execute(limit=None)
