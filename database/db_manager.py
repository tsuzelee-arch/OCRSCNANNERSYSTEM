import sqlite3
import os
import json
import core.config as config_manager

import sys

def get_app_root():
    if getattr(sys, 'frozen', False):
        # 如果是封裝後的 EXE，使用 EXE 所在目錄
        return os.path.dirname(sys.executable)
    # 開發環境下使用原始目錄
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 根據啟動模式決定資料庫路徑 (DEV vs TRIAL)
MODE = os.environ.get("ORDER_APP_MODE", "dev")
DB_NAME = "order_app.db" if MODE == "dev" else "order_app_trial.db"
DB_PATH = os.path.join(get_app_root(), DB_NAME)

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # 1. 基礎表結構
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS item_dictionary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wrong_spelling TEXT UNIQUE NOT NULL,
                correct_spelling TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS product_catalog (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                tags TEXT,
                item_no TEXT NOT NULL
            )
        ''')
        
        # 2. 核心平台表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS platforms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                keywords TEXT,
                excel_mapping TEXT,
                ocr_mapping TEXT,
                static_fields TEXT
            )
        ''')
        # 先 Commit 表結構，避免後續遷移失敗導致建表回滾
        conn.commit()
        
        # 3. 執行數據遷移
        migrate_config_to_sqlite(cursor)
        conn.commit()
    except Exception as e:
        print(f"Database Initialization Error: {e}")
    finally:
        conn.close()

def migrate_config_to_sqlite(cursor):
    """將 config_manager 中的 JSON 規則整合進 SQLite 平台庫 (優化版：正確處理巢狀結構)"""
    try:
        from core.config import get_templates, get_ocr_templates
        excel_tpls = get_templates()
        ocr_tpls = get_ocr_templates()
        
        # 取得所有唯一的平台名稱
        all_platform_names = set(excel_tpls.keys()) | set(ocr_tpls.keys())
        
        for name in all_platform_names:
            # 檢查是否已經存在於資料庫
            cursor.execute("SELECT id FROM platforms WHERE name = ?", (name,))
            if not cursor.fetchone():
                e_obj = excel_tpls.get(name, {})
                o_obj = ocr_tpls.get(name, {})
                
                # 處理 Excel 規則中的 mapping 與 static_values
                e_mapping = e_obj.get("mapping", e_obj) if isinstance(e_obj, dict) else {}
                # 如果 e_obj 本身就是平鋪的 mapping (沒有 mapping 鍵)，則 e_mapping 就是 e_obj
                # 除非 e_obj 裡面有 "mapping" 鍵
                if isinstance(e_obj, dict) and "mapping" in e_obj:
                    e_mapping = e_obj["mapping"]
                
                # 處理 OCR 規則中的 mapping
                o_mapping = o_obj.get("mapping", o_obj) if isinstance(o_obj, dict) else {}
                if isinstance(o_obj, dict) and "mapping" in o_obj:
                    o_mapping = o_obj["mapping"]
                
                # 提取靜態欄位 (優先從 Excel 或 OCR 中找)
                static_vals = {}
                if isinstance(e_obj, dict) and "static_values" in e_obj:
                    static_vals = e_obj["static_values"]
                elif isinstance(o_obj, dict) and "static_values" in o_obj:
                    static_vals = o_obj["static_values"]
                
                cursor.execute('''
                    INSERT INTO platforms (name, keywords, excel_mapping, ocr_mapping, static_fields)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    name,
                    "", # 預設空關鍵字
                    json.dumps(e_mapping),
                    json.dumps(o_mapping),
                    json.dumps(static_vals)
                ))
    except Exception as e:
        print(f"Migration error: {e}")

def add_dictionary_entry(wrong, correct):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR REPLACE INTO item_dictionary (wrong_spelling, correct_spelling) VALUES (?, ?)", (wrong, correct))
        conn.commit()
    finally:
        conn.close()

def get_dictionary():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT wrong_spelling, correct_spelling FROM item_dictionary")
    rows = cursor.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}

def delete_dictionary_entry(wrong):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM item_dictionary WHERE wrong_spelling = ?", (wrong,))
        conn.commit()
    finally:
        conn.close()

def add_catalog_item(product_name, tags, item_no):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO product_catalog (product_name, tags, item_no) VALUES (?, ?, ?)", (product_name, tags, item_no))
    conn.commit()
    conn.close()

def update_catalog_item(item_id, product_name, tags, item_no):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE product_catalog SET product_name=?, tags=?, item_no=? WHERE id=?", (product_name, tags, item_no, item_id))
    conn.commit()
    conn.close()

def get_catalog():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, product_name, tags, item_no FROM product_catalog")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "product_name": r[1], "tags": r[2], "item_no": r[3]} for r in rows]

def delete_catalog_item(item_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM product_catalog WHERE id=?", (item_id,))
    conn.commit()
    conn.close()

def clear_product_catalog():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM product_catalog")
    # Reset autoincrement counter if desired
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='product_catalog'")
    conn.commit()
    conn.close()

# == Platform Management ==
def add_platform(name, keywords="", excel_mapping=None, ocr_mapping=None, static_fields=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO platforms (name, keywords, excel_mapping, ocr_mapping, static_fields)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            name, 
            keywords, 
            json.dumps(excel_mapping) if excel_mapping else "{}", 
            json.dumps(ocr_mapping) if ocr_mapping else "{}", 
            json.dumps(static_fields) if static_fields else "{}"
        ))
        conn.commit()
    finally:
        conn.close()

def get_platforms():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, keywords, excel_mapping, ocr_mapping, static_fields FROM platforms")
        rows = cursor.fetchall()
        conn.close()
        
        platforms = {}
        for row in rows:
            platforms[row[0]] = {
                "keywords": row[1] or "",
                "excel_mapping": json.loads(row[2]) if row[2] else {},
                "ocr_mapping": json.loads(row[3]) if row[3] else {},
                "static_fields": json.loads(row[4]) if row[4] else {}
            }
        return platforms
    except sqlite3.OperationalError:
        # 如果表不存在，執行初始化並回傳空
        return {}
    except Exception as e:
        print(f"Error fetching platforms: {e}")
        return {}

def delete_platform(name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM platforms WHERE name = ?", (name,))
    conn.commit()
    conn.close()

def get_platform_by_keywords(text):
    """偵測文本中是否包含任何平台的關鍵字，回傳最匹配的平台名稱"""
    platforms = get_platforms()
    text_lower = text.lower()
    for name, config in platforms.items():
        keywords = [k.strip().lower() for k in config["keywords"].split(",") if k.strip()]
        # 同時檢查平台名稱本身作為關鍵字
        keywords.append(name.lower())
        
        for k in keywords:
            if k and k in text_lower:
                return name
    return None

# Delegate legacy methods strictly to config_manager to prevent backward compatibility issues
def save_template(name, mapping_dict):
    config_manager.save_template(name, mapping_dict)

def get_templates():
    return config_manager.get_templates()

def delete_template(name):
    config_manager.delete_template(name)

def set_setting(key, value):
    config_manager.set_setting(key, value)

def get_setting(key, default=""):
    return config_manager.get_setting(key, default)

def get_excel_passwords():
    return config_manager.get_excel_passwords()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
