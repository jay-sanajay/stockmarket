"""Daily AI assistant (Gemini)."""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from config import get_gemini_api_key
from dependencies.deps import get_current_user_optional
from models.db_models import User
from services import gemini_service

router = APIRouter(prefix="/assistant", tags=["assistant"])


class ChatBody(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    context: str | None = Field(default=None, max_length=8000)


@router.post("/chat")
def assistant_chat(
    body: ChatBody,
    user: Annotated[User | None, Depends(get_current_user_optional)],
):
    if not get_gemini_api_key():
        return {"reply": "Configure GEMINI_API_KEY on the server to enable the assistant."}
    uid = f"user {user.id}" if user else "guest"
    prompt = f"""You are JayQuant, a concise Indian equity dashboard assistant ({uid}). 
Answer in plain English. Not investment advice. Use short paragraphs or bullets.

Question:
{body.message}
"""
    if body.context:
        prompt += f"\nOptional context from the app:\n{body.context[:6000]}\n"
    try:
        reply = gemini_service.generate_text(prompt, context="assistant_chat").strip()
    except Exception as e:
        return {"reply": f"Assistant error: {e!s}"}
    return {"reply": reply}
