import pandas as pd
import math
import io
import os
import re
try:
    import msoffcrypto
except ImportError:
    msoffcrypto = None

from database.db_manager import get_platforms, get_setting, get_excel_passwords
from core.config import DEFAULT_HEADERS

def load_excel_stream(filepath, skip_rows=0):
    ext = os.path.splitext(filepath)[1].lower()
    try:
        # 嘗試預設引擎讀取
        return pd.read_excel(filepath, nrows=0, skiprows=skip_rows), pd.read_excel(filepath, skiprows=skip_rows)
    except Exception as base_e:
        err_str = str(base_e).lower()
        
        # 處理 .xls 格式但被誤稱為 .xlsx 的情況 (OLE2 報錯)
        if ("ole2" in err_str or "workbook in ole2" in err_str):
            try:
                return pd.read_excel(filepath, nrows=0, engine="xlrd", skiprows=skip_rows), pd.read_excel(filepath, engine="xlrd", skiprows=skip_rows)
            except:
                pass
                
        # 處理加密問題
        if msoffcrypto is not None and ("encrypted" in err_str or "unsupported format" in err_str or "password" in err_str):
            passwords = get_excel_passwords()
            for pw in passwords:
                decrypted_wb = io.BytesIO()
                try:
                    with open(filepath, "rb") as f:
                        office_file = msoffcrypto.OfficeFile(f)
                        office_file.load_key(password=pw) 
                        office_file.decrypt(decrypted_wb)
                        
                    decrypted_wb.seek(0)
                    # 對於解密後的流，有時 pandas 仍會猜錯，根據原副檔名強迫指定引擎
                    # 偵測是否為 OLE2 流
                    try:
                        return pd.read_excel(decrypted_wb, nrows=0, skiprows=skip_rows), pd.read_excel(decrypted_wb, skiprows=skip_rows)
                    except Exception as inner_e:
                        if "ole2" in str(inner_e).lower():
                           decrypted_wb.seek(0)
                           return pd.read_excel(decrypted_wb, nrows=0, engine="xlrd", skiprows=skip_rows), pd.read_excel(decrypted_wb, engine="xlrd", skiprows=skip_rows)
                        raise inner_e
                except Exception:
                    continue
            raise Exception("檔案受密碼保護，且嘗試了所有已知密碼皆失敗，請確保密碼已加入設定或手動解除。")
        
        # 最終報錯優化
        if "ole2" in err_str:
            raise Exception("Excel 解析失敗: 偵測到舊版 Excel 格式但讀取失敗，請嘗試另存為標準 .xlsx 格式。")
            
        raise base_e

