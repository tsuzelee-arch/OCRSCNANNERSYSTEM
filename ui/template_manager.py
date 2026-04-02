import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
from database.db_manager import add_platform, get_platforms, delete_platform
from core.config import DEFAULT_HEADERS

class TemplateManagerWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("平台 Excel 格式映射與常數定義")
        self.geometry("1000x800")
        
        self.wait_visibility()
        self.grab_set()
        
        lbl = ctk.CTkLabel(self, text="進階平台 Excel 版面對應與常數管理", font=ctk.CTkFont(size=20, weight="bold"))
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
        ctk.CTkLabel(right_frame, text="目前已建立的規則清單", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        self.tree = ttk.Treeview(right_frame, columns=("Vendor", "Details"), show="headings")
        self.tree.heading("Vendor", text="平台規則名稱")
        self.tree.heading("Details", text="設定資訊")
        self.tree.column("Vendor", width=150)
        self.tree.column("Details", width=150)
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)
        
        btn_action_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        btn_action_frame.pack(pady=10)
        
        # 雙擊載入規則
        self.tree.bind("<Double-1>", self._on_double_click)
        ctk.CTkButton(btn_action_frame, text="刪除選定規則", fg_color="red", hover_color="darkred", command=self.del_rule).pack(side="left", padx=5)
        
        btn_action_frame2 = ctk.CTkFrame(right_frame, fg_color="transparent")
        btn_action_frame2.pack(pady=5)
        ctk.CTkButton(btn_action_frame2, text="📤 匯出所有規則", fg_color="#4682B4", hover_color="#5F9EA0", command=self.export_rules).pack(side="left", padx=5)
        ctk.CTkButton(btn_action_frame2, text="📥 匯入/覆寫規則", fg_color="#D2691E", hover_color="#8B4513", command=self.import_rules).pack(side="left", padx=5)
        
        self.load_rules()
        
        # == LEFT: Create / Edit ==
        ctk.CTkLabel(left_frame, text="設定區 (新增或修改)", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        
        load_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        load_frame.pack(pady=5)
        ctk.CTkButton(load_frame, text="📂 從外部載入未知平台 Excel (.xlsx)", command=self.load_sample).pack(side="left", padx=5)
        ctk.CTkButton(load_frame, text="➕ 新增靜態常數", fg_color="#F4A460", hover_color="#CD853F", command=self.add_static_field).pack(side="left", padx=5)
        
        self.mapping_frame = ctk.CTkScrollableFrame(left_frame)
        self.mapping_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # New: Keywords for auto-detection
        self.keyword_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        self.keyword_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(self.keyword_frame, text="自動偵測關鍵字 (逗號隔開):", font=ctk.CTkFont(size=12)).pack(side="left", padx=5)
        self.entry_keywords = ctk.CTkEntry(self.keyword_frame, placeholder_text="Momo, Shopee... (用於自動匹配平台)", width=250)
        self.entry_keywords.pack(side="left", padx=5, fill="x", expand=True)
        
        # New: Skip Rows
        self.skip_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        self.skip_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(self.skip_frame, text="表頭下方略過資料行數 (跳過無效資訊):", font=ctk.CTkFont(size=12)).pack(side="left", padx=5)
        self.entry_skip_rows = ctk.CTkEntry(self.skip_frame, placeholder_text="預設 0", width=80)
        self.entry_skip_rows.pack(side="left", padx=5)
        
        self.vendor_headers = []
        self.comboboxes = {}      
        self.static_entries = {}  
        
        save_frame = ctk.CTkFrame(left_frame)
        save_frame.pack(fill="x", padx=10, pady=10)
        
        self.entry_name = ctk.CTkEntry(save_frame, placeholder_text="請填妥平台命名 (例如: 燦坤供應商)")
        self.entry_name.pack(side="left", padx=5, fill="x", expand=True)
        
        ctk.CTkButton(save_frame, text="儲存規則", fg_color="green", hover_color="darkgreen", command=self.save_rule).pack(side="right", padx=5)

    def load_rules(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        data = get_platforms()
        for name, config in data.items():
            excel_map = config.get("excel_mapping", {})
            static = config.get("static_fields", {})
            info = f"格式:{len(excel_map)} 常數:{len(static)}"
            self.tree.insert("", "end", values=(name, info))

    def del_rule(self):
        selected = self.tree.selection()
        if not selected: return
        item = self.tree.item(selected[0])
        val = item['values'][0]
        if messagebox.askyesno("警告", f"確定要刪除平台 '{val}' 的所有規則嗎？"):
            delete_platform(val)
            self.load_rules()

    def export_rules(self):
        import json
        save_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")], title="匯出規則格式檔")
        if save_path:
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(get_templates(), f, ensure_ascii=False, indent=4)
            self.status_lbl.configure(text=f"✅ 規則已成功匯出至: {os.path.basename(save_path)}", text_color="green")

    def import_rules(self):
        import json
        load_path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")], title="匯入/遷移規則格式檔")
        if load_path:
            try:
                with open(load_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for name, config in data.items():
                    # 嘗試遷移舊格式或存入新格式
                    if "excel_mapping" in config:
                        add_platform(name, config.get("keywords", ""), config.get("excel_mapping"), config.get("ocr_mapping"), config.get("static_fields"))
                    else:
                        # 舊版單純 mapping
                        add_platform(name, "", config)
                self.load_rules()
                self.status_lbl.configure(text=f"✅ 成功匯入並轉移了 {len(data)} 組平台規則！", text_color="green")
            except Exception as e:
                messagebox.showerror("錯誤", f"匯入失敗: {e}")
        
    def _on_double_click(self, event):
        self.load_rule_for_edit()

    def load_rule_for_edit(self):
        selected = self.tree.selection()
        if not selected: return
        
        item = self.tree.item(selected[0])
        name = item['values'][0]
        self.entry_name.delete(0, 'end')
        self.entry_name.insert(0, name)
        
        data = get_platforms().get(name, {})
        self.entry_keywords.delete(0, 'end')
        self.entry_keywords.insert(0, data.get("keywords", ""))
        
        mapping = data.get("excel_mapping", {})
        static_vals = data.get("static_fields", {})
        
        # 兼容性處理：如果 excel_mapping 裡面存的是舊格式
        if "mapping" in mapping:
            self.vendor_headers = list(mapping["mapping"].keys())
            static_vals = mapping.get("static_values", static_vals)
            skip_rows = mapping.get("skip_rows", 0)
            mapping = mapping["mapping"]
        else:
            self.vendor_headers = list(mapping.keys())
            skip_rows = 0
            
        self.entry_skip_rows.delete(0, 'end')
        if skip_rows > 0:
            self.entry_skip_rows.insert(0, str(skip_rows))
            
        self.render_mappings(pre_mapping=mapping, pre_static=static_vals)
        self.status_lbl.configure(text=f"✅ 平台設定 '{name}' 已匯入修改區！", text_color="green")
        
    def load_sample(self):
        filepath = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx;*.xls")])
        if not filepath: return
        try:
            df = pd.read_excel(filepath, nrows=0)
            self.vendor_headers = list(df.columns)
            self.render_mappings()
        except Exception as e:
            messagebox.showerror("讀取失敗", f"無法讀取範本檔案:\n{str(e)}")
            
    def render_mappings(self, pre_mapping=None, pre_static=None):
        for widget in self.mapping_frame.winfo_children():
            widget.destroy()
            
        self.comboboxes = {}
        self.static_entries = {}
        opts = ["-- 忽略此欄 --"] + DEFAULT_HEADERS
        
        ctk.CTkLabel(self.mapping_frame, text="平台方原始欄位", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=10, pady=5)
        ctk.CTkLabel(self.mapping_frame, text="對應到系統標準欄位", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, padx=10, pady=5)
        
        row_idx = 1
        for h in self.vendor_headers:
            h_str = str(h)
            ctk.CTkLabel(self.mapping_frame, text=h_str).grid(row=row_idx, column=0, padx=10, pady=5, sticky="w")
            cb = ctk.CTkComboBox(self.mapping_frame, values=opts, width=200)
            
            if pre_mapping and h_str in pre_mapping:
                cb.set(pre_mapping[h_str])
            else:
                for default_h in DEFAULT_HEADERS:
                    if default_h in h_str:
                        cb.set(default_h)
                        break
                else:
                    cb.set("-- 忽略此欄 --")
                    
            cb.grid(row=row_idx, column=1, padx=10, pady=5, sticky="w")
            self.comboboxes[h_str] = cb
            row_idx += 1
            
        if pre_static:
            ctk.CTkLabel(self.mapping_frame, text="-- 靜態常數 --", font=ctk.CTkFont(weight="bold", slant="italic")).grid(row=row_idx, column=0, columnspan=2, pady=(15, 5))
            row_idx += 1
            for sys_col, val in pre_static.items():
                self.create_static_row(row_idx, sys_col, val)
                row_idx += 1

    def create_static_row(self, r_idx, preset_sys="-- 請選擇 --", preset_val=""):
        opts = ["-- 請選擇 --"] + DEFAULT_HEADERS
        cb = ctk.CTkComboBox(self.mapping_frame, values=opts, width=150)
        cb.set(preset_sys)
        cb.grid(row=r_idx, column=0, padx=10, pady=5, sticky="e")
        
        en = ctk.CTkEntry(self.mapping_frame, width=200, placeholder_text="強制填入數值")
        en.insert(0, preset_val)
        en.grid(row=r_idx, column=1, padx=10, pady=5, sticky="w")
        
        self.static_entries[cb] = en

    def add_static_field(self):
        r_idx = len(self.mapping_frame.winfo_children()) // 2 + 10 
        self.create_static_row(r_idx)
            
    def save_rule(self):
        name = self.entry_name.get().strip()
        keywords = self.entry_keywords.get().strip()
        if not name: 
            messagebox.showwarning("警告", "請填寫平台名稱！")
            return
            
        mapping = {}
        for h, cb in self.comboboxes.items():
            val = cb.get()
            mapping[h] = val
                
        # 處理 Skip Rows
        skip_val = self.entry_skip_rows.get().strip()
        try:
            skip_rows = int(skip_val) if skip_val else 0
        except ValueError:
            skip_rows = 0
            
        final_mapping = {
            "mapping": mapping,
            "skip_rows": skip_rows
        }
                
        static_vals = {}
        for cb, en in self.static_entries.items():
            sys_col = cb.get()
            val = en.get().strip()
            if sys_col != "-- 請選擇 --" and val:
                static_vals[sys_col] = val
                
        # 存入資料庫
        # 先抓取舊有 OCR 設定（避免覆蓋）
        existing = get_platforms().get(name, {})
        ocr_map = existing.get("ocr_mapping", {})
        
        add_platform(name, keywords, final_mapping, ocr_map, static_vals)
        self.status_lbl.configure(text=f"✅ 平台設定 '{name}' 已完美儲存至資料庫！", text_color="green")
        self.load_rules()

def open_template_manager(parent):
    TemplateManagerWindow(parent)
