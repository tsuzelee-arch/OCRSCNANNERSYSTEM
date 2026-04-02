import cv2
import easyocr
import os
import time
import numpy as np
import pdfplumber
import google.generativeai as genai
from PIL import Image
import json
from database.db_manager import get_setting, get_platforms, get_platform_by_keywords
from core.config import DEFAULT_HEADERS

reader = None

def get_reader():
    global reader
    if reader is None:
        try:
            import torch
            use_gpu = torch.cuda.is_available()
        except ImportError:
            use_gpu = False
            
        print(f"OCR 引擎初始化 (OCR Engine Init) - GPU 加速: {'啟用' if use_gpu else '停用 (使用 CPU)'}")
        reader = easyocr.Reader(['ch_tra', 'en'], gpu=use_gpu)
    return reader

def extract_with_gemini(image_path, api_key, template_config=None):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-flash-latest')
    
    robust_rules = """
        規則與特殊狀況處理：
        1. 若未找到對應數值，保持空字串 ""。
        2. 只回傳合法的 JSON 字串，不要有任何多餘的文字註解。
        3. 【特別注意排版倒置】：有時標籤會在後方，例如「王大明【收件人】」或「0912-345-678（行動電話）」，請將前面的值填入對應欄位。
        4. 【無標籤隱性推斷】：若圖片中完全沒有寫「收件人」或「電話」字樣，但排版上明顯有一串「中文人名」或「符合電話格式的數字(如09xx)」及「地址格式(如xx縣xx區)」，請直接透過邏輯推理將它們填入正確的 JSON 欄位中。
    """
    
    if template_config:
        mapping = template_config.get("mapping", {})
        target_keys = list(mapping.keys())
        keys_str = ", ".join([f'"{k}": ""' for k in target_keys])
        prompt = f"""
        請仔細閱讀圖片中的台灣訂單資訊。
        請找出包含以下欄位的內容，並必須嚴格以 JSON 格式回應：
        {{{keys_str}}}
        {robust_rules}
        """
    else:
        prompt = f"""
        請仔細閱讀圖片中的台灣訂單資訊。這可能是一張發票、廠商回傳報表或是系統截圖。
        請找出包含以下欄位的內容，並必須嚴格以 JSON 格式回應：
        {{"訂單號碼": "", "訂單備註": "", "送貨方式": "", "收件人": "", "郵政編號（如適用)": "", "門市名稱": "", "商品貨號": "", "商品名稱": "", "選項": "", "數量": "", "完整地址": "", "出貨備註": "", "全家服務編號 / 7-11 店號": "", "電郵": "", "收件人電話號碼": "", "付款總金額": "", "貨運編號": "", "倉儲": ""}}
        {robust_rules}
        """
    
    with Image.open(image_path) as img:
        for attempt in range(4):
            try:
                response = model.generate_content([prompt, img])
                # Google Gemini 免費版限制每分鐘 5 次請求，在此進行強制節流
                time.sleep(12.5)
                
                text = response.text.strip()
                if text.startswith("```json"):
                    text = text[7:-3]
                elif text.startswith("```"):
                    text = text[3:-3]
                    
                return json.loads(text)
            except Exception as e:
                if "429" in str(e) or "Quota exceeded" in str(e):
                    print(f"API 流量達標，等待恢復中 (Attempt {attempt+1}/4)... 錯誤: {str(e)}")
                    time.sleep(20) # 遭遇限制時，退避 20 秒
                else:
                    raise e
    
    raise Exception("Google API 額度限制異常 (錯誤 429)，經過四次重試仍失敗，請確認用量是否超過。")

