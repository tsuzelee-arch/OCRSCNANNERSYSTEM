class AppError(Exception):
    """應用程式基礎例外類別 (Base exception for the app)"""
    pass

class OCRError(AppError):
    """OCR 處理過程中發生的錯誤"""
    pass

class DatabaseError(AppError):
    """資料庫操作過程中發生的錯誤"""
    pass

class ConfigError(AppError):
    """設定檔讀取或儲存時發生的錯誤"""
    pass

class BackupRestoreError(AppError):
    """備份或還原過程中發生的錯誤"""
    pass
