import os
import shutil
import datetime

# 企業級發布腳本 (Professional Release Manager)
# 功能：將當前穩定代碼複製到指定的試用版資料夾，並進行環境預設

SOURCE_DIR = os.path.dirname(os.path.abspath(__file__))
RELEASE_BASE = os.path.join(SOURCE_DIR, "dist", "Trial_Builds")

EXCLUDE_PATTERNS = [
    "__pycache__", ".git", ".vscode", "dist", "build", 
    "*.db", "order_ocr_config.json", "*.spec", "error_log.txt",
    ".gemini", ".agent"
]

def release():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    target_dir = os.path.join(RELEASE_BASE, f"Order_OCR_Trial_{timestamp}")
    
    print(f"--- 開始發布試用版本: {timestamp} ---")
    
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        
    # 複製檔案
    for item in os.listdir(SOURCE_DIR):
        if any(shutil.fnmatch.fnmatch(item, p) for p in EXCLUDE_PATTERNS):
            continue
            
        src_path = os.path.join(SOURCE_DIR, item)
        dst_path = os.path.join(target_dir, item)
        
        if os.path.isdir(src_path):
            shutil.copytree(src_path, dst_path, ignore=shutil.ignore_patterns(*EXCLUDE_PATTERNS))
            print(f"已複製目錄: {item}")
        else:
            shutil.copy2(src_path, dst_path)
            print(f"已複製檔案: {item}")

    # 生成啟動批次檔 (強制試用模式)
    bat_content = f"@echo off\npython main.py --mode trial\npause"
    with open(os.path.join(target_dir, "啟動試用版.bat"), "w", encoding="big5") as f: # 用 big5 以利 Windows CLI 顯示
        f.write(bat_content)
        
    print(f"\n✅ 發布成功！試用版位於：")
    print(f"{target_dir}")
    print("\n提示：您可以將此資料夾整個打包寄給用戶，他們只需執行「啟動試用版.bat」即可，且不會影響您的開發環境數據。")

if __name__ == "__main__":
    import fnmatch
    release()
