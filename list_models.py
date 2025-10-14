import os
import google.generativeai as genai
from dotenv import load_dotenv

def list_available_models():
    """현재 API 키로 사용 가능한 Gemini 모델 목록을 출력합니다."""
    try:
        load_dotenv()
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            print("❌ 오류: .env 파일에서 GEMINI_API_KEY를 찾을 수 없습니다.")
            return

        genai.configure(api_key=gemini_api_key)

        print("사용 가능한 모델 목록:")
        print("------------------------")
        for model in genai.list_models():
            if 'generateContent' in model.supported_generation_methods:
                print(model.name)
        print("------------------------")

    except Exception as e:
        print(f"\n❌ 모델 목록을 가져오는 중 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    list_available_models()

