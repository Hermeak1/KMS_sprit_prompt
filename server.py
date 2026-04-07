from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import crawler
import NPC_manager

# init
print("아르카나 데이터 수집 중...")
collection = crawler.setup_collection()
NPC_manager.init(collection)
print("서버 준비 완료!")

app = FastAPI(title="아르카나 돌의 정령 API")

# Unity 등 외부 클라이언트 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# 요청/응답 스키마
class ChatRequest(BaseModel):
    message: str
    session_id: str = "extend"   # 추후 멀티 유저 확장용


class ChatResponse(BaseModel):
    reply: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


# 세션별 히스토리 관리
sessions: dict[str, list] = {}


# 엔드포인트
@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="메시지가 비어 있습니다.")

    # 세션별 히스토리 주입
    NPC_manager.history = sessions.get(req.session_id, [])

    try:
        reply, usage = NPC_manager.chat(req.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # 히스토리 저장
    sessions[req.session_id] = NPC_manager.history

    return ChatResponse(
        reply=reply,
        prompt_tokens=usage["prompt_tokens"],
        completion_tokens=usage["completion_tokens"],
        total_tokens=usage["total_tokens"],
    )


@app.delete("/session/{session_id}")
async def reset_session(session_id: str):
    sessions.pop(session_id, None)
    return {"status": "ok", "session_id": session_id}


@app.get("/health")
async def health():
    return {"status": "ok"}


# ── 실행 ──────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080)
