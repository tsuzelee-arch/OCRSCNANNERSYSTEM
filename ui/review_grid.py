import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import re
from core.config import DEFAULT_HEADERS, get_setting

class ReviewGridWindow(ctk.CTkToplevel):
    def __init__(self, parent, data_records):
        super().__init__(parent)
        self.title("總表預覽與人工校對 (Human Review)")
        self.geometry("1100x700")
        self.data = data_records
        self.important_fields = get_setting("important_fields", [])
        
        self.wait_visibility()
        self.grab_set()
        
        self.lbl_title = ctk.CTkLabel(self, text="審閱與匯出總表", font=ctk.CTkFont(size=20, weight="bold"))
        self.lbl_title.pack(pady=10)
        
        style = ttk.Style()
        # 強制使用 clam 樣式以確保在 Windows 下 row background tags (紅/黃) 能正常運作
        style.theme_use("clam") 
        style.configure("Treeview", rowheight=30, background="white", foreground="black", fieldbackground="white")
        style.map("Treeview", background=[("selected", "#347083")])
        style.configure("Treeview.Heading", font=('Arial', 10, 'bold'))
        
        self.tree_frame = ctk.CTkFrame(self)
        self.tree_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        if not self.data:
            ctk.CTkLabel(self.tree_frame, text="無資料可顯示").pack(pady=50)
            return
            
        columns = list(self.data[0].keys())
        self.display_columns = [col for col in columns if not col.startswith('_')]
        
        self.tree = ttk.Treeview(self.tree_frame, columns=self.display_columns, show="headings")
        
        for col in self.display_columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")
            
        self.tree.pack(side="left", fill="both", expand=True)
        
        scrollbar_y = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(self.tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscroll=scrollbar_y.set, xscroll=scrollbar_x.set)
        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x.pack(side="bottom", fill="x")
        
        self.populate_data()
        self.tree.bind("<Button-1>", self.on_click)
        
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(pady=10)
        
        self.btn_export = ctk.CTkButton(
            action_frame, text="💾 智能關鍵字分流匯出 (Smart Export)", 
            command=self.export_excel, fg_color="green", hover_color="darkgreen", height=50
        )
        self.btn_export.pack(side="left", padx=10)
        
        self.btn_approve_all = ctk.CTkButton(
            action_frame, text="✨ 一鍵確認並套用所有 AI 建議", 
            command=self.approve_all, fg_color="#F4A460", hover_color="#CD853F", height=50
        )
        self.btn_approve_all.pack(side="left", padx=10)
        
        self.btn_split_export = ctk.CTkButton(
            action_frame, text="📂 依欄位分流匯出 (Split Export)", 
            command=self.export_split_excel, fg_color="#4682B4", hover_color="#5F9EA0", height=50
        )
        self.btn_split_export.pack(side="left", padx=10)
        
    def populate_data(self):
        self.tree.tag_configure('review_needed', background='#FFFACD', foreground='black')
        self.tree.tag_configure('important_missing', background='#FFCDD2', foreground='black') # Reddish
        
        for row_idx, item in enumerate(self.data):
            values = []
            tags = []
            requires_review = item.get("_requires_review", False)
            if requires_review: tags.append('review_needed')
            
            is_any_important_missing = False
            for col in self.display_columns:
                val = str(item.get(col, "")).strip()
                if val.endswith(".0"): val = val[:-2]
                
                # 重要欄位提示：顯示紅色與加上驚嘆號，如果是空值
                if col in self.important_fields and not val:
                    is_any_important_missing = True
                    val = f"[!] {val}"
                values.append(val)
                
            if is_any_important_missing:
                tags.append('important_missing')
                
            self.tree.insert("", "end", iid=str(row_idx), values=values, tags=tuple(tags))
            
    def on_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell": return
        
        item = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        if not item or not col: return
        
        col_idx = int(col.replace('#', '')) - 1
        current_vals = list(self.tree.item(item, "values"))
        current_val = current_vals[col_idx]
        col_name = self.display_columns[col_idx]
        
        default_val = str(current_val)
        if "[系統建議:" in default_val:
            match = re.search(r"系統建議: (.*?)\]", default_val)
            if match:
                accepted_val = match.group(1).strip()
                current_vals[col_idx] = accepted_val
                # Clear highlight once user touches it
                self.tree.item(item, values=current_vals, tags=())
            return
            
        # Spawn floating entry overlay
        import tkinter as tk
        try:
            x, y, w, h = self.tree.bbox(item, col)
        except ValueError:
            return # Cell not visible
            
        entry_overlay = tk.Entry(self.tree, font=('Arial', 10), justify='center')
        entry_overlay.place(x=x, y=y, width=w, height=h)
        entry_overlay.insert(0, default_val)
        entry_overlay.focus_set()
        
        def save_edit(event_or_none=None):
            new_val = entry_overlay.get().strip()
            
            # Numeric Formatting: remove .0
            if new_val.endswith(".0"):
                new_val = new_val[:-2]
                
            current_vals[col_idx] = new_val
            
            # Re-check important missing status for this row
            tags = []
            is_any_important_missing = False
            for c_idx, c_name in enumerate(self.display_columns):
                val = str(current_vals[c_idx]).strip()
                # Remove old [!] if user is editing
                if val.startswith("[!] "):
                    val = val[4:]
                    current_vals[c_idx] = val
                
                if c_name in self.important_fields and not val:
                    is_any_important_missing = True
                    current_vals[c_idx] = f"[!] {val}"
            
            if is_any_important_missing:
                tags.append('important_missing')
            
            self.tree.item(item, values=current_vals, tags=tuple(tags))
            entry_overlay.destroy()
            
        entry_overlay.bind("<Return>", save_edit)
        entry_overlay.bind("<FocusOut>", save_edit)

    def approve_all(self):
        has_unreviewed = False
        for child in self.tree.get_children():
            vals = list(self.tree.item(child, "values"))
            updated = False
            for idx, val in enumerate(vals):
                val_str = str(val).strip()
                if val_str.endswith(".0"): val_str = val_str[:-2]
                
                if "[系統建議:" in val_str:
                    has_unreviewed = True
                    match = re.search(r"系統建議: (.*?)\]", val_str)
                    if match:
                        vals[idx] = match.group(1).strip()
                        if vals[idx].endswith(".0"): vals[idx] = vals[idx][:-2]
                        updated = True
            if updated:
                self.tree.item(child, values=vals, tags=())
                
        if has_unreviewed:
            messagebox.showinfo("完成", "所有 AI 建議皆已全數替換為正式資料。")
        else:
            messagebox.showinfo("提示", "目前沒有需要一鍵確認的 AI 建議。")

    def export_excel(self):
        records = []
        has_unreviewed = False
        
        missing_mandatories = []
        for child in self.tree.get_children():
            row_vals = self.tree.item(child, "values")
            row_dict = {}
            row_id = str(child)
            for idx, (col, val) in enumerate(zip(self.display_columns, row_vals)):
                val_str = str(val).strip()
                if "[系統建議:" in val_str:
                    has_unreviewed = True
                
                # Check for important missing
                if col in self.important_fields and (not val_str or val_str.startswith("[!]")):
                    missing_mandatories.append(f"第 {int(row_id)+1} 行: {col}")
                
                # Clean up the visual prefix if it exists
                if val_str.startswith("[!] "):
                    val_str = val_str[4:]
                
                row_dict[col] = val_str
            records.append(row_dict)
            
        if missing_mandatories:
            err_list = "\n".join(missing_mandatories[:10])
            if len(missing_mandatories) > 10: err_list += "\n...等等"
            messagebox.showerror("匯出攔截：必填欄位缺失", f"下列欄位被標記為『重要』但目前為空值，請修正後再匯出：\n\n{err_list}")
            return

        accept_ai = True
        if has_unreviewed:
            resp = messagebox.askyesnocancel(
                "含有未讀取的 AI 建議", 
                "您有部分深黃色儲存格的 AI 建議貨號尚未雙點擊人工確認。\n\n選擇【是(Yes)】: 自動全部套用 AI 建議的數值匯出\n選擇【否(No)】: 放棄 AI 建議，統統保留原始空白或原數值\n選擇【取消(Cancel)】: 退回檢查"
            )
            if resp is None: return
            accept_ai = resp
            
            # Clean records based on choice
            for r in records:
                for k, v in r.items():
                    if "[系統建議:" in v:
                        if accept_ai:
                            match = re.search(r"系統建議: (.*?)\]", v)
                            cleaned = match.group(1).strip() if match else v.split("]")[0]
                            r[k] = cleaned
                        else:
                            # Revert to original
                            match = re.search(r"\] 原:(.*)", v)
                            cleaned = match.group(1).strip() if match else ""
                            r[k] = cleaned
            
        # 智能分流邏輯
        presets = get_setting("layout_presets", {})
        
        # 預先讀取關鍵字規則
        preset_rules = []
        for p_name, p_config in presets.items():
            if p_name == "預設主表單": continue
            kw_str = p_config.get("keywords", "").strip()
            if kw_str:
                kws = [k.strip().lower() for k in kw_str.split(",") if k.strip()]
                if kws: preset_rules.append((p_name, kws))
                
        # 分類資料
        routed_groups = {} # dict of config_name -> list of records
        
        import os
        for r in records:
            # 建立檢索字串
            row_text = " ".join([str(v).lower() for v in r.values() if v])
            matched_preset = None
            for p_name, kws in preset_rules:
                if any(kw in row_text for kw in kws):
                    matched_preset = p_name
                    break
                    
            if not matched_preset:
                matched_preset = "預設主表單"
                
            if matched_preset not in routed_groups:
                routed_groups[matched_preset] = []
            routed_groups[matched_preset].append(r)

        # 選擇存檔資料夾
        target_dir = filedialog.askdirectory(title="選擇智能分流匯出的儲存資料夾")
        if not target_dir: return
        
        try:
            success_count = 0
            for p_name, g_records in routed_groups.items():
                df = pd.DataFrame(g_records)
                p_config = presets.get(p_name, {})
                export_headers = p_config.get("headers", list(self.display_columns))
                
                # 保證所有定義的表頭都存在，即使沒資料
                for h in export_headers:
                    if h not in df.columns:
                        df[h] = ""
                        
                final_cols = [h for h in export_headers]
                df = df[final_cols]
                
                safe_name = "".join(x for x in p_name if x.isalnum() or x in " -_").strip()
                save_path = os.path.join(target_dir, f"{safe_name}_匯出總表.xlsx")
                df.to_excel(save_path, index=False)
                success_count += 1
                
            messagebox.showinfo("成功", f"智能分流匯出完成！\n共生成了 {success_count} 份專屬 Excel 檔案於：\n{target_dir}")
            from services.state_manager import state_manager
            state_manager.clear_records() # Clear after successful export
            self.destroy()
        except Exception as e:
            messagebox.showerror("錯誤", f"匯出失敗: {str(e)}")

    def export_split_excel(self):
        # 彈出小視窗選擇分流欄位
        split_win = ctk.CTkToplevel(self)
        split_win.title("選擇分流匯出欄位")
        split_win.geometry("400x350")
        split_win.grab_set()
        
        ctk.CTkLabel(split_win, text="請選擇要作為『分流關鍵』的欄位：\n(如：依照「訂單備註」或「倉儲」分開存檔)").pack(pady=10)
        
        selected_col = ctk.StringVar(value=self.display_columns[0])
        cb = ctk.CTkComboBox(split_win, values=self.display_columns, variable=selected_col, width=250)
        cb.pack(pady=10)
        
        def start_split():
            col = selected_col.get()
            split_win.destroy()
            
            target_dir = filedialog.askdirectory(title="選擇分流匯出的存檔資料夾")
            if not target_dir: return
            
            # 取得目前的記錄清單
            records = []
            for child in self.tree.get_children():
                row_vals = self.tree.item(child, "values")
                row_dict = {}
                for c, v in zip(self.display_columns, row_vals):
                    v_str = str(v).strip()
                    if v_str.startswith("[!] "): v_str = v_str[4:]
                    # Cleanup AI suggestions if any
                    if "[系統建議:" in v_str:
                        import re
                        match = re.search(r"系統建議: (.*?)\]", v_str)
                        v_str = match.group(1).strip() if match else v_str
                    row_dict[c] = v_str
                records.append(row_dict)
                
            df_full = pd.DataFrame(records)
            custom_header_str = get_setting("custom_export_headers", "")
            export_headers = custom_header_str.split("|||") if custom_header_str else DEFAULT_HEADERS
            final_cols = [h for h in export_headers if h in df_full.columns]
            
            # 分群並匯出
            groups = df_full.groupby(col)
            success_count = 0
            for val, df_group in groups:
                safe_val = "".join(x for x in str(val) if x.isalnum() or x in " -_").strip()
                if not safe_val: safe_val = "未分類"
                
                filename = f"分流匯出_{col}_{safe_val}.xlsx"
                save_path = os.path.join(target_dir, filename)
                
                df_to_save = df_group[final_cols]
                df_to_save.to_excel(save_path, index=False)
                success_count += 1
                
            messagebox.showinfo("成功", f"分流匯出完成！\n共生成了 {success_count} 份 Excel 文件於：\n{target_dir}")
            self.destroy()

        ctk.CTkButton(split_win, text="🚀 開始分流匯出", command=start_split, fg_color="green", height=40).pack(pady=20)

def show_review_window(parent_root, data_records):
    win = ReviewGridWindow(parent_root, data_records)
    win.grab_set()