def parse_excel_file(filepath):
    try:
        custom_header_str = get_setting("custom_export_headers", "")
        export_headers = custom_header_str.split("|||") if custom_header_str else DEFAULT_HEADERS
        
        df_header, df = load_excel_stream(filepath)
        file_headers = [str(h).strip() for h in df_header.columns]
        
        # 從平台資料庫獲取規則
        platforms = get_platforms()
        active_mapping = {}
        static_values = {}
        best_match_score = 0
        
        # 優先嘗試關鍵字識別 (Enterprise級別：自動偵測平台)
        # 讀取前幾列的內容作為特徵文本
        sample_text = ""
        try:
            sample_df = df.head(10).astype(str)
            sample_text = " ".join(sample_df.values.flatten())
        except:
            pass
            
        from database.db_manager import get_platform_by_keywords
        detected_p = get_platform_by_keywords(sample_text)
        
        if detected_p:
            config = platforms[detected_p]
            active_mapping = config.get("excel_mapping", {})
            
            # Extract mapping and skip_rows if new format
            skip_rows = 0
            if isinstance(active_mapping, dict) and "mapping" in active_mapping:
                skip_rows = active_mapping.get("skip_rows", 0)
                active_mapping = active_mapping["mapping"]
                
            static_values = config.get("static_fields", {})
            print(f"Automatic detection matched platform: {detected_p}")
            
            # 若發現平台設定需要跳過行數，則重新讀取以取得正確表頭
            if skip_rows > 0:
                print(f"套用 Skip Rows = {skip_rows} 重新讀取中...")
                df_header, df = load_excel_stream(filepath, skip_rows)
                file_headers = [str(h).strip() for h in df_header.columns]
        else:
            # 如果關鍵字沒中，使用傳統的表頭匹配評分
            for p_name, config in platforms.items():
                mapping = config.get("excel_mapping", {})
                if not mapping: continue
                
                # 兼容性處理
                current_mapping = mapping
                if isinstance(mapping, dict) and "mapping" in mapping:
                    current_mapping = mapping["mapping"]
                
                # 計算命中率
                match_count = sum(1 for h in current_mapping.keys() if h in file_headers)
                
                if match_count > best_match_score and match_count > 0:
                    best_match_score = match_count
                    active_mapping = current_mapping
                    static_values = config.get("static_fields", {})
                    
                    # 傳統匹配如果發現有 skiprows，也需重讀，不過最好還是靠關鍵字偵測
                    if isinstance(mapping, dict) and mapping.get("skip_rows", 0) > 0:
                        skip_rows = mapping.get("skip_rows", 0)
                        df_header, df = load_excel_stream(filepath, skip_rows)
                        file_headers = [str(h).strip() for h in df_header.columns]
                            
                    print(f"Heuristic match identified platform: {p_name} (Score: {match_count})")
        
        records = []
        for index, row in df.iterrows():
            record = {}
            for h in export_headers:
                record[h] = ""
            
            # 1. 根據映射讀取欄位
            for target_col in export_headers:
                found_vals = []
                read_cols = set()
                
                # 原始標題匹配
                if target_col in file_headers:
                    val = row[target_col]
                    if not (pd.isna(val) or (isinstance(val, float) and math.isnan(val))):
                        found_vals.append(str(val).strip())
                        read_cols.add(target_col)
                
                # 平台規則匹配
                for vendor_header, sys_header in active_mapping.items():
                    if sys_header == target_col and vendor_header in file_headers and vendor_header not in read_cols:
                        val = row[vendor_header]
                        if not (pd.isna(val) or (isinstance(val, float) and math.isnan(val))):
                            found_vals.append(str(val).strip())
                            read_cols.add(vendor_header)
                            
                if found_vals:
                    unique_vals = list(dict.fromkeys(found_vals))
                    record[target_col] = " ".join(unique_vals)
            
            # 2. 資料正規化 (Sanitize)
            for sanitize_col in ["數量", "收件人電話號碼", "付款總金額"]:
                if sanitize_col in record:
                    val_str = str(record[sanitize_col]).strip()
                    if val_str:
                        if val_str.endswith(".0"): val_str = val_str[:-2]
                        
                        if sanitize_col in ["數量", "收件人電話號碼"]:
                            record[sanitize_col] = re.sub(r'[^\d]', '', val_str)
                        else:
                            clean_amt = re.sub(r'[^\d.]', '', val_str)
                            if clean_amt.endswith(".0"): clean_amt = clean_amt[:-2]
                            record[sanitize_col] = clean_amt

            # 3. 強制注入靜態常數 (最高優先級，不可覆蓋)
            for sys_col, static_val in static_values.items():
                if sys_col in record:
                    record[sys_col] = static_val

            record["_requires_review"] = False
            record["_review_fields"] = []
            records.append(record)
            
        # 智慧延續空行補值 (Forward-fill) 迴圈
        last_seen = {col: "" for col in ["訂單號碼", "收件人", "收件人電話號碼", "完整地址"]}
        
        for r in records:
            # 1. 紀錄當下最新狀態
            for col in last_seen.keys():
                if r.get(col, "").strip():
                    last_seen[col] = r[col]
                    
            # 2. 如果該列具備商品名稱，但這些基本資訊缺漏，則自動繼承上位
            if r.get("商品名稱", "").strip():
                for col in last_seen.keys():
                    if not r.get(col, "").strip():
                        r[col] = last_seen[col]
                        
                # 3. 針對總金額：特別照顧，空行全部強迫歸零，不延續上位
                if "付款總金額" in r and not r.get("付款總金額", "").strip():
                    r["付款總金額"] = "0"
            
        return {"status": "success", "data": records, "source": filepath}
    except Exception as e:
        if "xlrd" in str(e).lower():
            return {"status": "error", "message": f"請重啟系統，正在背景升級 xlrd 模組以支援 .xls。"}
        return {"status": "error", "message": f"Excel 解析失敗: {str(e)}"}
