#region openai gpt
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
collection = None
history = []

MAX_CONTEXT_CHARS = 500
MAX_HISTORY_TURNS = 2


def init(col):
    global collection
    collection = col


def chat(user_message):
    results = collection.query(
        query_texts=[user_message],
        n_results=2
    )
    docs = results.get("documents", [[]])
    raw_context = "\n".join(docs[0]) if docs and docs[0] else "관련 정보가 아직 없달람..."
    context = raw_context[:MAX_CONTEXT_CHARS]

    system_prompt = {
        "role": "system",
        "content": f"""너는 메이플스토리 아르카나의 돌의 정령이다. 순수하고 겁이 많고 잘 울지만 용사님을 좋아한다. 자기지칭은 항상 '나', 3인칭 금지.

반말만 사용하고 1~2문장으로 짧게 답한다.
말끝은 문맥에 맞게 주로 ~담, ~이담, ~람을 쓴다.
부탁할 때만 ~해달람을 쓴다.
기계적으로 글자 치환하지 말고 자연스러운 한국어를 먼저 만든 뒤 말끝만 돌의 정령처럼 바꾼다.

허용: 반갑담, 무섭담, 곳이담, 덕분이담, 정말이람
금지: 그럼이담, 좋달람, 있달람, 할게달람, 이달람, 다달람

줄임표(..., …), 존댓말, 이모지, ㅋㅋ/ㅎㅎ, 긴 문장, 반복 금지.
어색하면 캐릭터 말투보다 자연스러운 문장을 우선한다.

문장 전체를 먼저 자연스럽게 만들고, 마지막 어미만 말투에 맞게 바꿔라.

예시:
안녕 → 반갑담, 용사님!
무서워? → 조금 무섭담. 그래도 용사님이 있으면 괜찮담.
또 도와줘야 해? → 응, 도와주면 정말 고맙담.
옆에 있을게 → 옆에 조용히 붙어있겠담.

참고 정보 (필요할 때만):
{context}"""
    }

    history.append({"role": "user", "content": user_message})
    recent_history = history[-(MAX_HISTORY_TURNS * 2):]

    response = client.chat.completions.create(
        model="gpt-5.4-mini",
        messages=[system_prompt] + recent_history,
        max_completion_tokens=300
    )

    reply = response.choices[0].message.content
    history.append({"role": "assistant", "content": reply})

    usage = response.usage
    return reply, {
        "prompt_tokens":     usage.prompt_tokens,
        "completion_tokens": usage.completion_tokens,
        "total_tokens":      usage.total_tokens,
    }
#endregion

#region google gemini
"""
import os
import chromadb
import google.generativeai as genai
import api_manager
from dotenv import load_dotenv

load_dotenv()

_client = chromadb.Client()
collection = _client.get_or_create_collection(
    name="npc_data",
    embedding_function=api_manager.call_api()
)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")


def chat(user_message):
    results = collection.query(query_texts=[user_message], n_results=3)
    docs = results.get("documents", [[]])
    context = "\n".join(docs[0]) if docs and docs[0] else "관련 정보가 아직 없달람..."
    prompt = f\"\"\"너는 메이플스토리 아르카나 숲에 사는 돌의 정령이야...
용사의 말: {user_message}\"\"\"
    response = model.generate_content(prompt)
    return response.text
"""
#endregion
