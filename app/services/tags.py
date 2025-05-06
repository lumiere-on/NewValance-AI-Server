from __future__ import annotations
import os, json, re
from openai import OpenAI
from app.core.logger import logger
from typing import List

_MODEL = "gpt-4o-mini"
_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

_PREDEFINED = """
정치-국회,선거,정부,법원,대통령,보수,진보,비리,외교,안보,지방자치,시위
사회-교육,복지,노동,환경,여성,청년,노인,장애인,의료,범죄,교통
경제-주식,부동산,투자,금리,산업,환율,세금,GDP,수출입,일자리,소득
IT/과학-인공지능,빅데이터,블록체인,클라우드,사물인터넷,메타버스,가상현실,증강현실,데이터센터,해킹,과학,스마트폰
국제-미국,중국,일본,유럽,중동,북한,러시아,UN,전쟁,난민,기후협약,국제법
생활/문화-예술,영화,음악,공연,문학,전통,역사,건축,패션,문화유산,날씨
"""

_SYS = "You are a Korean news‑tagging assistant. 4개의 태그만 JSON 배열로 반환하세요."

def generate(summary: str) -> List[str]:
    prompt = f"""
<미리 정의된 태그>
{_PREDEFINED}

<기사 요약>
{summary}

1. 위 목록에서 가장 연관성 높은 태그 1개를 고르고
2. 새로운 태그 3개를 만들어
3. 총 4개 태그를 JSON 배열만으로 응답하세요 (예: ["대통령","예산안","환경단체","기후위기"])
"""
    res = _client.chat.completions.create(
        model=_MODEL,
        messages=[{"role":"system","content":_SYS},
                  {"role":"user","content":prompt}],
        temperature=0.5,
        max_tokens=100,
    )
    txt = res.choices[0].message.content

    txt = re.sub(r'```(?:json)?', '', txt).replace('```', '').strip()

    try:
        return json.loads(txt)
    except Exception:
        logger.warning(f"[TAG] JSON 파싱 실패 → raw: {txt}")

        txt = re.sub(r"[\[\]]","",txt).strip()
        return [item.strip('" ') for item in txt.split(",")]