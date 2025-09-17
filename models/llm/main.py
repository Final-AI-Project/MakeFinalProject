# quick_demo.py
import asyncio
from src.orchestrator import plant_talk, talk_for_db
# from src.db import save_chat  # DB 쓰면 주석 해제

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
    for title, species, text, moisture in CASES:
        r = plant_talk(species, text, moisture)
        print(f"\n[{title}]")
        print(f"- 입력: species={species} | moisture={moisture} | text='{text}'")
        print(f"- 결과: mode={r.mode} | state={r.state}")
        print(f"- reply: {_short(r.reply)}")

    # --- DB 저장 예시 (필요 시 주석 해제) ---
    # row = talk_for_db(
    #     plant_id=1,
    #     plant_name="우리집 호접란",
    #     species="호접란",
    #     user_content="너 잘 자라고 있지?",
    #     moisture=22.0
    # )
    # await save_chat(row)

if __name__ == "__main__":
    asyncio.run(run())
