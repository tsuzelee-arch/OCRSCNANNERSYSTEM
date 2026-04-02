#!/bin/bash
# 自動切換到程式所在的資料夾
cd "$(dirname "$0")"

echo "=========================================="
echo "啟動 Order OCR 系統 (Mac 環境初始化)"
echo "首次啟動可能需要幾分鐘安裝系統依賴"
echo "=========================================="

# 檢查是否安裝 Python 3
if ! command -v python3 &> /dev/null; then
    echo "【錯誤】找不到 Python3 環境！請前往 https://www.python.org/ 安裝 Python 3.10 或更新版本。"
    echo "按任意鍵離開..."
    read -n 1
    exit 1
fi

# 建立專屬虛擬環境 (避免干擾 Mac 系統環境)
if [ ! -d ".mac_venv" ]; then
    echo "正在建立獨立環境 (.mac_venv)..."
    python3 -m venv .mac_venv
fi

# 啟動虛擬環境
source .mac_venv/bin/activate

# 檢查是否安裝所需套件
echo "正在檢查所需套件..."
python3 -m pip install --upgrade pip > /dev/null 2>&1
# 安裝 requirements.txt 內的套件，若失敗則不中斷，嘗試繼續執行
pip install -r requirements.txt

echo "=========================================="
echo "環境準備就緒，正在啟動主畫面..."
echo "=========================================="

# 執行主程式
python3 main.py
