from database.db_manager import get_catalog
from difflib import SequenceMatcher

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def find_best_match(product_name_str, catalog):
    if not product_name_str: return None
    
    product_name_str = product_name_str.lower()
    
    best_tag_match = None
    max_tag_matches = 0
    
    # 策略一：嚴格計算「關鍵字標籤命中數量」，取最高分者
    for item in catalog:
        tags = [t.strip().lower() for t in item.get('tags', '').split(',') if t.strip()]
        if not tags: continue
        
        match_count = sum(1 for tag in tags if tag in product_name_str)
        if match_count > max_tag_matches:
            max_tag_matches = match_count
            best_tag_match = item
            
    if best_tag_match and max_tag_matches > 0:
        return best_tag_match
        
    # 策略二：如果沒有命中任何標籤，透過原名進行模糊比較
    best_fuzzy_match = None
    highest_score = 0
    
    for item in catalog:
        # Fuzzy match on the official name
        score = similar(product_name_str, item['product_name'].lower())
        if score > highest_score:
            highest_score = score
            best_fuzzy_match = item
            
    if highest_score > 0.6:
        return best_fuzzy_match
        
    return None

def aggregate_and_flag_data(extracted_records):
    """
    Takes records from parsers, applies Product Catalog fuzzy flagging.
    """
    catalog = get_catalog()
    if not catalog: return extracted_records
    
    for record in extracted_records:
        raw_product = record.get("商品名稱", "")
        # Try to find a match in the catalog
        match = find_best_match(raw_product, catalog)
        
        if match:
            record["_requires_review"] = True
            
            if "_review_fields" not in record:
                record["_review_fields"] = []
            
            if "商品貨號" not in record["_review_fields"]:
                record["_review_fields"].append("商品貨號")
                
            record["_suggestion"] = match['item_no']
            
            # Format text explicitly so user knows it's an AI suggestion waiting for confirmation
            original_val = record.get("商品貨號", "")
            if original_val:
                record["商品貨號"] = f"[系統建議: {match['item_no']}] 原:{original_val}"
            else:
                record["商品貨號"] = f"[系統建議: {match['item_no']}]"
                
    return extracted_records
