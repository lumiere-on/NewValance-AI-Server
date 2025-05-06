# services/ttv.py
# ─────────────────────────────────────────────────────────────────
"""
CogVideoX‑1.5 기반 텍스트‑투‑비디오(TTV) 모듈
- fp16 + 4‑bit NF4 + int8 weight‑only
- ★ GPU가 없거나 SKIP_MODEL_LOAD=1 일 때는 모델을 건너뛴다!
"""
from __future__ import annotations

import os, torch
from datetime import datetime
from pathlib import Path
from typing import List

from diffusers.utils import export_to_video
from app.core.logger import logger
from app.services.storage import upload_file  # S3 업로드용 (필요 없으면 삭제)

# ────────────────────────────────────────────────────────────────
# 1. 전역 캐시 & Lazy‑loader
# ────────────────────────────────────────────────────────────────
_pipe = None   # ★ 최초엔 None

def _load_pipe():
    """★ 필요할 때 한 번만 불러오는 내부 함수"""
    global _pipe
    if _pipe is not None:                       # 이미 로딩됨
        return _pipe

    if os.getenv("SKIP_MODEL_LOAD") == "1":
        raise RuntimeError("🚫 SKIP_MODEL_LOAD=1 로 설정되어 있어 모델을 로드하지 않아요!")

    if not torch.cuda.is_available():
        raise RuntimeError("🚫 GPU(CUDA)가 필요합니다. 로컬 CPU 환경에서는 SKIP_MODEL_LOAD=1을 주고 FastAPI만 테스트하세요!")

    logger.info("⚙️  Loading CogVideoX1.5‑5B … (첫 실행만 시간이 걸려요)")

    from diffusers import (
        AutoencoderKLCogVideoX,
        CogVideoXPipeline,
        CogVideoXTransformer3DModel,
    )
    from torchao.quantization import quantize_, int8_weight_only
    from transformers import BitsAndBytesConfig, T5EncoderModel

    _quant = int8_weight_only
    _bnb_cfg = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
    )

    # text encoder
    _text_enc = T5EncoderModel.from_pretrained(
        "THUDM/CogVideoX1.5-5B",
        subfolder="text_encoder",
        torch_dtype=torch.bfloat16,
    )
    quantize_(_text_enc, _quant())

    # transformer
    _xf = CogVideoXTransformer3DModel.from_pretrained(
        "THUDM/CogVideoX1.5-5B",
        subfolder="transformer",
        torch_dtype=torch.bfloat16,
    )
    quantize_(_xf, _quant())

    # VAE
    _vae = AutoencoderKLCogVideoX.from_pretrained(
        "THUDM/CogVideoX1.5-5B",
        subfolder="vae",
        torch_dtype=torch.bfloat16,
    )
    quantize_(_vae, _quant())

    _pipe = CogVideoXPipeline.from_pretrained(
        "THUDM/CogVideoX1.5-5B",
        text_encoder=_text_enc,
        transformer=_xf,
        vae=_vae,
        torch_dtype=torch.bfloat16,
        quantization_config=_bnb_cfg,
    )
    _pipe.enable_model_cpu_offload()
    _pipe.vae.enable_tiling()
    _pipe.vae.enable_slicing()

    logger.info("✅  CogVideoX 파이프라인 로드 완료!")
    return _pipe

# ────────────────────────────────────────────────────────────────
# 2. 메인 함수
# ────────────────────────────────────────────────────────────────
def generate(
    prompts: List[str],
    article_idx: int | str,
    upload: bool = False,
    out_dir: str | None = None,
) -> List[str]:
    """
    prompt 리스트를 받아 mp4 파일들을 생성해 경로 리스트를 반환
    """
    # ★★ 필요 시 여기서 모델을 처음 로드
    pipe = _load_pipe()

    date_str = datetime.utcnow().strftime("%Y%m%d")
    base_dir = Path(out_dir or f"./output/ttv/{date_str}/{article_idx}")
    base_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"[TTV] output directory → {base_dir}")

    result_paths: List[str] = []

    for i, prompt in enumerate(prompts):
        logger.info(f"[TTV] ({i+1}/{len(prompts)})  {prompt}")

        frames = pipe(
            prompt=prompt,
            num_videos_per_prompt=1,
            num_inference_steps=50,
            num_frames=40,
            guidance_scale=6,
            generator=torch.Generator(device="cuda").manual_seed(42),
        ).frames[0]

        local_mp4 = base_dir / f"output_{i}.mp4"
        export_to_video(frames, local_mp4.as_posix(), fps=8)
        logger.info(f"[TTV] saved → {local_mp4}")
        result_paths.append(local_mp4.as_posix())

    # (선택) S3 업로드
    if upload:
        return [upload_file(p) for p in result_paths]

    return result_paths
