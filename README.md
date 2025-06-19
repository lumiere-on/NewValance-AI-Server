
````markdown
# 📰 NewValance-AI-Server

> 뉴스 크롤링 → GPT 정제 및 요약 → TTS/TTV → 🎬 숏폼 영상 완성  

---

## 📚 Table of Contents
1. [프로젝트 개요](# 프로젝트 개요)
2. [⚡ AI 파이프라인](#⚡AI 파이프라인)
3. [🗂️ 소스 코드 구조](#️소스코드 구조)
4. [🔧 Install → Build → Execute](#-install-→-build-→-execute)
5. [🗝️ 키값 설정](#️-키비밀값-설정)
6. [🧪 테스트 방법](#-테스트-방법)
7. [📁 샘플 데이터 & DB](#-샘플-데이터--db)
8. [📝 사용 오픈소스](#-사용-오픈소스)

---

## 프로젝트 개요
- **목표** : <무엇을, 왜, 어떻게>
- **주요 기능**
  1. 실시간 뉴스 크롤링 & 요약
  2. TTS(mp3) 및 TTV(영상) 생성
  3. 썸네일·태그 자동 생성 & S3 업로드
- **Tech Stack**  
  - **FastAPI** · Python 3.11  
  - **PyTorch / Diffusers**: CogVideoX-1.5  
  - **Google Cloud TTS**, **OpenAI GPT-4o**

---

## ⚡ AI 파이프라인 한눈에
```mermaid
graph TD
  A[뉴스 크롤러] --> B[GPT 요약 & 프롬프트]
  B --> C[TTS(MP3)]
  B --> D[TTV(Video)]
  C & D --> E[MoviePy 병합·썸네일]
  E --> F[(S3 업로드)]
````

* **GPU 필요 단계** : <br>`services/ttv.py` (CogVideoX 1.5)

  * Colab GPU ✔️ / CPU 시 `SKIP_MODEL_LOAD=1` 로 자동 건너뜀

---

## 🗂️ 소스 코드 구조

```
app/
 ├─ main.py          # FastAPI 엔트리
 ├─ api/             # 라우터 모음
 ├─ services/        # crawler, gpt, tts, ttv, moviepy …
 └─ core/            # 설정, 로거
scripts/
 ├─ execute.py       # FastAPI + ngrok 런처 (Colab 전용)
 └─ colab_fastapi.sh # 쉘 버전 자동 실행
data/                # (옵션) 샘플 뉴스 / 테스트 파일
.env.template        # 키 입력 템플릿
requirements.txt
```

---

## 🔧 Install → Build → Execute

### 🚀 Colab 5-step Quick Start

```bash
# 1) 새 Colab → GPU 런타임
!git init -q
!git clone https://github.com/<USER>/<REPO>.git
%cd <REPO>

# 2) 의존성 설치
!pip install -q -r requirements.txt

# 3) 키 템플릿 복사 후 값 입력
!cp .env.template .env
#  ↓ Colab 좌측 Files 패널에서 .env 열어 키값 채우기

# 4) FastAPI + ngrok 런칭
!python scripts/execute.py    # (≒ uvicorn + ngrok)
```

> 실행 후 `🌐 PUBLIC` URL 과 `🔗 SWAGGER` 링크가 출력됩니다.

### 💻 Local (Docker 없는 경우)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.template .env   # 키 입력
uvicorn app.main:app --reload
```

---

## 🗝️ 키/비밀값 설정

`.env.template` 예시 ↓

```dotenv
# OpenAI
OPENAI_API_KEY=sk-...

# Google Cloud TTS
GOOGLE_APPLICATION_CREDENTIALS=/abs/path/to/tts.json

# AWS S3
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_S3_BUCKET=news-shortform

# (옵션) SKIP_* 토글
# SKIP_MODEL_LOAD=1   # GPU 없을 땐 주석 해제
# SKIP_TTS=1          # TTS 건너뛰기
```

> **필수** 항목만 채우면 됩니다.
> 키 보안상 Git에 올리면 ❌ → `.gitignore` 포함!

---

## 🧪 테스트 방법

```bash
# 1. 헬스 체크
curl http://localhost:8000/

# 2. 파이프라인 1건 실행
curl -X POST http://localhost:8000/api/pipeline/ \
     -H "Content-Type: application/json" \
     -d '{"sections":null,"upload":false,"limit":1,"use_gpu":true}'
```

* Swagger UI (/swagger) 에서도 직접 테스트 가능!

---

## 📁 샘플 데이터 & DB

| 폴더             | 내용                    |
| -------------- | --------------------- |
| `data/sample/` | 예시 뉴스 HTML & JSON     |
| `data/exp/`    | 모델 테스트 결과 (프롬프트·영상)   |
| DB             | S3 버킷에 업로드된 결과 URL 참고 |

---

## 📝 사용 오픈소스

* **[FastAPI](https://github.com/tiangolo/fastapi)** (MIT) – REST 서버
* **[Diffusers](https://github.com/huggingface/diffusers)** (Apache-2.0) – CogVideoX 파이프라인
* **[torch-ao](https://github.com/pytorch/ao)** – int8 양자화
* **[MoviePy](https://github.com/Zulko/moviepy)** – 영상 병합
* 기타 라이선스는 `requirements.txt` 참고

````

---

### 📂 추가 파일: `.env.template`
```dotenv
# === API Keys (fill yours) ===
OPENAI_API_KEY=
GOOGLE_APPLICATION_CREDENTIALS=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_S3_BUCKET=

# === Optional Flags ===
# SKIP_MODEL_LOAD=1   # GPU 없으면 TTV 스킵
# SKIP_TTS=1          # TTS 스킵
````

### 🚀 추가 파일: `scripts/execute.py`

```python
import os, subprocess, threading, time, nest_asyncio
from pyngrok import ngrok

# FastAPI 백그라운드
def run_uvicorn():
    proc = subprocess.Popen(
        ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in proc.stdout:
        print("🖥️", line.rstrip())

threading.Thread(target=run_uvicorn, daemon=True).start()

# 서버 부팅 대기
print("⏳  FastAPI booting…")
import requests, urllib3
urllib3.disable_warnings()
while True:
    try:
        requests.get("http://127.0.0.1:8000", timeout=1, verify=False); break
    except Exception: time.sleep(1)
print("✅  FastAPI up!")

# ngrok 연결
nest_asyncio.apply()
ngrok.set_auth_token(os.getenv("NGROK_AUTHTOKEN", ""))
public_url = ngrok.connect(8000).public_url
print("🌐 PUBLIC :", public_url)
print("🔗 SWAGGER:", public_url + "/swagger")

# 유지
while True:
    time.sleep(300)
```

> **실행**
>
> ```bash
> !export NGROK_AUTHTOKEN="2Oxxx..."  # Colab 셀
> !python scripts/execute.py
> ```

README 그대로 넣고 키·프로젝트 정보만 바꾸면 누구나 Colab에서 바로 재현할 수 있어요! 🥳
필요한 수정점 있으면 편하게 알려주세요 💬
