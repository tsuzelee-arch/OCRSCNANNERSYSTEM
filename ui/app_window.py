import customtkinter as ctk
import os
import shutil
import threading
from tkinter import filedialog, messagebox

from processing.excel_parser import parse_excel_file
from processing.ocr_engine import process_image
from processing.data_aggregator import aggregate_and_flag_data
from ui.review_grid import show_review_window
from ui.dict_manager import open_dict_manager
from ui.template_manager import open_template_manager
from ui.ocr_template_manager import open_ocr_template_manager
from ui.summary_config import open_summary_config
from database.db_manager import set_setting, get_setting, DB_PATH
from core.config import CONFIG_FILE, get_excel_passwords, set_excel_passwords

from services.ocr_service import OCRService
from services.backup_service import BackupService
from services.state_manager import state_manager
from core.exceptions import OCRError, BackupRestoreError

def open_settings(parent):
    win = ctk.CTkToplevel(parent)
    win.title("系統設定 (Settings)")
    win.geometry("550x550")
    win.wait_visibility()
    win.grab_set()
    
    settings_status = ctk.CTkLabel(win, text="", text_color="green")
    settings_status.pack(pady=(5, 0))
    
    # == APIs ==
    lbl1 = ctk.CTkLabel(win, text="1. Google Gemini API Key (強化版免費 AI OCR)")
    lbl1.pack(pady=(15, 0))
    e1 = ctk.CTkEntry(win, width=450, placeholder_text="請貼上您的 API Key")
    e1.insert(0, get_setting("gemini_api_key", ""))
    e1.pack(pady=5)
    
    def test_api():
        key = e1.get().strip()
        try:
            OCRService.validate_api_key(key)
            messagebox.showinfo("連線成功", "Gemini API 連線測試成功！Key 確認有效。")
        except OCRError as e:
            messagebox.showerror("驗證失敗", str(e))
            
    btn_test = ctk.CTkButton(win, text="測試 API 連線狀態", command=test_api, width=150, fg_color="#F4A460", hover_color="#CD853F")
    btn_test.pack(pady=5)
    
    # == Database Export/Import ==
    lbl3 = ctk.CTkLabel(win, text="1. 系統資料庫轉移 (包含規則、字典、設定)")
    lbl3.pack(pady=(25, 0))
    
    db_frame = ctk.CTkFrame(win, fg_color="transparent")
    db_frame.pack()
    
    def backup_db():
        save_path = filedialog.asksaveasfilename(defaultextension=".zip", initialfile="order_app_backup.zip", title="打包備份系統資料庫與設定檔至...")
        if save_path:
            try:
                BackupService.backup_system(save_path)
                messagebox.showinfo("備份成功", f"資料庫與設定檔已完整備份為壓縮包:\n{save_path}")
            except BackupRestoreError as e:
                messagebox.showerror("備份失敗", str(e))
            
    def restore_db():
        if messagebox.askyesno("警告", "匯入新資料庫將會覆蓋您目前的設定與所有建立的規則、目錄。\n這會徹底讀取備份壓縮包中的內容。是否繼續？"):
            load_path = filedialog.askopenfilename(filetypes=[("ZIP 備份檔", "*.zip")], title="選擇備份的 ZIP 檔案")
            if load_path:
                try:
                    BackupService.restore_system(load_path)
                    messagebox.showinfo("匯入成功", "系統資料庫與設定已成功覆蓋還原！")
                    win.destroy()
                except BackupRestoreError as e:
                    messagebox.showerror("備份匯入失敗", f"復原過程中發生錯誤: {str(e)}")
            
    ctk.CTkButton(db_frame, text="✅ 匯出 (備份) 資料包", width=120, command=backup_db).pack(side="left", padx=5)
    ctk.CTkButton(db_frame, text="🔁 匯入 (覆蓋) 資料包", width=120, fg_color="brown", hover_color="darkred", command=restore_db).pack(side="left", padx=5)
    
    # == Excel Passwords ==
    lbl4 = ctk.CTkLabel(win, text="2. Excel 自動解鎖密碼庫 (一行一個)")
    lbl4.pack(pady=(15, 0))
    p_text = "\n".join(get_excel_passwords())
    p_box = ctk.CTkTextbox(win, width=450, height=100)
    p_box.insert("0.0", p_text)
    p_box.pack(pady=5)

    def save():
        set_setting("gemini_api_key", e1.get().strip())
        p_list = [p.strip() for p in p_box.get("0.0", "end").split("\n") if p.strip()]
        set_excel_passwords(p_list)
        settings_status.configure(text="✅ 設定已儲存！", text_color="green")
        win.after(1000, win.destroy)
        
    ctk.CTkButton(win, text="儲存以上設定", command=save, fg_color="green", hover_color="darkgreen", height=40).pack(pady=20)

