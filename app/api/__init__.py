from fastapi import APIRouter
from .endpoints import crawl, summarize, tts, ttv, moviepy, pipeline   # ← pipeline 추가

api_router = APIRouter()
api_router.include_router(crawl.router)
api_router.include_router(summarize.router)
api_router.include_router(tts.router)
api_router.include_router(ttv.router)
api_router.include_router(moviepy.router)
api_router.include_router(pipeline.router)          # NEW
