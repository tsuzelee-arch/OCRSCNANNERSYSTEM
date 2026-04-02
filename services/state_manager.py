from threading import Lock
from typing import List, Dict, Any
from core.logger import logger

class StateManager:
    """管理應用程式的全域記憶體狀態 (Singleton)"""
    _instance = None
    _lock = Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(StateManager, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized: return
        self._cached_records: List[Dict[str, Any]] = []
        self._initialized = True
        logger.info("StateManager initialized.")

    def get_records(self) -> List[Dict[str, Any]]:
        """取得目前記憶體中的訂單紀錄"""
        return self._cached_records

    def set_records(self, records: List[Dict[str, Any]]):
        """覆寫記憶體中的訂單紀錄"""
        self._cached_records = records
        logger.info(f"已覆寫總表紀錄，目前共 {len(self._cached_records)} 筆。")

    def append_records(self, new_records: List[Dict[str, Any]]):
        """附加新的訂單紀錄至總表"""
        self._cached_records.extend(new_records)
        logger.info(f"已附加 {len(new_records)} 筆紀錄，目前共 {len(self._cached_records)} 筆。")

    def clear_records(self):
        """清空所有紀錄"""
        self._cached_records.clear()
        logger.info("已清空總表紀錄。")

state_manager = StateManager()
