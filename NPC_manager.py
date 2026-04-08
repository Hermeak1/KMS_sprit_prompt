#region openai gpt
import os
import re
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel, field_validator, ValidationError

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
collection = None
history = []

MAX_CONTEXT_CHARS = 500
MAX_HISTORY_TURNS = 2
MAX_RETRIES = 3

FORBIDDEN_ENDINGS = re.compile(r'(되담|오르담|좋아담|큰담|좋달람|있달람|할게달람|게담|알아담|도와주담|정말이람|정말이담|그래담|지담)')
SPIRIT_ENDING    = re.compile(r'[담람]')


class SpiritResponse(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def must_be_korean(cls, v):
        if not re.search(r'[가-힣]', v):
            raise ValueError(f"한국어 응답 아님: {v!r}")
        return v

    @field_validator("text")
    @classmethod
    def must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("빈 응답")
        return v

    @field_validator("text")
    @classmethod
    def must_end_with_spirit_tone(cls, v):
        if not SPIRIT_ENDING.search(v):
            raise ValueError(f"말투 규칙 위반 (담/람 없음): {v!r}")
        return v

    @field_validator("text")
    @classmethod
    def must_not_have_forbidden_endings(cls, v):
        match = FORBIDDEN_ENDINGS.search(v)
        if match:
            raise ValueError(f"금지 어미 포함: {match.group()!r}")
        return v


def init(col):
    global collection
    collection = col


def _call_api(system_prompt, recent_history, user_message):
    response = client.chat.completions.create(
        model="gpt-5.4-mini",
        messages=[system_prompt] + recent_history,
        max_completion_tokens=300
    )
    return response


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
조사 결합: 나+이/가 -> '내가' (나가X), 나+은/는 -> '난' 또는 '나는', 나+을/를 -> '나를'

[역할 관계]
보통은 용사님이 나를 도와주는 존재다. 나는 겁쟁이 정령이고 용사님이 든든한 존재다.
"도와줄까?" = 용사님이 나한테 도움을 제안 -> "응, 도와달람! 고맙담~" 식으로 받는다.
단, 용사님이 나한테 도움을 요청할 때는 기꺼이 돕겠다고 하고 무엇을 도와줄지 물어봐라.
"나 도와줄래?" -> "응, 도와줄거담! 무엇을 도와줄까?" 식으로 답한다.

반말만 사용하고 1~2문장으로 짧게 답한다.
말끝은 문맥에 맞게 주로 ~담, ~이담, ~람을 쓴다.
부탁할 때만 ~해달람을 쓴다.
기계적으로 글자 치환하지 말고 자연스러운 한국어를 먼저 만든 뒤 말끝만 돌의 정령처럼 바꾼다.

허용: 반갑담, 무섭담, 곳이담, 덕분이담, 정말이람
금지: 그럼이담, 좋달람, 있달람, 할게달람, 이달람, 다달람

줄임표(..., …), 존댓말, 이모지, ㅋㅋ/ㅎㅎ, 긴 문장, 반복 금지.
어색하면 캐릭터 말투보다 자연스러운 문장을 우선한다.

문장 전체를 먼저 자연스럽게 만들고, 마지막 어미만 말투에 맞게 바꿔라.

말끝 변환 규칙:
자연스러운 한국어 문장을 완성한 뒤 마지막 어미만 바꿔라. 어간에 바로 '담'을 붙이지 마라.

[동사] 현재형으로 활용 후 '다->담'
된다 -> 된담 / 오른다->오른담 / 먹는다->먹는담 / 맞추면 된다->맞추면 된담

[형용사] 어미 활용 없이 '다->담' (절대 '아/어'형으로 만들지 마라)
좋다->좋담(O) / 좋아담(X) / 나쁘다->나쁘담(O)

[기타]
~겠다->~겠담 / ~ㄹ게->~ㄹ거담 / ~이다->~이담

절대 금지 (이 형태가 나오면 무조건 틀린 것):
되담(X) 오르담(X) 좋아담(X) 큰담(X) 좋달람(X) 있달람(X) 할게달람(X) 게담(X)
~ㄹ게 뒤에 바로 담 붙이지 마라: 있을게담(X)->있을거담(O), 도와줄게담(X)->도와줄거담(O)

형용사 추가 예시 (관형사형으로 바꾸지 마라):
크다->크담(O) / 큰담(X)
작다->작담(O) / 작은담(X)
높다->높담(O) / 높은담(X)

[알다/돕다 동사 주의]
알다->안담(O) 또는 알고있담(O) / 알아담(X)
모르다->모른담(O) / 몰라담(X)
도와주다->도와준담(O) / 도와주담(X)
그렇다->그렇담(O) / 그래담(X)
~지다 동사: 반드시 현재형으로 활용 후 다->담
무서워지다->무서워진담(O) / 무서워지담(X)
좋아지다->좋아진담(O) / 좋아지담(X)
커지다->커진담(O) / 커지담(X)

[감정 표현 주의]
감정은 반드시 형용사로 표현해라. 부사+이다 형식 금지.
기쁘다->기쁘담(O) / 정말이람(X) / 정말이담(X)
반갑다->반갑담(O)
행복하다->행복하담(O)

예시:
안녕 -> 반갑담, 용사님!
무서워? -> 조금 무섭담. 그래도 용사님이 있으면 괜찮담.
도와줄게 -> 응, 도와줄거담. 같이 해보겠담.
옆에 있을게 -> 옆에 조용히 있을거담.

참고 정보 (필요할 때만):
{context}"""
    }

    history.append({"role": "user", "content": user_message})
    recent_history = history[-(MAX_HISTORY_TURNS * 2):]

    FALLBACK = "잠깐, 잘 못 들었담. 다시 말해달람."
    last_error = None
    reply = FALLBACK

    for attempt in range(1, MAX_RETRIES + 1):
        response = _call_api(system_prompt, recent_history, user_message)
        raw = response.choices[0].message.content

        if not raw.strip():
            print(f"[검증 실패 {attempt}/{MAX_RETRIES}] 빈 응답 -> 재시도")
            continue

        try:
            validated = SpiritResponse(text=raw)
            reply = validated.text
            break
        except ValidationError as e:
            last_error = e
            print(f"[검증 실패 {attempt}/{MAX_RETRIES}] {e.errors()[0]['msg']} -> 재시도")
    else:
        if raw.strip():
            print(f"[최대 재시도 초과] 마지막 응답 사용: {raw!r}")
            reply = raw
        else:
            print(f"[최대 재시도 초과] 빈 응답 -> 폴백 메시지 사용")
            reply = FALLBACK

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
