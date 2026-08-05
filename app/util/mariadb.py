import pymysql.cursors
from dbutils.pooled_db import PooledDB

from util.common import common

config = common.config

_pool = PooledDB(
    creator=pymysql,
    maxconnections=int(config.get('mariadb', 'pool_max_connections', fallback=10)),
    mincached=int(config.get('mariadb', 'pool_min_cached', fallback=2)),
    maxcached=int(config.get('mariadb', 'pool_max_cached', fallback=5)),
    maxshared=0,
    blocking=True,
    ping=1,
    host=config.get('mariadb', 'mariadb_host'),
    port=int(config.get('mariadb', 'mariadb_port')),
    user=config.get('mariadb', 'mariadb_user'),
    password=config.get('mariadb', 'mariadb_password'),
    database=config.get('mariadb', 'mariadb_database'),
    charset=config.get('mariadb', 'charset'),
    cursorclass=pymysql.cursors.DictCursor,
)


def get_mariadb_connection() -> pymysql.Connection:
    return _pool.connection()