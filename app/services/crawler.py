from __future__ import annotations
import time, logging, sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from selenium import webdriver
from selenium.webdriver.common.by import By

from app.core.logger import logger

SECTIONS = {
    "100": 1, #정치
    "101": 2, #경제
    "102": 6, #사회
    "103": 4, #생활/문화
    "104": 3, #세계
    "105": 5, #IT/과학
}
def _get_driver(headless: bool = True) -> webdriver.Chrome:
    opts = webdriver.ChromeOptions()
    if headless:
        opts.add_argument("--headless=new")   # 구버전 Chrome이면 "--headless"로 변경
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("lang=ko_KR")
    return webdriver.Chrome(options=opts)     # Selenium 4.20+ → driver auto-download

def crawl_headlines(sections: List[str]|None=None) -> List[Dict]:
    """
    섹션별 헤드라인(제목+URL)만 우선 수집
    """
    drv = _get_driver()
    date_str = datetime.utcnow().strftime("%Y%m%d")
    res, base, idx = [], "https://news.naver.com/section/", 0
    try:
        for sec in sections or SECTIONS:
            drv.get(base + sec); 
            time.sleep(1.5)
            for art in drv.find_elements(By.CSS_SELECTOR,"a.sa_text_title"):
                res.append({
                    "index": idx,
                    "date": date_str,
                    "section": SECTIONS.get(sec,sec),
                    "url": art.get_attribute("href"),
                    "title": art.find_element(By.TAG_NAME,"strong").text.strip()
                }); 
                idx+=1
        logger.info(f"[HEAD] total {len(res)} collected")
        return res
    finally: drv.quit()

def enrich_articles(news_list: List[Dict]) -> List[Dict]:
    drv = _get_driver()
    try:
        for itm in news_list:
            drv.get(itm["url"]); 
            time.sleep(1.5)

            # 본문
            try:
                txt = drv.find_element(By.ID,"dic_area").text
                itm["content"]=" ".join(t.strip() for t in txt.split("\n") if t.strip())
            except: itm["content"]=""
            # 입력시간
            try:
                raw = drv.find_element(
                    By.CSS_SELECTOR,
                    'span.media_end_head_info_datestamp_time._ARTICLE_DATE_TIME'
                ).get_attribute("data-date-time") # 예: "2025-02-28T12:23:00"

                # 문자열을 datetime 객체로 변환
                parsed_date = datetime.fromisoformat(raw)

                # 다시 ISO 8601 형식으로 문자열 변환 (T 포함)
                iso_date = parsed_date.isoformat(timespec='seconds').replace(":", "-") # 👉 결과: "2025-02-28T12:23:00"

                itm["published_at"] = iso_date
                logger.info("ISO 형식으로 변환 완료")

            except: itm["published_at"]=""

            logger.debug(f"[ENRICH] idx={itm['index']} published_at={itm['published_at']}")
        logger.info("[CRAWL] enrichment done")
        return news_list
    finally: drv.quit()

if __name__ == "__main__":
    heads = crawl_headlines()
    full = enrich_articles(heads)

    import pandas as pd
    out = Path(f"./output/crawling/news_data_{datetime.utcnow():%Y%m%d}.csv")
    pd.DataFrame(full).to_csv(out, index=False, encoding="utf-8-sig")
    print(f"CSV saved → {out.resolve()}")
