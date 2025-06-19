from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from app.core.config import get_settings
from app.api import api_router

settings = get_settings()

app = FastAPI(
    title="📰Shortform Generating by New-valance",
    description="네이버 뉴스 → GPT요약 → TTS/TTV → 병합 → S3 업로드",
    version="1.0.0",
    docs_url="/swagger",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS (필요 시 Origins 조정)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

app.include_router(api_router, prefix="/api")

# API‑Key 보안 헤더 <- 필요하면 쓰기기
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {"type":"apiKey","in":"header","name":"X-API-KEY"}
    }
    for path in schema["paths"].values():
        for op in path.values():
            op.setdefault("security",[{"ApiKeyAuth": []}])
    app.openapi_schema = schema
    return schema

app.openapi = custom_openapi
