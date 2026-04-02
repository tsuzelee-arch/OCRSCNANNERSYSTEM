import logging
import sys
import os

def setup_logger(log_file="app.log", level=logging.INFO):
    """
    設定並回傳全域的 Logger，同時輸出到控制台與檔案。
    """
    logger = logging.getLogger("order_ocr")
    logger.setLevel(level)

    # 避免重複添加 Handler
    if logger.handlers:
        return logger

    # 控制台 Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    
    # 檔案 Handler
    fh = logging.FileHandler(log_file, encoding='utf-8', mode='a')
    fh.setLevel(level)

    # 設定格式 (Formatter)
    formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(module)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)

    # 將 Handlers 加入 logger
    logger.addHandler(ch)
    logger.addHandler(fh)

    return logger

# 提供全域實例，讓其他模組直接引入使用
logger = setup_logger()
