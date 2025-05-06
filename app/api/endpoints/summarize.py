from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services import gpt

class SummarizeIn(BaseModel):
    article: str

router = APIRouter(prefix="/summarize", tags=["GPT"])

@router.post("/", summary="기사 요약 & 프롬프트 생성")
async def summarize(body: SummarizeIn):
    try:
        cleaned = gpt.refine_news(body.article)
        formal, casual = gpt.mk_TTS_prompt(cleaned)
        ttv_prompt = gpt.mk_TTV_prompt(formal)
        return {
            "formal": formal,
            "casual": casual,
            "ttv_prompt": ttv_prompt
        }
    except Exception as e:
        raise HTTPException(500, str(e))
