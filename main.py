import os
import re
import time
import notion_client
import google.generativeai as genai
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

# --- 환경 변수 및 클라이언트 초기화 ---
def init_clients():
    """환경 변수를 불러와 API 클라이언트를 초기화합니다."""
    notion_api_key = os.getenv("NOTION_API_KEY")
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not notion_api_key or not gemini_api_key: raise ValueError("API 키가 .env 파일에 설정되지 않았습니다.")
    notion = notion_client.Client(auth=notion_api_key)
    genai.configure(api_key=gemini_api_key)
    gemini_model = genai.GenerativeModel('models/gemini-pro-latest')
    return notion, gemini_model

# --- Notion 관련 함수 ---
def get_existing_topics(notion: notion_client.Client, db_id: str) -> list[str]:
    """Notion 데이터베이스에서 모든 페이지의 제목을 가져와 목록으로 반환합니다."""
    print("기존 주제 목록을 Notion에서 가져옵니다...")
    try:
        all_results = []
        has_more = True
        start_cursor = None
        while has_more:
            response = notion.databases.query(database_id=db_id, start_cursor=start_cursor, page_size=100)
            all_results.extend(response.get("results"))
            has_more = response.get("has_more")
            start_cursor = response.get("next_cursor")
        topic_list = []
        for res in all_results:
            title_property = res.get("properties", {}).get("주제", {})
            title_list = title_property.get("title", [])
            if title_list:
                topic_list.append(title_list[0].get("plain_text", ""))
        print(f"   총 {len(topic_list)}개의 기존 주제를 찾았습니다.")
        return topic_list
    except Exception as e:
        print(f"   Notion에서 주제 목록을 가져오는 중 오류 발생: {e}")
        return []

def parse_rich_text(text: str) -> list:
    """인라인 마크다운(bold, italic, code)을 파싱하여 rich_text 배열을 생성합니다."""
    parts = re.split(r'(\*\*.*?\*\*|\*.*?\*|`.*?`)', text)
    rich_text = []
    for part in parts:
        if not part: continue
        annotations = {}
        content = part
        if part.startswith('**') and part.endswith('**'):
            annotations['bold'] = True
            content = part[2:-2]
        elif part.startswith('*') and part.endswith('*'):
            annotations['italic'] = True
            content = part[1:-1]
        elif part.startswith('`') and part.endswith('`'):
            annotations['code'] = True
            content = part[1:-1]
        rich_text.append({"type": "text", "text": {"content": content}, "annotations": annotations})
    return rich_text

def markdown_to_blocks(markdown_text: str) -> list:
    """Markdown 텍스트를 Notion 블록 객체 리스트로 변환합니다."""
    blocks = []
    lines = markdown_text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('## '):
            blocks.append({"type": "heading_2", "heading_2": {"rich_text": parse_rich_text(line[3:])}})
        elif line.startswith('### '):
            blocks.append({"type": "heading_3", "heading_3": {"rich_text": parse_rich_text(line[4:])}})
        elif line.startswith('#### '):
            blocks.append({"type": "heading_3", "heading_3": {"rich_text": parse_rich_text(line[5:])}})
        elif line.startswith('```'):
            code_lines = []
            language = line[3:].strip()
            i += 1
            while i < len(lines) and not lines[i].startswith('```'):
                code_lines.append(lines[i])
                i += 1
            content = '\n'.join(code_lines)
            for j in range(0, len(content), 1900):
                chunk = content[j:j+1900]
                blocks.append({"type": "code", "code": {"rich_text": [{"type": "text", "text": {"content": chunk}}], "language": language if language else "plaintext"}})
        elif re.match(r'^\s*([\*\-\+])\s', line):
            blocks.append({"type": "bulleted_list_item", "bulleted_list_item": {"rich_text": parse_rich_text(re.sub(r'^\s*([\*\-\+])\s', '', line))}})
        elif re.match(r'^\s*\d+\.\s', line):
            blocks.append({"type": "numbered_list_item", "numbered_list_item": {"rich_text": parse_rich_text(re.sub(r'^\s*\d+\.\s', '', line))}})
        elif line.strip():
            for j in range(0, len(line), 1900):
                chunk = line[j:j+1900]
                blocks.append({"type": "paragraph", "paragraph": {"rich_text": parse_rich_text(chunk)}}
)
        i += 1
    return blocks

