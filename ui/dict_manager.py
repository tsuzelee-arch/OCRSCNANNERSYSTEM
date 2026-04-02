import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox
import tkinter as tk
import pandas as pd
from database.db_manager import add_catalog_item, get_catalog, delete_catalog_item, update_catalog_item, clear_product_catalog

class CatalogManagerWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("商品目錄與智能對應設定")
        self.geometry("800x600")
        
        self.wait_visibility()
        self.grab_set()
        self.editing_id = None
        
        self.lbl = ctk.CTkLabel(self, text="管理系統自訂商品目錄", font=ctk.CTkFont(size=20, weight="bold"))
        self.lbl.pack(pady=10)
        
        add_frame = ctk.CTkFrame(self)
        add_frame.pack(fill="x", padx=20, pady=10)
        
        self.entry_name = ctk.CTkEntry(add_frame, placeholder_text="商品官方名稱 (例: ASUS 筆電)", width=200)
        self.entry_name.pack(side="left", padx=5)
        
        self.entry_tags = ctk.CTkEntry(add_frame, placeholder_text="擷取關鍵字 (以逗號分隔, 例: 華碩,ROG)", width=250)
        self.entry_tags.pack(side="left", padx=5, fill="x", expand=True)
        
        self.entry_item_no = ctk.CTkEntry(add_frame, placeholder_text="綁定商品貨號 (例: P-123)", width=150)
        self.entry_item_no.pack(side="left", padx=5)
        
        self.btn_add = ctk.CTkButton(add_frame, text="新增目錄項目", width=100, command=self.add_entry_cmd, fg_color="green", hover_color="darkgreen")
        self.btn_add.pack(side="left", padx=5)
        
        list_frame = ctk.CTkFrame(self)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.tree = ttk.Treeview(list_frame, columns=("ID", "Name", "Tags", "ItemNo"), show="headings")
        self.tree.heading("ID", text="編號")
        self.tree.heading("Name", text="商品名稱")
        self.tree.heading("Tags", text="對應關鍵字標籤")
        self.tree.heading("ItemNo", text="系統專屬貨號")
        
        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Name", width=200)
        self.tree.column("Tags", width=300)
        self.tree.column("ItemNo", width=150, anchor="center")
        
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<ButtonRelease-1>", self.on_tree_select)
        
        sb = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=sb.set)
        sb.pack(side="right", fill="y")
        
        # Bottom controls
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(pady=10)
        
        self.btn_cancel_edit = ctk.CTkButton(bottom_frame, text="取消修改", fg_color="gray", command=self.reset_edit_state)
        # 隱藏取消按鈕，直到進入編輯模式才顯示
        self.btn_cancel_edit.pack(side="left", padx=10)
        self.btn_cancel_edit.pack_forget()
        
        btn_del = ctk.CTkButton(bottom_frame, text="刪除選定目錄", width=120, fg_color="red", hover_color="darkred", command=self.del_entry_cmd)
        btn_del.pack(side="left", padx=5)
        
        btn_clear = ctk.CTkButton(bottom_frame, text="🗑️ 徹底清空目錄庫", width=140, fg_color="black", hover_color="gray", command=self.clear_all_cmd)
        btn_clear.pack(side="left", padx=5)
        
        btn_import = ctk.CTkButton(bottom_frame, text="📥 從 Excel 批次匯入", width=160, fg_color="#4682B4", hover_color="#5F9EA0", command=self.import_excel_cmd)
        btn_import.pack(side="left", padx=5)
        
        self.load_data()
        
    def load_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        data = get_catalog()
        for rec in data:
            self.tree.insert("", "end", values=(rec['id'], rec['product_name'], rec['tags'], rec['item_no']))
            
    def reset_edit_state(self):
        self.editing_id = None
        self.btn_add.configure(text="新增目錄項目", fg_color="green", hover_color="darkgreen")
        self.entry_name.delete(0, tk.END)
        self.entry_tags.delete(0, tk.END)
        self.entry_item_no.delete(0, tk.END)
        self.btn_cancel_edit.pack_forget()
            
    def on_tree_select(self, event):
        selection = self.tree.selection()
        if not selection: return
        item = self.tree.item(selection[0])
        vals = item['values']
        
        self.editing_id = vals[0]
        self.entry_name.delete(0, tk.END)
        self.entry_name.insert(0, vals[1])
        
        self.entry_tags.delete(0, tk.END)
        self.entry_tags.insert(0, vals[2])
        
        self.entry_item_no.delete(0, tk.END)
        self.entry_item_no.insert(0, vals[3])
        
        self.btn_add.configure(text="儲存 / 修改", fg_color="#F4A460", hover_color="#CD853F")
        self.btn_cancel_edit.pack(side="left", padx=10)
        
    def add_entry_cmd(self):
        name = self.entry_name.get().strip()
        tags = self.entry_tags.get().strip()
        item_no = self.entry_item_no.get().strip()
        
        if name and item_no:
            if self.editing_id is not None:
                update_catalog_item(self.editing_id, name, tags, item_no)
            else:
                add_catalog_item(name, tags, item_no)
            
            self.reset_edit_state()
            self.load_data()
            
    def del_entry_cmd(self):
        selected = self.tree.selection()
        if not selected: return
        item = self.tree.item(selected[0])
        item_id = item['values'][0]
        delete_catalog_item(item_id)
        if self.editing_id == item_id:
            self.reset_edit_state()
        self.load_data()

    def import_excel_cmd(self):
        filepath = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx *.xls"), ("All Files", "*.*")])
        if not filepath: return
        
        try:
            df = pd.read_excel(filepath)
            cols = [str(c).lower() for c in df.columns]
            
            # Map columns by keywords dynamically
            name_col = next((c for c in df.columns if any(k in str(c) for k in ['名稱', '品名', '商品', 'name'])), None)
            tags_col = next((c for c in df.columns if any(k in str(c) for k in ['標籤', '關鍵字', 'tags', 'alias', '關聯', '小名'])), None)
            item_no_col = next((c for c in df.columns if any(k in str(c) for k in ['貨號', '編號', 'item', 'sku', 'id'])), None)
            
            if not name_col or not item_no_col:
                messagebox.showerror("格式錯誤", "找不到適用的欄位！請確認 Excel 內包含「名稱(Name)」、「貨號(SKU)」之類的標題列。")
                return
            
            # Check for overwrite vs append
            resp = messagebox.askyesnocancel("匯入模式選擇", "是否要【覆寫 (清空舊資料並匯入新的)】原有資料？\n\n選【是(Yes)】: 清除當前資料庫，僅保留本次匯入的新資料。\n選【否(No)】: 保留舊有資料，將新資料疊加進去。\n選【取消(Cancel)】: 終止匯入操作。")
            if resp is None: return
            
            if resp: # Yes = overwite
                clear_product_catalog()
                
            success_count = 0
            for idx, row in df.iterrows():
                name = str(row[name_col]).strip() if pd.notna(row[name_col]) else ""
                item_no = str(row[item_no_col]).strip() if pd.notna(row[item_no_col]) else ""
                tags = str(row[tags_col]).strip() if tags_col and pd.notna(row[tags_col]) else ""
                
                if name and item_no:
                    add_catalog_item(name, tags, item_no)
                    success_count += 1
            
            self.load_data()
            messagebox.showinfo("匯入成功", f"成功批次匯入了 {success_count} 筆商品目錄設定！")
        except Exception as e:
            messagebox.showerror("匯入失敗", f"讀取或寫入過程發生錯誤:\n{str(e)}")

    def clear_all_cmd(self):
        if messagebox.askyesno("嚴重警告", "您確定要徹底「清空」本系統所有的自訂商品目錄嗎？\n一旦清空無法還原！"):
            clear_product_catalog()
            self.load_data()
            messagebox.showinfo("已清空", "商品目錄已全數還原為無。")


def open_dict_manager(parent):
    CatalogManagerWindow(parent)
