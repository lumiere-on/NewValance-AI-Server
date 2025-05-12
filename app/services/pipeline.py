"""
services/pipeline.py
────────────────────
크롤링 → 본문 enrich → GPT 요약/프롬프트 → TTS → 태그 → 병합/썸네일 → S3 업로드
(한 기사 = formal+casual 두 버전)

변경 내역 ⭐
- GPU 의존적인 TTV 단계 제거
- gpt.mk_tags() 호출로 자동 태그 4개 산출 후 업로드 모듈에 전달
"""

from typing import List
from app.core.logger import logger
from app.services import (
    crawler,
    gpt,
    tts,
    ttv
)
from app.services.moviepy import build_and_upload


def run(sections: List[str] | None = None, upload: bool = True, limit: int = 5):
    """파이프라인 메인 함수

    Parameters
    ----------
    sections : list[str] | None
        네이버 섹션 코드. None 이면 전체 섹션
    upload : bool, default True
        True → S3 업로드, False → 로컬 저장만
    limit : int, default 5
        테스트용 기사 개수 제한
    """

    # 1) 헤드라인 & 기사 본문 -------------------------------------------------
    heads = crawler.crawl_headlines(sections)
    articles = crawler.enrich_articles(heads)[:limit]

    for art in articles:
  
        title = art["title"]
        idx   = str(art["index"])
        section = art["section"]
        news_url = art["url"]
        published_at = art["published_at"]
        
        # 2) GPT 요약 ---------------------------------------------------------
        logger.info("[step] GPT sum start")

        summary = gpt.refine_news(art["content"])
        formal, casual = gpt.mk_TTS_prompt(summary)
        ttv_prompt = gpt.mk_TTV_prompt(formal)

        logger.info("[step] GPT sum end")

        # 3) 태그 추출 --------------------------------------------------------
        logger.info("[step] Extract Tags start")
        tags = gpt.mk_tags(summary)  # ['정치', '대통령', '예산안', '기후위기'] 등
        logger.info("[step] Extract Tags done")

        # 4) TTS 생성 ---------------------------------------------------------
        tts_dir = f"./output/tts_tmp/{idx}"
        logger.info("[STEP] TTS synth start")
        formal_mp3 = tts.synthesize(" ".join(formal), "formal", f"{tts_dir}/formal.mp3")
        casual_mp3 = tts.synthesize(" ".join(casual), "casual", f"{tts_dir}/casual.mp3")

        logger.info("[STEP] TTS synth done")

        # 3) TTV
        video_dir = f"./output/ttv_tmp/{idx}"
        #ttv_paths = ttv.generate(ttv_prompt, article_idx=idx, upload=False, out_dir=video_dir)
        try:
            ttv_paths = ttv.generate(
                ttv_prompt,
                article_idx=idx,
                upload=True,
                out_dir=video_dir,
            )
        except RuntimeError as e:
            msg = str(e)
            if "SKIP_MODEL_LOAD=1" in msg:
                logger.info("🚀 SKIP_MODEL_LOAD, TTV 단계 건너뜀")
                video_dir = None
            else:
                raise  # 그 외 예외는 그대로 터지게

        # 5) 병합 + 썸네일 + 태그 --------------------------------------------
        logger.info("[STEP] build_and_upload start")
        urls = build_and_upload(
            formal_subs   = formal,
            casual_subs   = casual,
            formal_mp3    = formal_mp3,
            casual_mp3    = casual_mp3,
            article_idx   = idx,
            news_title    = title,
            category_id   = section,
            original_url  = news_url,
            published_at  = published_at,
            summary_text  = summary,
            tags          = tags,         
            upload        = upload,
            video_dir     = video_dir        # TTV 제거로 비움/None 처리

        )

        logger.info(f"[PIPE] idx={idx} done → {urls}")
