#!/usr/bin/env python
import logging
import os
import warnings
import zipfile
from pathlib import Path

import click
import pandas as pd
import sqlalchemy as sa
from toolz import dissoc

SCRIPT_DIR = Path(__file__).parent.absolute()
DATA_DIR_NAME = 'ibis-testing-data'
DATA_DIR = Path(
    os.environ.get('IBIS_TEST_DATA_DIRECTORY', SCRIPT_DIR / DATA_DIR_NAME)
)

TEST_TABLES = ['functional_alltypes', 'diamonds', 'batting', 'awards_players']


def get_logger(name, level=None, format=None, propagate=False):
    logging.basicConfig()
    handler = logging.StreamHandler()

    if format is None:
        format = (
            '%(relativeCreated)6d '
            '%(name)-20s '
            '%(levelname)-8s '
            '%(threadName)-25s '
            '%(message)s'
        )
    handler.setFormatter(logging.Formatter(fmt=format))
    logger = logging.getLogger(name)
    logger.propagate = propagate
    logger.setLevel(
        level
        or getattr(logging, os.environ.get('LOGLEVEL', 'WARNING').upper())
    )
    logger.addHandler(handler)
    return logger


logger = get_logger(Path(__file__).with_suffix('').name)


def recreate_database(driver, params, **kwargs):
    url = sa.engine.url.URL(driver, **dissoc(params, 'database'))
    engine = sa.create_engine(url, **kwargs)

    with engine.connect() as conn:
        conn.execute('DROP DATABASE IF EXISTS {}'.format(params['database']))
        conn.execute('CREATE DATABASE {}'.format(params['database']))


def init_database(driver, params, schema=None, recreate=True, **kwargs):
    new_params = params.copy()
    new_params['username'] = new_params.pop('user', None)

    if recreate:
        recreate_database(driver, new_params, **kwargs)

    url = sa.engine.url.URL(driver, **new_params)
    engine = sa.create_engine(url, **kwargs)

    if schema:
        with engine.connect() as conn:
            # clickhouse doesn't support multi-statements
            for stmt in schema.read().split(';'):
                if len(stmt.strip()):
                    conn.execute(stmt)

    return engine


def read_tables(names, data_directory):
    for name in names:
        path = data_directory / '{}.csv'.format(name)

        params = {}

        if name == 'geo':
            params['quotechar'] = '"'

        df = pd.read_csv(str(path), index_col=None, header=0, **params)

        if name == 'functional_alltypes':
            df['bool_col'] = df['bool_col'].astype(bool)
            # string_col is actually dt.int64
            df['string_col'] = df['string_col'].astype(str)
            df['date_string_col'] = df['date_string_col'].astype(str)
            # timestamp_col has object dtype
            df['timestamp_col'] = pd.to_datetime(df['timestamp_col'])

        yield name, df


def convert_to_database_compatible_value(value):
    """Pandas 0.23 broke DataFrame.to_sql, so we workaround it by rolling our
    own extremely low-tech conversion routine
    """
    if pd.isnull(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    try:
        return value.item()
    except AttributeError:
        return value


def insert(engine, tablename, df):
    keys = df.columns
    rows = [
        dict(zip(keys, map(convert_to_database_compatible_value, row)))
        for row in df.itertuples(index=False, name=None)
    ]
    t = sa.Table(tablename, sa.MetaData(bind=engine), autoload=True)
    engine.execute(t.insert(), rows)


def insert_tables(engine, names, data_directory):
    for table, df in read_tables(names, data_directory):
        with engine.begin() as connection:
            insert(connection, table, df)


@click.group()
@click.option('--quiet/--verbose', '-q', default=False, is_flag=True)
def cli(quiet):
    if quiet:
        logger.setLevel(logging.ERROR)
    else:
        logger.setLevel(logging.INFO)


@cli.command()
@click.option(
    '--repo-url', '-r', default='https://github.com/ibis-project/testing-data'
)
@click.option('-d', '--directory', default=DATA_DIR)
def download(repo_url, directory):
    from plumbum.cmd import curl
    from shutil import rmtree

    directory = Path(directory)
    # download the master branch
    url = repo_url + '/archive/master.zip'
    # download the zip next to the target directory with the same name
    path = directory.with_suffix('.zip')

    if not path.exists():
        logger.info('Downloading {} to {}...'.format(url, path))
        path.parent.mkdir(parents=True, exist_ok=True)
        download = curl[url, '-o', path, '-L']
        download(
            stdout=click.get_binary_stream('stdout'),
            stderr=click.get_binary_stream('stderr'),
        )
    else:
        logger.info('Skipping download: {} already exists'.format(path))

    logger.info('Extracting archive to {}'.format(directory))

    # extract all files
    extract_to = directory.with_name(directory.name + '_extracted')
    with zipfile.ZipFile(str(path), 'r') as f:
        f.extractall(str(extract_to))

    # remove existent folder
    if directory.exists():
        rmtree(str(directory))

    # rename to the target directory
    (extract_to / 'testing-data-master').rename(directory)

    # remove temporary extraction folder
    extract_to.rmdir()


@cli.command()
@click.option('-h', '--host', default='localhost')
@click.option('-P', '--port', default=1433, type=int)
@click.option('-u', '--user', default='SA')
@click.option('-p', '--password', default='Ibis_MSSQL_2017')
@click.option('-D', '--database', default='master')
@click.option(
    '-S',
    '--schema',
    type=click.File('rt'),
    default=str(SCRIPT_DIR / '..' / 'schema.sql'),
)
@click.option('-t', '--tables', multiple=True, default=TEST_TABLES)
@click.option('-d', '--data-directory', default=DATA_DIR)
def mssql(schema, tables, data_directory, **params):
    data_directory = Path(data_directory)
    logger.info('Initializing MSSQL...')
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        params['query'] = {'driver': 'ODBC Driver 17 for SQL Server'}
        engine = init_database(
            'mssql+pyodbc',
            params,
            schema,
            connect_args={'autocommit': False},
            recreate=False,
        )
    insert_tables(engine, tables, data_directory)


if __name__ == '__main__':
    """
    Environment Variables are automatically parsed:
     - IBIS_TEST_{BACKEND}_PORT
     - IBIS_TEST_{BACKEND}_HOST
     - IBIS_TEST_{BACKEND}_USER
     - IBIS_TEST_{BACKEND}_PASSWORD
     - etc.
    """
    cli(auto_envvar_prefix='IBIS_TEST')
