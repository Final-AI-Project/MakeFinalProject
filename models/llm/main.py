# quick_demo.py
import asyncio
from src.orchestrator import plant_talk, talk_for_db
from src.db import save_chat, get_chat_history

CASES = [
    # 1) 일상 + moisture → hybrid 기대
    ("hybrid 기대", "선인장", "오늘 직장상사한테 털려서 기분 안좋음 근데 너 잎 상태가 안좋네", 22.0),
    # 2) 식물 강신호 + moisture → plant 기대
    ("plant 기대",  "보스턴고사리", "잎 끝이 갈변하고 시들어 보여",         22.0),
    # 3) 일상 only + moisture 없음 → daily 기대
    ("daily 기대",  "스파티필럼", "회사일 때문에 스트레스 받았어",        None),
]

def _short(s: str, n: int = 120) -> str:
    return s if len(s) <= n else s[:n].rstrip() + "…"

async def run():
    print("=== LLM 채팅 테스트 ===")
    for title, species, text, moisture in CASES:
        r = plant_talk(species, text, moisture)
        print(f"\n[{title}]")
        print(f"- 입력: species={species} | moisture={moisture} | text='{text}'")
        print(f"- 결과: mode={r.mode} | state={r.state}")
        print(f"- reply: {_short(r.reply)}")

    print("\n=== DB 저장 테스트 ===")
    # DB 저장 예시
    try:
        chat_data = talk_for_db(
            user_id="test_user_001",
            plant_id=1,
            plant_name="우리집 호접란",
            species="호접란",
            user_content="너 잘 자라고 있지? 오늘 날씨가 좋아서 기분이 좋아!",
            user_title="호접란과의 즐거운 대화",  # 사용자가 입력한 제목
            moisture=22.0,
            hashtag="#호접란 #일상 #기분좋음",
            weather="맑음"
        )
        
        diary_id = await save_chat(chat_data)
        print(f"✅ 채팅이 DB에 저장되었습니다. diary_id: {diary_id}")
        print(f"- 제목: {chat_data['user_title']}")
        print(f"- 모드: {chat_data['mode']}")
        print(f"- 해시태그: {chat_data['hashtag']}")
        print(f"- 날씨: {chat_data['weather']}")
        
        # 저장된 채팅 기록 조회
        print("\n=== 저장된 채팅 기록 조회 ===")
        history = await get_chat_history("test_user_001", limit=5)
        for i, record in enumerate(history, 1):
            print(f"\n[{i}] {record['user_title']}")
            print(f"    작성일: {record['created_at']}")
            print(f"    사용자: {_short(record['user_content'])}")
            print(f"    식물: {_short(record['plant_content'])}")
            if record['hashtag']:
                print(f"    해시태그: {record['hashtag']}")
            if record['weather']:
                print(f"    날씨: {record['weather']}")
                
    except Exception as e:
        print(f"❌ DB 저장 중 오류 발생: {e}")
        print("💡 .env 파일에 올바른 DB 설정이 있는지 확인해주세요.")

if __name__ == "__main__":
    asyncio.run(run())
