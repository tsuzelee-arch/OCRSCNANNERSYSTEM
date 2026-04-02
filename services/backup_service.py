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
                files_in_zip = zf.namelist()
                
                # 如果舊備份包裡面沒有 db，只有 json，我們要刪除現有的 db 強制它走 migration 流程
                if "order_app.db" not in files_in_zip:
                    if os.path.exists(DB_PATH):
                        # Force closing connection by db_manager if needed, but normally sqlite allows file deletion if no active handles
                        try:
                            os.remove(DB_PATH)
                            logger.info(f"發現舊版備份 (無資料庫)，已清除現有資料庫以強制重新轉移舊設定")
                        except Exception as e:
                            logger.error(f"清除現有資料庫失敗: {e}")
                else:
                    with open(DB_PATH, "wb") as f:
                        f.write(zf.read("order_app.db"))
                    logger.info(f"已還原 {DB_PATH}")

                if "order_ocr_config.json" in files_in_zip:
                    with open(CONFIG_FILE, "wb") as f:
                        f.write(zf.read("order_ocr_config.json"))
                    logger.info(f"已還原 {CONFIG_FILE}")
            logger.info(f"系統資料已從 {load_path} 成功還原")
        except Exception as e:
            logger.error(f"還原過程中發生錯誤: {e}")
            raise BackupRestoreError(f"復原失敗: {str(e)}")
