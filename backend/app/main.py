# backend/app/main.py
from __future__ import annotations

import uuid
import logging
from typing import Optional, Union

import redis
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.app.chat import router as chat_router          # (keep if you still expose /chat/* sub-routes)
from backend.app.config import settings
from backend.app.langgraph_workflow import compiled_chat_graph, ChatState
from langchain_core.messages import AIMessage

# ────────────────────────── Logging ──────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ────────────────────────── FastAPI & CORS ──────────────────────────
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],   # adjust to your frontend(s)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ────────────────────────── Redis ──────────────────────────
redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)

# ────────────────────────── Include other routers (optional) ──────────────────────────
app.include_router(chat_router)

# ────────────────────────── Pydantic models ──────────────────────────
class QueryRequest(BaseModel):
    """
    Front-end must echo the same session_id in every turn of a conversation.
    If omitted on the first turn, the back-end will generate one and return it.
    """
    user_query: str
    session_id: Optional[str] = None


# ────────────────────────── Helper (de)serialisers ──────────────────────────
def _dump_state(state: ChatState) -> str:
    return state.model_dump_json()


def _load_state(raw: Optional[str]) -> Optional[ChatState]:
    if not raw:
        return None
    try:
        return ChatState.model_validate_json(raw)
    except Exception as exc:                     # noqa: BLE001
        logger.error("Failed to parse ChatState JSON from Redis: %s", exc)
        return None


# ────────────────────────── Simple health check ──────────────────────────
@app.get("/")
def root():
    return {"message": "Bot Agent API is running.", "redis_connected": redis_client.ping()}


# ────────────────────────── Main chat endpoint ──────────────────────────
@app.post("/chat/query")
async def chat_query(request: QueryRequest):
    """
    Stateless HTTP endpoint

    • The client supplies `session_id` in the body (or omits it on first turn).
    • ChatState is persisted in Redis under key  chat_state:<session_id>.
    • The updated session_id is echoed back so the client can store it.
    """
    # 1) choose / create session ID
    session_id = request.session_id or str(uuid.uuid4())
    redis_key = f"chat_state:{session_id}"

    # 2) fetch previous ChatState (if any)
    state = _load_state(redis_client.get(redis_key)) or ChatState(messages=[], user_input=None)

    # 3) inject current user message
    state.user_input = request.user_query

    try:
        # 4) run LangGraph
        final_state: ChatState = await compiled_chat_graph.ainvoke(state)

        # 5) save updated state
        redis_client.set(redis_key, _dump_state(final_state))

        # 6) extract assistant reply
        if final_state.messages and isinstance(final_state.messages[-1], AIMessage):
            reply = final_state.messages[-1].content
        else:
            reply = final_state.response or "No response generated."

        # 7) return JSON
        return {"session_id": session_id, "message": reply}

    except Exception as exc:                     # noqa: BLE001
        logger.exception("LangGraph error:")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {exc}") from exc
