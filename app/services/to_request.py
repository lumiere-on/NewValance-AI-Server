# app/services/be_request.py

import os
import requests
from .logger import logger
from dotenv import load_dotenv

load_dotenv()

BE_SERVER_URL = os.getenv("BE_SERVER_URL")

print(f"{BE_SERVER_URL}")
def post_metadata_to_be(payload: dict) -> bool:
    """
    BE 서버에 메타데이터를 POST 방식으로 전송함
    """
    try:
        response = requests.post(BE_SERVER_URL, json=payload, timeout=5)
        response.raise_for_status()
        print("request.url:", response.request.url)
        print("request.method:", response.request.method)
        print("response.status_code:", response.status_code)
        print("response.history:", response.history)
        logger.info(f"[BE REQUEST] Success → {response.status_code}")
        return True
    except requests.RequestException as e:
        logger.error(f"[BE REQUEST ERROR] {e}")
        return False
