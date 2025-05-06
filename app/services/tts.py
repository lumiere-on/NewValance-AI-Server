"""
services/tts.py
────────────────
Google Cloud TTS
  • synthesize(text, style, out_path)  : 단일 문장 → MP3
  • generate_from_csv(csv_path, ...)   : 배치 생성 (CSV → 많은 MP3)
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple

import pandas as pd
from google.cloud import texttospeech

from app.core.logger import logger
from app.services.storage import upload_file  # S3 업로드 (옵션)

# ──────────────────────────────────────────────────────────────────────────────
# 1. 단일 문장 합성
# ──────────────────────────────────────────────────────────────────────────────
_client = texttospeech.TextToSpeechClient()


def _voice(style: str) -> texttospeech.VoiceSelectionParams:
    return texttospeech.VoiceSelectionParams(
        language_code="ko-KR",
        name="ko-KR-Standard-B" if style == "formal" else "ko-KR-Standard-A",
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
    )


def synthesize(text: str, style: str = "formal", out_path: str | None = None) -> str:
    """
    text  : 한국어 문장
    style : formal / casual
    out_path : 저장 경로 (None이면 ./output/tts/<timestamp>.mp3)

    Returns : 최종 저장 파일 경로
    """
    if style not in {"formal", "casual"}:
        raise ValueError("style must be 'formal' or 'casual'")

    out_path = out_path or f"./output/tts/{datetime.utcnow().timestamp():.0f}.mp3"
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    input_txt = texttospeech.SynthesisInput(text=text)
    audio_cfg = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

    resp = _client.synthesize_speech(
        request={"input": input_txt, "voice": _voice(style), "audio_config": audio_cfg}
    )

    with open(out_path, "wb") as f:
        f.write(resp.audio_content)

    logger.info(f"[TTS] {style} saved → {out_path}")
    return out_path


# ──────────────────────────────────────────────────────────────────────────────
# 2. CSV 배치 처리
# ──────────────────────────────────────────────────────────────────────────────
def _ensure_dir(p: Path) -> None:
    if not p.exists():
        p.mkdir(parents=True, exist_ok=True)


def generate_from_csv(
    csv_path: str,
    date_str: str | None = None,
    upload: bool = False,
    limit: int | None = None,
) -> Dict[str, Dict[str, List[str]]]:
    """
    csv_path : gpt_news_data_YYYYMMDD.csv
    upload   : True → S3 업로드 후 URL 반환
    limit    : 상위 N개 행만 처리 (테스트용)

    Return : {index: {"formal":[...], "casual":[...]}}
    """
    df = pd.read_csv(csv_path)
    if limit:
        df = df.head(limit)

    date_str = date_str or datetime.utcnow().strftime("%Y%m%d")
    base_dir = Path(f"./output/tts/{date_str}")
    _ensure_dir(base_dir)

    styles: List[Tuple[str, str]] = [
        ("formal", "TTS_formal_prompt"),
        ("casual", "TTS_casual_prompt"),
    ]

    results: Dict[str, Dict[str, List[str]]] = {}

    for _, row in df.iterrows():
        idx = str(row["index"])
        idx_dir = base_dir / idx
        _ensure_dir(idx_dir)
        results[idx] = {"formal": [], "casual": []}

        for style, col in styles:
            prompt = row.get(col, "")
            if not isinstance(prompt, str) or not prompt.strip():
                logger.warning(f"[SKIP] idx={idx}, style={style} → 빈 프롬프트")
                continue

            mp3_local = idx_dir / f"{style}.mp3"
            synthesize(prompt, style, mp3_local.as_posix())

            ref = upload_file(mp3_local) if upload else mp3_local.as_posix()
            results[idx][style].append(ref)

    return results


# ──────────────────────────────────────────────────────────────────────────────
# CLI 테스트
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    CSV = "./data/gpt_news_data_20250410.csv"  # 필요 시 수정
    out_dict = generate_from_csv(CSV, upload=False, limit=5)
    print(out_dict)