class AppWindow:
    def __init__(self, root):
        self.root = root
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.root.title("自動訂單辨識與資料整合系統 (Automated Order App)")
        self.root.geometry("850x750")

        label = ctk.CTkLabel(self.root, text="自動訂單整合平台", font=ctk.CTkFont(size=24, weight="bold"))
        label.pack(pady=(20, 10))

        frame = ctk.CTkFrame(self.root)
        frame.pack(pady=10, padx=60, fill="both", expand=True)

        self.status_label = ctk.CTkLabel(self.root, text="就緒", anchor="w")

        # 上傳區間
        upload_frame = ctk.CTkFrame(frame, fg_color="transparent")
        upload_frame.pack(pady=15, padx=40, fill="x")
        
        btn_upload = ctk.CTkButton(
            upload_frame, text="📁 批量擷取並整合訂單 (Excel / PDF / 圖檔)", font=ctk.CTkFont(size=16), height=60,
            command=self.handle_upload
        )
        btn_upload.pack(fill="x")
        
        append_frame = ctk.CTkFrame(upload_frame, fg_color="transparent")
        append_frame.pack(pady=5, fill="x")
        
        from database.db_manager import get_platforms
        platforms = list(get_platforms().keys())
        self.ocr_mode_var = ctk.StringVar(value="✨ 智能自動辨識 (全推薦)")
        
        ctk.CTkLabel(append_frame, text="圖檔/PDF解析模式:").pack(side="left", padx=(0, 5))
        cb_mode = ctk.CTkComboBox(append_frame, values=["✨ 智能自動辨識 (全推薦)"] + platforms, variable=self.ocr_mode_var, width=180)
        cb_mode.pack(side="left")
        
        self.chk_append_var = ctk.BooleanVar(value=False)
        chk_append = ctk.CTkCheckBox(append_frame, text="附加於目前總表", variable=self.chk_append_var)
        chk_append.pack(side="left", padx=10)
        
        btn_reset = ctk.CTkButton(append_frame, text="清除暫存", fg_color="red", hover_color="darkred", width=80, command=self.reset_records)
        btn_reset.pack(side="right")

        # 核心功能切換
        btn_summary = ctk.CTkButton(
            frame, text="📊 匯總表選擇與必填設定", font=ctk.CTkFont(size=16), height=50, fg_color="#F4A460", hover_color="#CD853F",
            command=lambda: open_summary_config(self.root)
        )
        btn_summary.pack(pady=10, padx=40, fill="x")

        btn_template = ctk.CTkButton(
            frame, text="📑 管理平台格式轉換表", font=ctk.CTkFont(size=16), height=50, fg_color="transparent", border_width=2,
            command=lambda: open_template_manager(self.root)
        )
        btn_template.pack(pady=10, padx=40, fill="x")

        btn_ocr_template = ctk.CTkButton(
            frame, text="📸 管理圖檔 / PDF 辨識模板", font=ctk.CTkFont(size=16), height=50, fg_color="transparent", border_width=2,
            command=lambda: open_ocr_template_manager(self.root)
        )
        btn_ocr_template.pack(pady=10, padx=40, fill="x")

        btn_dict = ctk.CTkButton(
            frame, text="📖 商品目錄與智能對應設定", font=ctk.CTkFont(size=16), height=50, fg_color="transparent", border_width=2,
            command=lambda: open_dict_manager(self.root)
        )
        btn_dict.pack(pady=10, padx=40, fill="x")
        
        btn_settings = ctk.CTkButton(
            frame, text="⚙️ 系統設定 (換電腦備份 / 輸入 AI Key / 自訂輸出格式)", font=ctk.CTkFont(size=14), height=40, fg_color="gray",
            command=lambda: open_settings(self.root)
        )
        btn_settings.pack(pady=10, padx=40, fill="x")
        
        btn_export = ctk.CTkButton(
            frame, text="📊 檢視校對與匯出總表", font=ctk.CTkFont(size=16), height=60, fg_color="green", hover_color="darkgreen",
            command=self.show_export
        )
        btn_export.pack(pady=30, padx=40, fill="x")

        self.status_label.pack(fill="x", side="bottom", padx=20, pady=10)
        
    def reset_records(self):
        state_manager.clear_records()
        self.status_label.configure(text="已清除：後台資料已全數淨空。")

    def handle_upload(self):
        file_paths = filedialog.askopenfilenames(
            title="選擇訂單文件",
            filetypes=[("All Supported", "*.xlsx;*.xls;*.png;*.jpg;*.pdf"), ("Excel Files", "*.xlsx;*.xls"), ("Images/PDF", "*.png;*.jpg;*.pdf")]
        )
        if not file_paths:
            return
        
        # 讀取主畫面上的模式設定
        mode_val = self.ocr_mode_var.get()
        template_name = None if mode_val == "✨ 智能自動辨識 (全推薦)" else mode_val
        
        self.status_label.configure(text=f"處理中: 0/{len(file_paths)}")
        threading.Thread(target=lambda: self.execute_processing(file_paths, template_name), daemon=True).start()

    def execute_processing(self, file_paths, ocr_template_name):
        all_records = []
        errors = []
        for i, path in enumerate(file_paths):
            ext = os.path.splitext(path)[1].lower()
            if ext in ['.xlsx', '.xls']:
                result = parse_excel_file(path)
            else:
                result = process_image(path, ocr_template_name)
                
            if result.get('status') == 'success':
                all_records.extend(result['data'])
            else:
                err_msg = result.get('message', '未知錯誤')
                print(f"Failed to process {path}: {err_msg}")
                errors.append(f"{os.path.basename(path)}: {err_msg}")
                    
            self.root.after(0, lambda c=i+1, t=len(file_paths): self.status_label.configure(text=f"處理中: {c}/{t}"))
            
        final_records = aggregate_and_flag_data(all_records)
        
        # Append Logic
        if self.chk_append_var.get() and state_manager.get_records():
            state_manager.append_records(final_records)
        else:
            state_manager.set_records(final_records)
        
        def finish():
            if errors:
                err_text = "\n".join(errors[:3])
                if len(errors) > 3: err_text += "\n...與其他錯誤"
                messagebox.showwarning("部分解析無法完成", f"有 {len(errors)} 個檔案無法處理:\n{err_text}")
                
            self.status_label.configure(text=f"處理完成！共計 {len(state_manager.get_records())} 筆紀錄。")
            
            # Automatically jump to review window if there are records
            if state_manager.get_records():
                self.show_export()
            
        self.root.after(0, finish)
        
    def show_export(self):
        records = state_manager.get_records()
        if not records:
            messagebox.showwarning("警告", "尚未上傳並解析任何檔案！請先至少匯入一份訂單。")
        else:
            show_review_window(self.root, records)

def run_app():
    root = ctk.CTk()
    app = AppWindow(root)
    root.mainloop()

if __name__ == "__main__":
    run_app()