def publish_to_notion(notion: notion_client.Client, db_id: str, topic: str, content_md: str, category: str, keywords: list):
    """생성된 콘텐츠를 Notion 데이터베이스에 게시합니다."""
    print(f'\"{topic}\" 주제를 Notion에 게시합니다...')
    try:
        properties = {
            "주제": {"title": [{"text": {"content": topic}}]},
            "카테고리": {"select": {"name": category}},
            "핵심 키워드": {"multi_select": [{"name": kw} for kw in keywords]},
        }
        children = markdown_to_blocks(content_md)
        notion.pages.create(parent={"database_id": db_id}, properties=properties, children=children)
        print(f"   ✅ \"{topic}\" 게시 완료!")
    except Exception as e:
        print(f"   ❌ Notion 게시 중 오류 발생: {e}")

# --- Gemini 관련 함수 (분리된 호출로 변경) ---
def generate_new_topic(model, existing_topics: list[str], category: str) -> str:
    """AI가 여러 줄로 답하더라도 첫 줄만 사용하도록 수정"""
    print(f'\'{category}\' 카테고리에서 새로운 주제를 생성합니다...')
    prompt = f"""당신은 CS 지식 블로그의 전문 튜터입니다. '{category}' 카테고리에 대한 구체적이고 흥미로운 블로그 포스트 주제를 제안해주세요. 아래 목록은 이미 존재하는 주제이니, 겹치지 않게 해주세요. 반드시 단 하나의 주제명만, 다른 어떤 설명도 없이 간결하게 한 줄로 출력해주세요.\n\n[기존 주제 목록]: {', '.join(existing_topics)}"""
    try:
        response = model.generate_content(prompt)
        first_line = response.text.split('\n')[0].strip().replace('**', '').replace('*', '')
        new_topic = re.sub(r'^\s*([\*\-\+])\s*', '', first_line)
        print(f"   새 주제 생성 완료: {new_topic}")
        return new_topic
    except Exception as e:
        print(f"   ❌ 새 주제 생성 중 오류: {e}")
        return None

def generate_content(model, topic: str) -> str:
    """주제에 대한 상세 콘텐츠를 생성합니다."""
    print(f'\"{topic}\"에 대한 콘텐츠를 생성합니다...')
    prompt = f"""당신은 CS 지식 블로그의 전문 튜터입니다. '{topic}' 주제에 대해, 독자가 이해하기 쉬운 상세한 블로그 글을 Markdown 형식으로 작성해주세요. [정의, 핵심 원리, 장단점, 활용 사례, 코드 예제, 요약] 등의 구조를 포함하고, 소제목은 '##'로 구분하며, 중요한 용어는 '**'로 강조해주세요."""
    try:
        response = model.generate_content(prompt)
        print("   콘텐츠 생성 완료.")
        return response.text
    except Exception as e:
        print(f"   ❌ 콘텐츠 생성 중 오류: {e}")
        return None

def generate_keywords(model, topic: str, content: str) -> list:
    """콘텐츠에 맞는 키워드를 생성합니다."""
    print("게시글에 대한 핵심 키워드를 생성합니다...")
    prompt = f"""아래 CS 기술 블로그 글의 핵심 키워드를 3~5개만 쉼표(,)로 구분하여 나열해주세요.\n\n주제: {topic}\n내용 일부: {content[:500]}...\n\n[출력 형식] 키워드1,키워드2,키워드3"""
    try:
        response = model.generate_content(prompt)
        keywords = [kw.strip() for kw in response.text.split(',')]
        print(f"   생성된 키워드: {keywords}")
        return keywords
    except Exception as e:
        print(f"   ❌ 키워드 생성 중 오류: {e}")
        return []

# --- 메인 로직 ---
def main():
    """메인 실행 함수"""
    print("CS Tutor 자동화 스크립트를 시작합니다.")
    try:
        notion, gemini_model = init_clients()
        db_id = os.getenv("NOTION_DATABASE_ID")
        if not db_id: raise ValueError("DB ID가 .env에 없습니다.")

        num_posts_to_create = 1
        category = "네트워크"

        existing_topics = get_existing_topics(notion, db_id)

        for i in range(num_posts_to_create):
            print(f"\n--- {i+1}/{num_posts_to_create}번째 글 생성 시작 ---")
            
            new_topic = generate_new_topic(gemini_model, existing_topics, category)
            if not new_topic: continue
            
            print("   (API 호출 제한을 피하기 위해 30초 대기...)")
            time.sleep(30)

            content_md = generate_content(gemini_model, new_topic)
            if not content_md: continue

            print("   (API 호출 제한을 피하기 위해 30초 대기...)")
            time.sleep(30)

            keywords = generate_keywords(gemini_model, new_topic, content_md)
            
            existing_topics.append(new_topic)
            publish_to_notion(notion, db_id, new_topic, content_md, category, keywords)

    except ValueError as e:
        print(f"오류: {e}")
    except Exception as e:
        print(f"예상치 못한 오류가 발생했습니다: {e}")
    
    print("\n스크립트 실행을 완료했습니다.")

if __name__ == "__main__":
    main()
