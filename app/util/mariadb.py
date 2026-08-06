# util/mariadb.py
import pymysql.cursors
from contextlib import contextmanager
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


@contextmanager
def mariadb_connection():
    """
    連線用完自動歸還連線池的 context manager。
    conn.close() 在連線池模式下實際是「歸還」而非真的關閉，
    這裡用 try/finally 統一管理，避免每個 repository 方法各自重複 try/finally。
    """
    conn = get_mariadb_connection()
    try:
        yield conn
    finally:
        conn.close()  # 歸還連線給連線池，不是真的關閉