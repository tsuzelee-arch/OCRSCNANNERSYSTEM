import zipfile
import os
from core.logger import logger
from core.exceptions import BackupRestoreError
from database.db_manager import DB_PATH
from core.config import CONFIG_FILE

class BackupService:
    @staticmethod
    def backup_system(save_path: str):
        """將系統資料庫與設定檔打包為 ZIP"""
        try:
            with zipfile.ZipFile(save_path, 'w') as zf:
                if os.path.exists(DB_PATH):
                    zf.write(DB_PATH, "order_app.db")
                    logger.info(f"已備份 {DB_PATH}")
                if os.path.exists(CONFIG_FILE):
                    zf.write(CONFIG_FILE, "order_ocr_config.json")
                    logger.info(f"已備份 {CONFIG_FILE}")
            logger.info(f"系統資料已備份至 {save_path}")
        except Exception as e:
            logger.error(f"備份過程中發生錯誤: {e}")
            raise BackupRestoreError(f"備份失敗: {str(e)}")

    @staticmethod
    def restore_system(load_path: str):
        """讀取 ZIP 並覆蓋目前的資料庫與設定檔"""
        try:
            with zipfile.ZipFile(load_path, 'r') as zf:
                if "order_app.db" in zf.namelist():
                    with open(DB_PATH, "wb") as f:
                        f.write(zf.read("order_app.db"))
                    logger.info(f"已還原 {DB_PATH}")
                if "order_ocr_config.json" in zf.namelist():
                    with open(CONFIG_FILE, "wb") as f:
                        f.write(zf.read("order_ocr_config.json"))
                    logger.info(f"已還原 {CONFIG_FILE}")
            logger.info(f"系統資料已從 {load_path} 成功還原")
        except Exception as e:
            logger.error(f"還原過程中發生錯誤: {e}")
            raise BackupRestoreError(f"復原失敗: {str(e)}")
