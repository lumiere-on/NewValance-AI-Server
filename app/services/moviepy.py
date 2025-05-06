from __future__ import annotations
import cv2, os, textwrap
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from moviepy.editor import (
    VideoFileClip, AudioFileClip, TextClip,
    CompositeVideoClip, concatenate_videoclips
)
from moviepy.video.fx.resize import resize

from app.core.logger import logger
from app.services.storage import upload_file, upload_json
from app.services.tags import generate as generate_tags
from app.services.to_request import post_metadata_to_be as meta_payload

FONT_PATH = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
W, H = 1080, 1920

# ──────────────────────────────────────────────
def _wrap(t: str, w: int = 20) -> List[str]:
    return textwrap.wrap(t, width=w)

def _thumbnail(video_path: str, sec: int = 1) -> str:
    clip = VideoFileClip(video_path)
    frame = clip.get_frame(sec)
    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    thumb_path = Path(video_path).with_suffix("_thumbnail.jpg").as_posix()
    cv2.imwrite(thumb_path, frame_bgr)
    logger.info(f"[THUMB] {thumb_path}")
    return thumb_path

def _subclip(mp4: str, subtitle: str) -> CompositeVideoClip | None:
    if not Path(mp4).is_file():
        return None
    base = VideoFileClip(mp4).without_audio()
    padded = resize(base, width=W).on_color((W, H), color=(0,0,0))
    lines = _wrap(subtitle)
    txts = [
        TextClip(
            line, fontsize=50, color="white", font=FONT_PATH,
            stroke_color="black", stroke_width=2, align="center"
        ).set_position(("center", H-300+i*60)).set_duration(padded.duration)
        for i, line in enumerate(lines)
    ]
    return CompositeVideoClip([padded, *txts])

# ──────────────────────────────────────────────
def build_and_upload(
    formal_subs: List[str],
    casual_subs: List[str],
    formal_mp3: str,
    casual_mp3: str,
    article_idx: str,
    news_title: str,
    category_id: str,
    original_url: str,
    published_at: str,
    summary_text: str,
    tags: list[str],
    upload: bool = True,
    video_dir: str | None=None,

) -> Dict[str, Dict[str,str]]:
    """
    반환: {style:{video_url, thumbnail_url}}  (+meta_url)
    """
    
    date = datetime.utcnow().isoformat(timespec='seconds')
    out_dir = Path(f"./output/moviepy/{date}/{article_idx}"); out_dir.mkdir(parents=True, exist_ok=True)

    if video_dir:
        mp4s = sorted(str(p) for p in Path(video_dir).glob("output_*.mp4"))
        # 정상처리 로직
    else:
        mp4s = []  # video가 없는 경우 빈 배열 처리

    # mp4s가 없을 때의 로직 추가
    if not mp4s:
        logger.info("[UPLOAD] TTV 비디오가 없습니다. 음성/썸네일만 업로드 진행합니다.")
        
    results: Dict[str, Dict[str, str]] = {}
    formal_video_url=None
    casual_video_url=None
    f_thumb_url=None
    for style, subs, mp3 in [
        ("formal", formal_subs, formal_mp3),
        ("casual", casual_subs, casual_mp3)
    ]:
        if not Path(mp3).is_file(): continue
        clip = _make_video(mp4s, subs, mp3)
        if not clip: continue
        out_mp4 = out_dir / f"{style}_{article_idx}.mp4"
        clip.write_videofile(out_mp4.as_posix(), codec="libx264", audio_codec="aac")
        clip.close()

        # ── 썸네일
        thumb_local = _thumbnail(out_mp4)

        # ── 업로드
        if upload:
            video_url = upload_file(out_mp4)
            thumb_url = upload_file(thumb_local)
            f_thumb_url = thumb_url
        else:
            video_url, thumb_url = out_mp4.as_posix(), thumb_local

        results[style] = {"video_url": video_url, "thumbnail_url": thumb_url}
        formal_video_url = results.get("formal", {}).get("video_url")
        casual_video_url = results.get("casual", {}).get("video_url")

    # 메타 & 태그 JSON -> BE server
    tags = generate_tags(summary_text)

    if upload and results:
        meta_url = meta_payload(
            {
                "title": news_title,
                "category_id": category_id,
                "original_url": original_url,
                "published_at": published_at,
                "created_at": date,
                "easyVersionUrl": casual_video_url,
                "normalVersionUrl": formal_video_url,
                "thumbnailUrl": f_thumb_url,
                "tags": tags,
            },
            base_name=f"meta_{article_idx}"
        )
        results["meta_url"] = meta_url
    return results

def _make_video(videos, subs, mp3):
    limit = min(len(videos), len(subs))
    subclips = [_subclip(videos[i], subs[i]) for i in range(limit)]
    subclips = [c for c in subclips if c]
    if not subclips: return None
    silent = concatenate_videoclips(subclips)
    audio  = AudioFileClip(mp3)
    return silent.set_audio(audio)
