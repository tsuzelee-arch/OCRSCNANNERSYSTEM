import json
import os
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Any

from core.logger import logger
from core.exceptions import ConfigError

def get_app_root() -> str:
    """取得應用程式的根目錄"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 決定設定檔路徑
MODE = os.environ.get("ORDER_APP_MODE", "dev")
CONFIG_NAME = "order_ocr_config.json" if MODE == "dev" else "order_ocr_config_trial.json"
CONFIG_FILE = os.path.join(get_app_root(), CONFIG_NAME)

DEFAULT_HEADERS = [
    "訂單號碼", "訂單備註", "送貨方式", "收件人", "郵政編號（如適用)", 
    "門市名稱", "商品貨號", "商品名稱", "選項", "數量", "完整地址", 
    "出貨備註", "全家服務編號 / 7-11 店號", "電郵", "收件人電話號碼", 
    "付款總金額", "貨運編號", "倉儲"
]

@dataclass
class AppSettings:
    gemini_api_key: str = ""
    custom_export_headers: str = ""
    important_fields: List[str] = field(default_factory=list)
    layout_presets: Dict[str, Any] = field(default_factory=dict)
    excel_passwords: List[str] = field(default_factory=lambda: ["roommi2020", "Haoo2021"])

@dataclass
class AppConfigModel:
    settings: AppSettings = field(default_factory=AppSettings)
    templates: Dict[str, dict] = field(default_factory=dict)
    ocr_templates: Dict[str, dict] = field(default_factory=dict)

class ConfigManager:
    """單例模式管理全域配置"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._load_from_disk()
        return cls._instance

    def _load_from_disk(self):
        self.cached_raw_data = {
            "settings": {
                "gemini_api_key": "",
                "custom_export_headers": "",
                "important_fields": [],
                "layout_presets": {},
                "excel_passwords": ["roommi2020", "Haoo2021"]
            },
            "templates": {},
            "ocr_templates": {}
        }
        
        if not os.path.exists(CONFIG_FILE):
            logger.info(f"設定檔 {CONFIG_FILE} 不存在，使用預設值。")
            self._save_to_disk()
            return
        
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                if "settings" not in config: config["settings"] = {}
                if "templates" not in config: config["templates"] = {}
                if "ocr_templates" not in config: config["ocr_templates"] = {}
                
                # 保留所有原始與新增欄位
                self.cached_raw_data.update(config)
        except Exception as e:
            logger.error(f"無法讀取設定檔 {CONFIG_FILE}，使用預設值。錯誤: {e}")
            self._save_to_disk()

    def _save_to_disk(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.cached_raw_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"儲存設定檔發生錯誤: {e}")
            raise ConfigError(f"無法儲存設定檔: {e}")

    # 封裝後的對外介面
    def get_setting(self, key: str, default: Any = "") -> Any:
        return self.cached_raw_data["settings"].get(key, default)

    def set_setting(self, key: str, value: Any):
        self.cached_raw_data["settings"][key] = value
        self._save_to_disk()

    def get_templates(self) -> Dict[str, dict]:
        return self.cached_raw_data.get("templates", {})

    def save_template(self, name: str, mapping_dict: dict):
        if "templates" not in self.cached_raw_data:
            self.cached_raw_data["templates"] = {}
        self.cached_raw_data["templates"][name] = mapping_dict
        self._save_to_disk()

    def delete_template(self, name: str):
        if "templates" in self.cached_raw_data and name in self.cached_raw_data["templates"]:
            del self.cached_raw_data["templates"][name]
            self._save_to_disk()

    def get_ocr_templates(self) -> Dict[str, dict]:
        return self.cached_raw_data.get("ocr_templates", {})

    def save_ocr_template(self, name: str, config_dict: dict):
        if "ocr_templates" not in self.cached_raw_data:
            self.cached_raw_data["ocr_templates"] = {}
        self.cached_raw_data["ocr_templates"][name] = config_dict
        self._save_to_disk()

    def delete_ocr_template(self, name: str):
        if "ocr_templates" in self.cached_raw_data and name in self.cached_raw_data["ocr_templates"]:
            del self.cached_raw_data["ocr_templates"][name]
            self._save_to_disk()

    def get_excel_passwords(self) -> List[str]:
        return self.cached_raw_data["settings"].get("excel_passwords", ["roommi2020", "Haoo2021"])

    def set_excel_passwords(self, pw_list: List[str]):
        self.cached_raw_data["settings"]["excel_passwords"] = pw_list
        self._save_to_disk()

# 模組級函式 (維持向下相容)
_config = ConfigManager()

def load_config(): return _config.cached_raw_data
def save_config(config): 
    _config.cached_raw_data = config
    _config._save_to_disk()
def get_setting(key, default=""): return _config.get_setting(key, default)
def set_setting(key, value): return _config.set_setting(key, value)
def get_templates(): return _config.get_templates()
def save_template(name, mapping_dict): return _config.save_template(name, mapping_dict)
def delete_template(name): return _config.delete_template(name)
def get_ocr_templates(): return _config.get_ocr_templates()
def save_ocr_template(name, config_dict): return _config.save_ocr_template(name, config_dict)
def delete_ocr_template(name): return _config.delete_ocr_template(name)
def get_excel_passwords(): return _config.get_excel_passwords()
def set_excel_passwords(pw_list): return _config.set_excel_passwords(pw_list)
