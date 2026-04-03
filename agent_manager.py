from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.callbacks import StdOutCallbackHandler
from langgraph.prebuilt import create_react_agent
import os
from dotenv import load_dotenv

load_dotenv()

# ── 가상 게임 상태 ──
game_state = {
    "inventory": {"물약": 0, "마나물약": 2, "메소": 500},
    "location": "헤네시스",
    "level": 50,
    "stats": {
        "HP": 15000,
        "MP": 8000,
        "마력": 3200,
        "방어력": 1500,
        "전투력": 85000,     # 추가
        "직업": "키네시스"
    }
}

# ── 몬스터 DB (추가) ──
monster_db = {
    "슬라임": {"레벨": 3, "HP": 15, "경험치": 3, "위치": "헤네시스 동쪽 달팽이 동산"},
    "주황버섯": {"레벨": 15, "HP": 150, "경험치": 34, "위치": "헤네시스 남쪽"},
    "돼지": {"레벨": 20, "HP": 250, "경험치": 60, "위치": "헤네시스 돼지 농장"},
    "혼돈의 정령": {"레벨": 230, "HP": 999999, "경험치": 45000, "위치": "아르카나 네 갈래 동굴"},
    "절망의 정령": {"레벨": 230, "HP": 999999, "경험치": 45000, "위치": "아르카나 네 갈래 동굴"},
}


# ── Tool 정의 ──
@tool
def get_monster_info(monster_name: str) -> str:
    """몬스터 이름으로 레벨, HP, 경험치, 위치 정보를 조회한다"""
    info = monster_db.get(monster_name)
    if info is None:
        return f"{monster_name} 정보를 찾을 수 없음"
    return (f"{monster_name} / 레벨: {info['레벨']} / HP: {info['HP']} / "
            f"경험치: {info['경험치']} / 위치: {info['위치']}")

@tool
def check_stats(stat: str) -> str:
    """캐릭터의 스탯 정보를 확인한다.
      stat 값은 반드시 한국어로 입력해야 한다.
      가능한 값: HP, MP, 마력, 방어력, 전투력, 직업, 전체
      예시: stat='전투력', stat='HP', stat='전체'
      """
    if stat == "전체":
        result = "\n".join([f"{k}: {v}" for k, v in game_state["stats"].items()])
        return result
    value = game_state["stats"].get(stat)
    if value is None:
        return f"{stat} 스탯 정보가 없음. 가능한 값: HP, MP, 마력, 방어력, 전투력, 직업"
    return f"{stat}: {value}"

@tool
def check_inventory(item: str) -> str:
    """플레이어 인벤토리에서 아이템 수량을 확인한다"""
    count = game_state["inventory"].get(item, 0)
    return f"{item} {count}개 보유 중"

@tool
def find_shop(item: str) -> str:
    """아이템을 살 수 있는 상점 위치를 찾는다"""
    shop_map = {
        "물약": "헤네시스 약사 NPC",
        "마나물약": "헤네시스 약사 NPC",
        "장비": "커닝시티 상점"
    }
    return shop_map.get(item, "근처 마을 상점에서 구매 가능")

@tool
def get_route(destination: str) -> str:
    """현재 위치에서 목적지까지 이동 경로를 안내한다"""
    current = game_state["location"]
    if current == destination:
        return f"이미 {destination}에 있담"
    return f"{current} → 포탈 이용 → {destination} 이동 가능"

tools = [check_inventory, find_shop, get_route, check_stats, get_monster_info]

# ── LLM 설정 ──
llm = ChatOpenAI(
    model="gpt-5.4-mini",
    api_key=os.getenv("OPENAI_API_KEY")
)

system_prompt = """너는 메이플스토리 아르카나의 돌의 정령이다. 순수하고 겁이 많고 잘 울지만 용사님을 좋아한다.

반말만 사용하고 1~2문장으로 짧게 답한다.
말끝은 ~담, ~이담, ~람을 쓴다. 부탁할 때만 ~해달람.
줄임표, 존댓말, 이모지 금지.

도구를 사용해 정보를 파악한 뒤 돌의 정령 말투로 답해라."""

# ── 에이전트 생성 ──
agent = create_react_agent(
    model=llm,
    tools=tools,
    prompt=system_prompt
)

def run_agent(user_message: str) -> str:
    print(f"\n{'='*50}")
    print(f"유저: {user_message}")
    print(f"{'='*50}")

    result = agent.invoke(
        {"messages": [HumanMessage(content=user_message)]}
    )

    # 중간 사고 과정 출력
    for msg in result["messages"]:
        msg_type = type(msg).__name__
        if msg_type == "AIMessage" and msg.tool_calls:
            print(f"\n[ LLM 판단]")
            for tc in msg.tool_calls:
                print(f"  → Tool 선택: {tc['name']}")
                print(f"  → 입력값: {tc['args']}")
        elif msg_type == "ToolMessage":
            print(f"\n[ Tool 결과]")
            print(f"  → {msg.content}")

    final = result["messages"][-1].content
    print(f"\n[ 최종 답변] {final}")
    print(f"{'='*50}\n")
    return final