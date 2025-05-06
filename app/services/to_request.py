# app/services/be_request.py

import os
import requests
from .logger import logger
from dotenv import load_dotenv

load_dotenv()

BE_SERVER_URL = os.getenv("BE_SERVER_URL", "http://<your-be-ip>:<port>/api/summary")

def post_metadata_to_be(payload: dict) -> bool:
    """
    BE 서버에 메타데이터를 POST 방식으로 전송함
    """
    try:
        response = requests.post(BE_SERVER_URL, json=payload, timeout=5)
        response.raise_for_status()
        logger.info(f"[BE REQUEST] Success → {response.status_code}")
        return True
    except requests.RequestException as e:
        logger.error(f"[BE REQUEST ERROR] {e}")
        return False
