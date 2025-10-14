import os
from dotenv import load_dotenv
import notion_client

def verify_notion_connection():
    """Notion API 키와 데이터베이스 ID의 유효성을 검사합니다."""
    try:
        # .env 파일에서 환경 변수 로드
        load_dotenv()
        print("1. .env 파일 로드를 시도합니다...")
        notion_api_key = os.getenv("NOTION_API_KEY")
        database_id = os.getenv("NOTION_DATABASE_ID")

        if not notion_api_key or not database_id:
            print("❌ 오류: .env 파일에서 NOTION_API_KEY 또는 NOTION_DATABASE_ID를 찾을 수 없습니다.")
            print("   .env 파일이 Notion_CS_Tutor 폴더 안에 있는지, 변수 이름이 올바른지 확인해주세요.")
            return

        print("   .env 파일 로드 완료.")

        # Notion 클라이언트 초기화
        print("2. Notion 클라이언트 초기화를 시도합니다...")
        notion = notion_client.Client(auth=notion_api_key)
        print("   Notion 클라이언트 초기화 완료.")

        # 데이터베이스 정보 조회를 통해 연결 테스트
        print(f"3. 데이터베이스(ID: {database_id[:4]}...) 연결을 테스트합니다...")
        db_info = notion.databases.retrieve(database_id=database_id)
        db_title = db_info.get("title", [{"plain_text": "(제목 없음)"}])[0].get("plain_text")
        
        print("\n--------------------------------------------------------")
        print(f"✅ 성공! Notion 데이터베이스에 성공적으로 연결했습니다.")
        print(f"   - 데이터베이스 제목: {db_title}")
        print("   - 이제 다음 단계를 진행할 수 있습니다.")
        print("--------------------------------------------------------")

    except notion_client.errors.APIResponseError as e:
        print("\n--------------------------------------------------------")
        print(f"❌ 오류: Notion API가 오류를 반환했습니다. 원인을 확인해주세요.")
        if e.code == "unauthorized":
            print("   - 원인: API 키가 잘못되었습니다. `NOTION_API_KEY`를 다시 확인해주세요.")
        elif e.code == "object_not_found":
            print("   - 원인: 데이터베이스 ID가 잘못되었습니다. `NOTION_DATABASE_ID`를 다시 확인해주세요.")
        elif e.code == "restricted_resource":
            print("   - 원인: 통합(Integration)이 데이터베이스에 초대(공유)되지 않았습니다.")
            print("     Notion 데이터베이스 페이지의 [공유] > [통합 추가]에서 생성한 통합을 추가해주세요.")
        else:
            print(f"   - 오류 코드: {e.code}")
            print(f"   - 오류 메시지: {e.body}")
        print("--------------------------------------------------------")

    except Exception as e:
        print(f"\n❌ 예상치 못한 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    verify_notion_connection()
