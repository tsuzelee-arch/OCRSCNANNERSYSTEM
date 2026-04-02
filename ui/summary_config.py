import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
from core.config import DEFAULT_HEADERS, get_setting, set_setting

class SummaryConfigWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("📊 匯總表分流導出與欄位設定")
        self.geometry("950x750")
        
        self.wait_visibility()
        self.grab_set()
        
        # Data State
        self.all_headers = list(DEFAULT_HEADERS)
        self.presets = get_setting("layout_presets", {})
        
        # 確保至少有一個預設配置
        if "預設主表單" not in self.presets:
            legacy_headers_str = get_setting("custom_export_headers", "")
            legacy_headers = legacy_headers_str.split("|||") if legacy_headers_str else list(DEFAULT_HEADERS)
            self.presets["預設主表單"] = {
                "headers": legacy_headers,
                "important": get_setting("important_fields", []),
                "keywords": ""
            }

        self.current_preset_name = "預設主表單"
        self.selected_headers = []
        self.important_fields = []
        
        self.setup_ui()
        self.refresh_preset_list()
        self.load_preset_data("預設主表單")
        
    def setup_ui(self):
        ctk.CTkLabel(self, text="匯出表單管理與智能分流設定", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=10)
        
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # == Left Panel (List of Presets) ==
        left_frame = ctk.CTkFrame(main_frame, width=250)
        left_frame.pack(side="left", fill="y", padx=10, pady=10)
        left_frame.pack_propagate(False)
        
        ctk.CTkLabel(left_frame, text="表單配置清單", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        
        self.preset_listbox = ttk.Treeview(left_frame, columns=("Name",), show="headings", height=20)
        self.preset_listbox.heading("Name", text="配置名稱")
        self.preset_listbox.column("Name", width=200, anchor="w")
        self.preset_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.preset_listbox.bind("<<TreeviewSelect>>", self.on_preset_select)
        
        btn_frame_left = ctk.CTkFrame(left_frame, fg_color="transparent")
        btn_frame_left.pack(fill="x", pady=5)
        
        ctk.CTkButton(btn_frame_left, text="➕ 新增配置", command=self.add_preset, width=100).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame_left, text="🗑 刪除", fg_color="#D32F2F", command=self.delete_preset, width=80).pack(side="right", padx=5)

        # == Right Panel (Settings) ==
        right_frame = ctk.CTkFrame(main_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        # Name and Keywords
        config_head_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        config_head_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(config_head_frame, text="目前編輯:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.lbl_current_preset = ctk.CTkLabel(config_head_frame, text="預設主表單", font=ctk.CTkFont(weight="bold", text_color="#F4A460"))
        self.lbl_current_preset.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        ctk.CTkLabel(config_head_frame, text="觸發關鍵字 (逗號分隔):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.entry_keywords = ctk.CTkEntry(config_head_frame, placeholder_text="輸入關鍵字以自動分流至此表單", width=300)
        self.entry_keywords.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Columns Manage
        ctk.CTkLabel(right_frame, text="步驟2: 選擇需要匯出的欄位與是否必填", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        
        self.scroll_frame = ctk.CTkScrollableFrame(right_frame)
        self.scroll_frame.pack(side="top", fill="both", expand=True, padx=5, pady=5)
        
        # Checkbox variables and UI elements
        self.column_widgets = []

        # Control Buttons
        btn_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkButton(btn_frame, text="📁 從 Excel 抽取標題", fg_color="brown", command=self.import_from_excel).pack(side="left", padx=15)
        
        ctk.CTkButton(btn_frame, text="💾 儲存此配置設定", fg_color="#4682B4", hover_color="#5F9EA0", command=self.save_current_preset).pack(side="right", padx=5)

        # Final Action (Save All to Database)
        ctk.CTkButton(self, text="✅ 關閉並套用所有變更", font=ctk.CTkFont(weight="bold"), height=45, fg_color="green", hover_color="darkgreen", command=self.final_save).pack(pady=10, padx=40, fill="x")

    def refresh_preset_list(self):
        for item in self.preset_listbox.get_children():
            self.preset_listbox.delete(item)
        for p_name in self.presets.keys():
            self.preset_listbox.insert("", "end", iid=p_name, values=(p_name,))
            
        # Select current
        if self.current_preset_name in self.presets:
            self.preset_listbox.selection_set(self.current_preset_name)

    def on_preset_select(self, event):
        selected = self.preset_listbox.selection()
        if not selected: return
        p_name = selected[0]
        if p_name != self.current_preset_name:
            # Auto save currently edited one before switching
            self.sync_order_from_tree()
            self.presets[self.current_preset_name] = {
                "headers": list(self.selected_headers),
                "important": list(self.important_fields),
                "keywords": self.entry_keywords.get().strip()
            }
            # Switch
            self.load_preset_data(p_name)

    def load_preset_data(self, name):
        self.current_preset_name = name
        self.lbl_current_preset.configure(text=name)
        preset = self.presets.get(name, {})
        
        self.selected_headers = list(preset.get("headers", self.all_headers))
        self.important_fields = list(preset.get("important", []))
        
        self.entry_keywords.delete(0, 'end')
        self.entry_keywords.insert(0, preset.get("keywords", ""))
        
        if name == "預設主表單":
            self.entry_keywords.configure(state="disabled", placeholder_text="預設表單不需關鍵字")
            self.entry_keywords.delete(0, 'end')
        else:
            self.entry_keywords.configure(state="normal", placeholder_text="輸入關鍵字以自動分流至此表單")
            
        self.refresh_tree()

    def add_preset(self):
        from tkinter import simpledialog
        name = simpledialog.askstring("新增配置", "請輸入新表單配置名稱:")
        if name and name not in self.presets:
            self.presets[name] = {
                "headers": list(DEFAULT_HEADERS),
                "important": [],
                "keywords": ""
            }
            self.refresh_preset_list()
            self.preset_listbox.selection_set(name)
            self.load_preset_data(name)
        elif name in self.presets:
            messagebox.showwarning("警告", "配置名稱已存在。")

    def delete_preset(self):
        selected = self.preset_listbox.selection()
        if not selected: return
        p_name = selected[0]
        
        if p_name == "預設主表單":
            messagebox.showwarning("警告", "無法刪除預設主表單！")
            return
            
        if messagebox.askyesno("確認", f"確定要刪除配置 '{p_name}' 嗎？"):
            del self.presets[p_name]
            self.current_preset_name = "預設主表單"
            self.refresh_preset_list()
            self.load_preset_data("預設主表單")

    def refresh_tree(self):
        # Clear existing widgets
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.column_widgets.clear()
            
        # Combine selected and unselected to show all available headers
        all_display = list(self.selected_headers)
        for h in self.all_headers:
            if h not in all_display:
                all_display.append(h)
                
        # Header row
        header_frame = ctk.CTkFrame(self.scroll_frame, fg_color="#E0E0E0")
        header_frame.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(header_frame, text="欄位名稱", width=250, anchor="w", text_color="black").pack(side="left", padx=10)
        ctk.CTkLabel(header_frame, text="決定匯出", width=80, text_color="black").pack(side="left", padx=10)
        ctk.CTkLabel(header_frame, text="設為必填", width=80, text_color="black").pack(side="left", padx=10)
        ctk.CTkLabel(header_frame, text="排序", width=120, text_color="black").pack(side="right", padx=10)

        for idx, h in enumerate(all_display):
            self.create_column_row(h, idx)

    def create_column_row(self, col_name, idx):
        row_frame = ctk.CTkFrame(self.scroll_frame)
        row_frame.pack(fill="x", pady=2)
        
        ctk.CTkLabel(row_frame, text=col_name, width=250, anchor="w").pack(side="left", padx=10)
        
        var_export = ctk.BooleanVar(value=(col_name in self.selected_headers))
        var_important = ctk.BooleanVar(value=(col_name in self.important_fields))
        
        chk_export = ctk.CTkCheckBox(row_frame, text="", variable=var_export, width=80)
        chk_export.pack(side="left", padx=10)
        
        chk_important = ctk.CTkCheckBox(row_frame, text="", variable=var_important, width=80, fg_color="red")
        chk_important.pack(side="left", padx=10)
        
        btn_down = ctk.CTkButton(row_frame, text="⬇️", width=40, command=lambda cn=col_name: self.move_item(cn, 1))
        btn_down.pack(side="right", padx=5)
        
        btn_up = ctk.CTkButton(row_frame, text="⬆️", width=40, command=lambda cn=col_name: self.move_item(cn, -1))
        btn_up.pack(side="right", padx=5)
        
        self.column_widgets.append({
            "name": col_name,
            "export_var": var_export,
            "important_var": var_important
        })

    def move_item(self, col_name, direction):
        self.sync_order_from_tree() # ensure unselected ones are synced too
        
        all_display = list(self.selected_headers)
        for h in self.all_headers:
            if h not in all_display:
                all_display.append(h)
                
        try:
            idx = all_display.index(col_name)
        except ValueError:
            return
            
        new_idx = idx + direction
        if 0 <= new_idx < len(all_display):
            all_display.insert(new_idx, all_display.pop(idx))
            
        # rebuild selected_headers based on the new order so UI respects it
        new_selected = []
        for h in all_display:
            if h in self.selected_headers:
                new_selected.append(h)
                
        self.selected_headers = new_selected
        self.all_headers = all_display
        self.refresh_tree()

    def sync_order_from_tree(self):
        new_selected = []
        new_important = []
        for widget_info in self.column_widgets:
            col_name = widget_info["name"]
            if widget_info["export_var"].get():
                new_selected.append(col_name)
            if widget_info["important_var"].get():
                new_important.append(col_name)
        self.selected_headers = new_selected
        self.important_fields = new_important

    def import_from_excel(self):
        filepath = filedialog.askopenfilename(title="從空白 Excel 抽取標題:", filetypes=[("Excel", "*.xlsx;*.xls")])
        if filepath:
            try:
                df = pd.read_excel(filepath, nrows=0)
                new_cols = list(df.columns)
                self.selected_headers = new_cols
                # Merge into all_headers if missing
                for c in new_cols:
                    if c not in self.all_headers:
                        self.all_headers.append(c)
                self.refresh_tree()
                messagebox.showinfo("成功", "已成功讀取匯出樣板的標題列！")
            except Exception as e:
                messagebox.showerror("失敗", f"讀取失敗: {str(e)}")

    def save_current_preset(self):
        self.sync_order_from_tree()
        self.presets[self.current_preset_name] = {
            "headers": list(self.selected_headers),
            "important": list(self.important_fields),
            "keywords": self.entry_keywords.get().strip()
        }
        set_setting("layout_presets", self.presets)
        messagebox.showinfo("成功", f"此配置 '{self.current_preset_name}' 已經暫存！")

    def final_save(self):
        # Auto save current
        self.sync_order_from_tree()
        self.presets[self.current_preset_name] = {
            "headers": list(self.selected_headers),
            "important": list(self.important_fields),
            "keywords": self.entry_keywords.get().strip()
        }
        
        # Save to DB
        set_setting("layout_presets", self.presets)
        
        # 為了向下相容某些直接讀 custom_export_headers 的系統（避免崩潰），將「預設主表單」同步給它
        default_p = self.presets.get("預設主表單", {})
        set_setting("custom_export_headers", "|||".join(default_p.get("headers", [])))
        set_setting("important_fields", default_p.get("important", []))
        
        messagebox.showinfo("完成", "所有匯出表單配置已儲存完畢！")
        self.destroy()

def open_summary_config(parent):
    SummaryConfigWindow(parent)
