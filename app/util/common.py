from configparser import ConfigParser
import logging
from logging.handlers import TimedRotatingFileHandler
import os

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
        path = self._get_project_path('resource/config/config.ini')
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
        log_mode = self._config.get("global", "log_mode")
        log_level = self._config.get("global", "log_level")
        log_path_name = os.path.join(log_path, log_name)

        logging.basicConfig(
            level=log_level,
            filemode=log_mode,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt=log_date_format
        )

        logger = logging.getLogger(__name__)
        handler = TimedRotatingFileHandler(
            filename=log_path_name,
            when="midnight",
            interval=1,
            backupCount=0,
            encoding="utf-8"
        )
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s', log_date_format)
        handler.setFormatter(formatter)
        handler.suffix = "%Y-%m-%d_%H-%M-%S.log"
        logger.addHandler(handler)

        return logger

    @property
    def config(self):
        return self._config

    @property
    def logger(self):
        return self._logger

    def get_project_path(self, relative_path):
        return self._get_project_path(relative_path)


# ← module 載入時就初始化，之後直接 import 用
common = Common()