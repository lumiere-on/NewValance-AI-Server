"""
services/crawler.py
───────────────────
네이버 뉴스 섹션 → 제목·URL·기사 본문·대표이미지·감정·기사입력시간(published_at) 크롤링
- 크롬 드라이버는 chromedriver‑autoinstaller 로 자동 설치
- headless 옵션 기본
"""

from __future__ import annotations
import time, chromedriver_autoinstaller
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager 

from app.core.logger import logger

# ─────────────────────────────────────────────
SECTIONS = {
    "100": 1, #정치
    "101": 2, #경제
    "102": 6, #사회
    "103": 4, #생활/문화
    "104": 3, #세계
    "105": 5, #IT/과학
}

def _get_driver(headless: bool = True) -> webdriver.Chrome:
    chrome_options = webdriver.ChromeOptions()
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("lang=ko_KR")

    service = Service(ChromeDriverManager().install())  
    return webdriver.Chrome(options=chrome_options)

# ─────────────────────────────────────────────
def crawl_headlines(sections: List[str] | None = None) -> List[Dict]:
    """
    섹션별 헤드라인(제목+URL)만 우선 수집
    """
    drv = _get_driver()
    date_str = datetime.utcnow().strftime("%Y%m%d")
    results: List[Dict] = []
    base = "https://news.naver.com/section/"
    try:
        idx = 0
        for sec in sections or SECTIONS.keys():
            drv.get(base + sec)
            time.sleep(1.5)
            for art in drv.find_elements(By.CSS_SELECTOR, "a.sa_text_title"):
                url = art.get_attribute("href")
                title = art.find_element(By.TAG_NAME, "strong").text.strip()
                results.append({
                    "index": idx,
                    "date": date_str,
                    "section": SECTIONS.get(sec, sec),
                    "url": url,
                    "title": title,
                })
                logger.debug(f"[HEAD] ({idx}) {title}")
                idx += 1
        logger.info(f"[CRAWL] headlines collected: {len(results)}")
        return results
    finally:
        drv.quit()

# ─────────────────────────────────────────────
def enrich_articles(news_list: List[Dict]) -> List[Dict]:
    """
    개별 기사 URL 로 이동해 본문, 입력시간 추가
    """
    drv = _get_driver()
    try:
        for item in news_list:
            drv.get(item["url"])
            time.sleep(1.5)

            # ── 본문
            try:
                txt = drv.find_element(By.ID, "dic_area").text
                item["content"] = " ".join(t.strip() for t in txt.split("\n") if t.strip())
                print("본문 내용 크롤링 완료")
            except Exception:
                item["content"] = ""

            # ── 기사 입력시간
            try:
                dt_tag = drv.find_element(
                    By.CSS_SELECTOR,
                    'span.media_end_head_info_datestamp_time._ARTICLE_DATE_TIME'
                )
                raw_date_str = dt_tag.get_attribute("data-date-time")  # 예: "2025-02-28T12:23:00"
    
                # 문자열을 datetime 객체로 변환
                parsed_date = datetime.fromisoformat(raw_date_str)

                # 다시 ISO 8601 형식으로 문자열 변환 (T 포함)
                iso_date = parsed_date.isoformat()  # 👉 결과: "2025-02-28T12:23:00"

                item["published_at"] = iso_date
                print("ISO 형식으로 변환 완료")
            except Exception:
                item["published_at"] = ""

            logger.debug(f"[ENRICH] idx={item['index']} published_at={item['published_at']}")
        logger.info("[CRAWL] enrichment done")
        return news_list
    finally:
        drv.quit()

# ─────────────────────────────────────────────
# CLI 테스트
# ─────────────────────────────────────────────
if __name__ == "__main__":
    heads = crawl_headlines()
    full = enrich_articles(heads)
    import pandas as pd, os
    out = Path(f"./output/crawling/news_data_{datetime.utcnow():%Y%m%d}.csv")
    pd.DataFrame(full).to_csv(out, index=False, encoding="utf-8-sig")
    print(f"CSV saved → {out.resolve()}")
