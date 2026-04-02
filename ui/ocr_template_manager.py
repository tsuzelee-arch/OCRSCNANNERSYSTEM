import customtkinter as ctk
from tkinter import ttk, messagebox
import json
from database.db_manager import add_platform, get_platforms, delete_platform
from core.config import DEFAULT_HEADERS

class OCRTemplateManagerWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("圖檔/PDF 辨識模板映射 (OCR Template Mapping)")
        self.geometry("1000x800")
        
        self.wait_visibility()
        self.grab_set()
        
        lbl = ctk.CTkLabel(self, text="圖檔與 PDF AI 辨識模板管理", font=ctk.CTkFont(size=20, weight="bold"))
        lbl.pack(pady=10)
        
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.status_lbl = ctk.CTkLabel(main_frame, text="", text_color="green", font=ctk.CTkFont(weight="bold"))
        self.status_lbl.pack(pady=2)
        
        left_frame = ctk.CTkFrame(main_frame, width=500)
        left_frame.pack(side="left", fill="both", expand=True, padx=10)
        
        right_frame = ctk.CTkFrame(main_frame, width=400)
        right_frame.pack(side="right", fill="both", expand=True, padx=10)
        
        # == RIGHT: List ==
        ctk.CTkLabel(right_frame, text="目前已建立的 OCR 規則清單", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        self.tree = ttk.Treeview(right_frame, columns=("Vendor", "Details"), show="headings")
        self.tree.heading("Vendor", text="平台 OCR 規則名稱")
        self.tree.heading("Details", text="設定資訊")
        self.tree.column("Vendor", width=150)
        self.tree.column("Details", width=150)
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)
        
        btn_action_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        btn_action_frame.pack(pady=10)
        
        ctk.CTkButton(btn_action_frame, text="載入選定規則以修改", command=self.load_rule_for_edit).pack(side="left", padx=5)
        ctk.CTkButton(btn_action_frame, text="刪除選定規則", fg_color="red", hover_color="darkred", command=self.del_rule).pack(side="left", padx=5)
        
        self.load_rules()
        
        # == LEFT: Create / Edit ==
        ctk.CTkLabel(left_frame, text="設定區 (新增或修改)", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        ctk.CTkLabel(left_frame, text="說明: 請於下方手動輸入圖片中出現的欄位名稱 (原稱)，並對應到系統標準欄位。", font=ctk.CTkFont(size=12)).pack(pady=2)
        
        ctrl_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        ctrl_frame.pack(pady=5)
        ctk.CTkButton(ctrl_frame, text="➕ 新增映射列", command=self.add_mapping_row).pack(side="left", padx=5)
        ctk.CTkButton(ctrl_frame, text="➕ 新增靜態常數", fg_color="#F4A460", hover_color="#CD853F", command=self.add_static_row_btn).pack(side="left", padx=5)
        
        self.scroll_frame = ctk.CTkScrollableFrame(left_frame)
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.mapping_rows = []
        self.static_rows = []
        
        save_frame = ctk.CTkFrame(left_frame)
        save_frame.pack(fill="x", padx=10, pady=10)
        
        self.entry_name = ctk.CTkEntry(save_frame, placeholder_text="請填妥模板命名 (例如: 某某平台圖片模板)")
        self.entry_name.pack(side="left", padx=5, fill="x", expand=True)
        
        ctk.CTkButton(save_frame, text="儲存規則", fg_color="green", hover_color="darkgreen", command=self.save_rule).pack(side="right", padx=5)

    def load_rules(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        data = get_platforms()
        for name, config in data.items():
            ocr_map = config.get("ocr_mapping", {})
            static = config.get("static_fields", {})
            info = f"映射:{len(ocr_map)} 常數:{len(static)}"
            self.tree.insert("", "end", values=(name, info))

    def del_rule(self):
        selected = self.tree.selection()
        if not selected: return
        name = self.tree.item(selected[0])['values'][0]
        if messagebox.askyesno("確認", f"確定要刪除平台 '{name}' 的 OCR 規則嗎？"):
            # 注意：這裡只清除 OCR 映射，但保留平台實體（因為可能還有 Excel 映射）
            # 或者按照用戶直覺，刪除整個平台。考慮到這是 "OCR 模板管理"，我們只清空 OCR 部分較為保險，但為了簡化，目前與 Excel Manager 保持一致：刪除整個平台。
            delete_platform(name)
            self.load_rules()
            self.status_lbl.configure(text=f"✅ 已刪除平台規則: {name}", text_color="red")

    def add_mapping_row(self, orig_name="", sys_name="-- 忽略此欄 --"):
        row_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        row_frame.pack(fill="x", pady=2)
        
        orig_entry = ctk.CTkEntry(row_frame, width=150, placeholder_text="原始欄位(圖片上的)")
        orig_entry.insert(0, orig_name)
        orig_entry.pack(side="left", padx=5)
        
        ctk.CTkLabel(row_frame, text="➔").pack(side="left")
        
        opts = ["-- 忽略此欄 --"] + DEFAULT_HEADERS
        cb = ctk.CTkComboBox(row_frame, values=opts, width=180)
        cb.set(sys_name)
        cb.pack(side="left", padx=5)
        
        del_btn = ctk.CTkButton(row_frame, text="X", width=30, fg_color="#D32F2F", command=lambda: self.remove_row(row_frame, self.mapping_rows))
        del_btn.pack(side="left", padx=5)
        
        self.mapping_rows.append({"frame": row_frame, "orig": orig_entry, "cb": cb})

    def add_static_row_btn(self, sys_name="-- 請選擇 --", val=""):
        row_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        row_frame.pack(fill="x", pady=2)
        
        opts = ["-- 請選擇 --"] + DEFAULT_HEADERS
        cb = ctk.CTkComboBox(row_frame, values=opts, width=150)
        cb.set(sys_name)
        cb.pack(side="left", padx=5)
        
        en = ctk.CTkEntry(row_frame, width=180, placeholder_text="強制填入數值")
        en.insert(0, val)
        en.pack(side="left", padx=5)
        
        del_btn = ctk.CTkButton(row_frame, text="X", width=30, fg_color="#D32F2F", command=lambda: self.remove_row(row_frame, self.static_rows))
        del_btn.pack(side="left", padx=5)
        
        self.static_rows.append({"frame": row_frame, "cb": cb, "en": en})

    def remove_row(self, frame, list_obj):
        frame.destroy()
        # Find and remove from list
        for i, item in enumerate(list_obj):
            if item["frame"] == frame:
                list_obj.pop(i)
                break

    def load_rule_for_edit(self):
        selected = self.tree.selection()
        if not selected: return
        name = self.tree.item(selected[0])['values'][0]
        
        data = get_platforms().get(name, {})
        self.entry_name.delete(0, 'end')
        self.entry_name.insert(0, name)
        
        # Clear current
        for r in self.mapping_rows: r['frame'].destroy()
        for r in self.static_rows: r['frame'].destroy()
        self.mapping_rows = []
        self.static_rows = []
        
        mapping = data.get("ocr_mapping", {})
        for orig, sys_val in mapping.items():
            self.add_mapping_row(orig, sys_val)
            
        static_vals = data.get("static_fields", {})
        for sys_col, val in static_vals.items():
            self.add_static_row_btn(sys_col, val)
            
        self.status_lbl.configure(text=f"✅ 已載入 OCR 規則: {name}", text_color="green")

    def save_rule(self):
        name = self.entry_name.get().strip()
        if not name: 
            messagebox.showwarning("警告", "請填寫模板名稱！")
            return
            
        mapping = {}
        for row in self.mapping_rows:
            orig = row["orig"].get().strip()
            sys_val = row["cb"].get()
            if orig and sys_val != "-- 忽略此欄 --":
                mapping[orig] = sys_val
                
        static_vals = {}
        for row in self.static_rows:
            sys_col = row["cb"].get()
            val = row["en"].get().strip()
            if sys_col != "-- 請選擇 --" and val:
                static_vals[sys_col] = val
                
        # 存入資料庫
        # 先抓取舊有 Excel 設定（避免覆蓋）
        existing = get_platforms().get(name, {})
        excel_map = existing.get("excel_mapping", {})
        keywords = existing.get("keywords", "")
        
        add_platform(name, keywords, excel_map, mapping, static_vals)
        self.status_lbl.configure(text=f"✅ 平台 OCR 模板 '{name}' 儲存成功！", text_color="green")
        self.load_rules()

def open_ocr_template_manager(parent):
    OCRTemplateManagerWindow(parent)