def process_file_with_ai_or_ocr(image_path, template_name=None):
    api_key = get_setting("gemini_api_key", "")
    platforms = get_platforms()
    
    template_config = None
    if template_name and template_name in platforms:
        config = platforms[template_name]
        template_config = {
            "mapping": config.get("ocr_mapping", {}),
            "static_values": config.get("static_fields", {})
        }
    
    # == Enterprise Feature: Auto-detection if no template provided ==
    if not template_name:
        # Perform a quick local OCR scan to find keywords
        try:
            ocr_reader = get_reader()
            quick_result = ocr_reader.readtext(image_path, detail=0)
            sample_text = " ".join(quick_result)
            detected_p = get_platform_by_keywords(sample_text)
            if detected_p:
                print(f"OCR Auto-detection matched platform: {detected_p}")
                config = platforms[detected_p]
                template_config = {
                    "mapping": config.get("ocr_mapping", {}),
                    "static_values": config.get("static_fields", {})
                }
        except Exception as e:
            print(f"Auto-detection failed: {e}")

    if api_key:
        try:
            ai_data = extract_with_gemini(image_path, api_key, template_config)
            
            # Map back to standard headers
            custom_header_str = get_setting("custom_export_headers", "")
            export_headers = custom_header_str.split("|||") if custom_header_str else DEFAULT_HEADERS
            record = {h: "" for h in export_headers}
            
            if template_config:
                mapping = template_config.get("mapping", {})
                for orig_key, val in ai_data.items():
                    sys_key = mapping.get(orig_key)
                    if sys_key and sys_key in record:
                        record[sys_key] = val
                
                # == 最高優先級：強制注入靜態常數 (Static Overwrite) ==
                static_vals = template_config.get("static_values", {})
                for sys_key, val in static_vals.items():
                    if sys_key in record:
                        record[sys_key] = val
            else:
                # Direct match
                for k, v in ai_data.items():
                    if k in record: record[k] = v

            record["_requires_review"] = True 
            record["_review_fields"] = ["商品貨號", "付款總金額"]
            return {"status": "success", "data": [record], "source": image_path}
        except Exception as e:
            print("Gemini API OCR Failed, falling back to local OCR:", str(e))
            
    # Fallback to local easyocr
    try:
        img_array = np.fromfile(image_path, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError(f"Could not decode image at {image_path}")
            
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        temp_path = "temp_local_ocr.png"
        cv2.imwrite(temp_path, gray)
        
        ocr_reader = get_reader()
        result = ocr_reader.readtext(temp_path, detail=0)
        os.remove(temp_path)
        
        raw_text = "\n".join(result)
        
        from processing.excel_parser import DEFAULT_HEADERS
        custom_header_str = get_setting("custom_export_headers", "")
        export_headers = custom_header_str.split("|||") if custom_header_str else DEFAULT_HEADERS
        
        record = {h: "" for h in export_headers}
        record["訂單備註"] = f"[自動擷取備註] {raw_text[:300]}..."
        
        record["_requires_review"] = True
        record["_review_fields"] = ["訂單備註"]
        return {"status": "success", "data": [record], "source": image_path}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def process_image(filepath, template_name=None):
    ext = os.path.splitext(filepath)[1].lower()
    
    # == 效能優化：針對數位型 PDF 直接提取文字層 (數位標籤) ==
    digital_text = ""
    if ext == '.pdf':
        try:
            with pdfplumber.open(filepath) as pdf:
                # 僅提取前兩頁文字作為特徵辨識，速度極快
                sample_pages = pdf.pages[:2]
                digital_text = " ".join([p.extract_text() or "" for p in sample_pages])
        except Exception as e:
            print(f"Digital text extraction failed or not available: {e}")

    # 如果用戶未指定模板，嘗試根據「數位文字」直接判定平台 (比 OCR 快 100 倍)
    if not template_name and digital_text.strip():
        from database.db_manager import get_platform_by_keywords
        detected_p = get_platform_by_keywords(digital_text)
        if detected_p:
            print(f"Fast Digital Detection matched: {detected_p}")
            template_name = detected_p

    if ext == '.pdf':
        try:
            all_records = []
            with pdfplumber.open(filepath) as pdf:
                for i, page in enumerate(pdf.pages):
                    img = page.to_image(resolution=200) # 稍微降低解析度以提升速度
                    temp_img_path = f"temp_pdf_page_{i}.png"
                    img.original.save(temp_img_path, format="PNG")
                    res = process_file_with_ai_or_ocr(temp_img_path, template_name)
                    if res["status"] == "success":
                        all_records.extend(res["data"])
                    if os.path.exists(temp_img_path):
                        os.remove(temp_img_path)
            return {"status": "success", "data": all_records, "source": filepath}
        except Exception as e:
             return {"status": "error", "message": f"PDF parsing failed: {str(e)}."}
    else:
        return process_file_with_ai_or_ocr(filepath, template_name)
