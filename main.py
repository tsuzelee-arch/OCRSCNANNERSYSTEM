import os
import sys
import warnings
import traceback

# 徹底隱藏擾人的 libpng warning 與 OpenCV 報錯
os.environ["OPENCV_LOG_LEVEL"] = "SILENT"
os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"
os.environ["QT_LOGGING_RULES"] = "*.debug=false;qt.qpa.*=false"

import warnings
import traceback
import logging

# 關閉 Pillow 對於圖片色域的警告
logging.getLogger("PIL").setLevel(logging.CRITICAL)
logging.getLogger("PIL.PngImagePlugin").setLevel(logging.CRITICAL)

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--mode", choices=["dev", "trial"], default="dev", help="運行模式: dev (開發) 或 trial (試用)")
args, unknown = parser.parse_known_args()
os.environ["ORDER_APP_MODE"] = args.mode

# print(f"--- 系統啟動模式: {os.environ['ORDER_APP_MODE'].upper()} ---")

class StderrFilter:
    def __init__(self, stream):
        self.stream = stream
    def write(self, data):
        if "libpng warning: iCCP: known incorrect sRGB profile" in data: return
        if "libpng warning:" in data: return
        if self.stream is not None:
            self.stream.write(data)
    def flush(self):
        if self.stream is not None:
            self.stream.flush()

sys.stderr = StderrFilter(sys.stderr)
sys.stdout = StderrFilter(sys.stdout) # Prevent print crashes

warnings.filterwarnings('ignore')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
# 自動將工作目錄切換至程式所在位置，防止相對路徑噴錯
os.chdir(BASE_DIR)

from core.logger import logger
from database.db_manager import init_db

def main():
    try:
        logger.info('初始化資料庫 (Initializing Database)...')
        init_db()
        logger.info('啟動主應用程式介面 (Starting Main App Window)...')
        from ui.app_window import run_app
        run_app()
    except Exception as e:
        error_path = os.path.join(BASE_DIR, 'error_log.txt')
        with open(error_path, 'w', encoding='utf-8') as f:
            f.write(traceback.format_exc())
        logger.error(f'Error: {e}')
        input('Press enter to exit...')

if __name__ == '__main__':
    # add multiprocessing freeze support for PyInstaller
    import multiprocessing
    multiprocessing.freeze_support()
    main()
