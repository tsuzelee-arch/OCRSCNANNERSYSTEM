import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError
from core.logger import logger
from core.exceptions import OCRError

class OCRService:
    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """
        測試 Gemini API Key 是否有效。
        若無效或連線失敗，會拋出 OCRError。
        """
        if not api_key:
            raise OCRError("API Key 不能為空！")
        
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-flash-latest')
            response = model.generate_content("Ping")
            if getattr(response, 'text', None):
                logger.info("Gemini API 連線測試成功。")
                return True
            else:
                raise OCRError("Gemini API 測試連線失敗：未回傳預期內容。")
        except GoogleAPIError as e:
            logger.error(f"GoogleAPIError: {e}")
            raise OCRError(f"API 驗證失敗。請確認 Key 是否正確或是否存在地區/流量限制。\n詳細錯誤: {str(e)}")
        except Exception as e:
            logger.error(f"未知的 API 連線錯誤: {e}")
            raise OCRError(f"未知錯誤: {str(e)}")
