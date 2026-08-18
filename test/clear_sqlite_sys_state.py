import os
import sys
from pathlib import Path

# 1. 計算專案根目錄 (此腳本位在 test/，上一層 .parent 就是專案根目錄)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 2. 強制將當前工作目錄 (CWD) 切換到專案根目錄 (確保相對路徑與 app.py 一致)
os.chdir(PROJECT_ROOT)

# 3. 將專案根目錄加入 sys.path，確保 import util 時不會找不到模組
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# --- 接下來才 import 專案內模組 ---
import logging
import sqlite3
from util.sqlite import sqlite_connection

# 設定日誌輸出格式
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def clear_sys_state_table():
    """
    清空 sys_state 資料表的所有內容，並重置 AUTOINCREMENT 計數器。
    """
    try:
        with sqlite_connection() as conn:
            cursor = conn.cursor()

            # 印出目前實際連線的 DB 絕對路徑做為確認
            cursor.execute("PRAGMA database_list;")
            db_info = cursor.fetchall()
            db_path = db_info[0]["file"] if db_info else "Unknown"
            logger.info(f"正在操作的資料庫路徑: {db_path}")

            # 1. 開始事務 (Transaction)
            cursor.execute("BEGIN TRANSACTION;")

            # 2. 清空 sys_state 資料表
            cursor.execute("DELETE FROM sys_state;")
            deleted_rows = cursor.rowcount

            # 3. 清除 SQLite 自增主鍵 (AUTOINCREMENT) 的計數器紀錄 (若存在)
            cursor.execute("DELETE FROM sqlite_sequence WHERE name = 'sys_state';")

            # 4. 提交變更
            conn.commit()

            logger.info(f"成功清空 sys_state 資料表！共刪除 {deleted_rows} 筆紀錄。")

    except sqlite3.OperationalError as e:
        logger.error(f"資料庫操作失敗（可能遇到 lock 或路徑錯誤）: {e}")
        raise
    except Exception as e:
        logger.error(f"清空 sys_state 時發生未預期錯誤: {e}")
        raise


if __name__ == "__main__":
    # 若手動執行要注意 python path
    # echo $PYTHONPATH
    # export PYTHONPATH=/opt/nekosaur/nekosaur_simulator_server/app
    #
    # cd /opt/nekosaur/nekosaur_simulator_server
    # python3 test/clear_sqlite_table.py
    clear_sys_state_table()