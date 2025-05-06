from fastapi import APIRouter
from capstone.api import create_shortform

api_router = APIRouter()
api_router.include_router(create_shortform.router, prefix = "/create_toS3", tags = ["create_toS3"])