from configparser import ConfigParser
import logging
from logging.handlers import TimedRotatingFileHandler
import os
from pathlib import Path
from typing import Union


class Common:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = None
            cls._instance._logger = None
            cls._instance._init()
        return cls._instance

    def _init(self):
        self._config = ConfigParser()
        path = Path(f'{self._get_project_path('resource/config/config.ini')}')
        files_read = self._config.read(path)
        if not files_read:
            raise FileNotFoundError(f"Config not found: {path}")

        self._logger = self._build_logger()

    def _get_project_path(self, relative_path):
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(base, relative_path)

    def _build_logger(self):
        log_date_format = '%Y-%m-%d %H:%M:%S'
        log_path = self._get_project_path(self._config.get("global", "log_path"))
        os.makedirs(log_path, exist_ok=True)
        log_name = self._config.get("global", "log_name")
        log_level = self._config.get("global", "log_level")
        log_path_name = os.path.join(log_path, log_name)

        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s', log_date_format)

        logger = logging.getLogger(__name__)
        logger.setLevel(log_level)
        logger.propagate = False  # 不往 root logger 冒泡

        # 一般 log，全部 level 寫進自己管理的檔案
        file_handler = TimedRotatingFileHandler(
            filename=log_path_name,
            when="midnight",
            interval=1,
            backupCount=0,
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        file_handler.suffix = "%Y-%m-%d_%H-%M-%S.log"
        logger.addHandler(file_handler)

        # 只有 ERROR 以上才寫到 stderr（systemd 會導去 app_error.log）
        stderr_handler = logging.StreamHandler()
        stderr_handler.setLevel(logging.ERROR)
        stderr_handler.setFormatter(formatter)
        logger.addHandler(stderr_handler)

        return logger

    @property
    def config(self):
        return self._config

    @property
    def logger(self):
        return self._logger

    def get_project_path(self, relative_path):
        return self._get_project_path(relative_path)

    @staticmethod
    def to_path(val: Union[Path, str, None]) -> Path:
        """
        將傳入的數值安全轉為 pathlib.Path 物件。
        - 若傳入已是 Path 物件，直接回傳。
        - 若傳入非空字串，轉為 Path 物件。
        - 若傳入 None 或空字串 ""，回傳 Path("")。
        """
        if isinstance(val, Path):
            return val
        return Path(val) if val else Path("")

# 建立單例物件 (Singleton Instance)
# ← module 載入時就初始化，之後直接 import 用
common = Common()