
# 📰 NewValance-AI-Server

> 뉴스 크롤링 → GPT 정제 및 요약 → TTS/TTV → 🎬 숏폼 영상 완성  

---

## 📚 Table of Contents
1. [프로젝트 개요]
2. [⚡ AI 파이프라인]
3. [🗂️ 소스 코드 구조]
4. [🔧 Install → Build → Execute]
5. [🗝️ 키 템플릿릿]
6. [🧪 테스트 방법]
7. [📝 사용 오픈소스]

---

## 프로젝트 개요
- **목표** : <무엇을, 왜, 어떻게>
- **주요 기능**
  1. 뉴스 크롤링
  2. gpt-4o-mini를 이용한 기사 정제 및 요약
  3-1. TTS를 이용해 음성 생성
  3-2. TTV를 이용해 영상 생성
  5. 썸네일·태그 자동 생성 & S3 업로드
- **Tech Stack**  
  - **FastAPI** · Python 3.11  
  - **PyTorch / Diffusers**: CogVideoX-1.5  
  - **Google Cloud TTS**, **OpenAI GPT-4o**

---

## ⚡ AI 파이프라인
```mermaid
graph TD
  A[뉴스 크롤링링] --> B[GPT 요약 & 프롬프트]
  B --> C[TTS(MP3)]
  B --> D[TTV(Video)]
  C & D --> E[MoviePy 병합·썸네일]
  E --> F[(S3 업로드)]
````

* **GPU 필요 단계** : <br>`services/ttv.py` (CogVideoX 1.5)

  *본 서버에서는 Colab GPU ✔️를 이용해 코드 실행
  * / CPU로 실행 시 `SKIP_MODEL_LOAD=1` 로 자동 건너뜀

---

## 🗂️ 소스 코드 구조

```
app/
 ├─ main.py          # FastAPI 엔트리
 ├─ api/             # 라우터 모음
 ├─ services/        # crawler, gpt, tts, ttv, moviepy …
 ├─ core             # 설정, 로거
 ├─ main.py          # FastAPI 엔트리
 └─ init.py           # fastapi 초기화

scripts/
 ├─ execute.py       # FastAPI + ngrok 런처 (Colab 전용)
 └─ colab_fastapi.sh # 쉘 버전 자동 실행
requirements.txt
```

---

## 🔧 Install → Build → Execute

```bash
# 1) Colab 노트북 생성 → 런타임을 A100으로 설정
!git init -q
!git clone https://github.com/<USER>/<REPO>.git
%cd <REPO>

# 2) 의존성 설치
!pip install -q -r requirements.txt

# 3) 아래 키 템플릿 복사+붙여넣기 후 키값 입력

# 4) FastAPI + ngrok 런칭
!python scripts/execute.py    # (≒ uvicorn + ngrok)
```

> 실행 후 `🌐 PUBLIC` URL 과 `🔗 SWAGGER` 링크가 출력됩니다.
> Swagger에서 pipeline을 "Try it out"을 눌러 동작을 확인합니다. 

---

## 🗝️ 키 템플릿

```bash
import os, subprocess, textwrap, sys, nest_asyncio, threading, time, pathlib
from pyngrok import ngrok

#Google cloud key path
key_path = "/content/NewValance-AI-Server/app/keys/tts.json"
!assert pathlib.Path(key_path).exists(),
# Google Cloud TTS
os.environ[GOOGLE_APPLICATION_CREDENTIALS]=key_path

#set environment variables
# OpenAI
os.environ[OPENAI API_KEY]="sk-..."

# AWS S3
os.environ[AWS_ACCESS_KEY_ID]="AKIA..."
os.environ[AWS_SECRET_ACCESS_KEY]=...
os.environ[AWS_S3_BUCKET]=...
os.environ["AWS_REGION"] = "ap-northeast-2"
os.environ["S3_BUCKET"] = ...
os.environ["S3_BUCKET_URL]=...

# Moviepy
os.environ["IMAGEMAGICK_BINARY"] = "/usr/bin/convert"
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


## 📝 사용 오픈소스

* **[FastAPI](https://github.com/tiangolo/fastapi)** (MIT) – REST 서버
* **[Selenium]** - 뉴스 크롤링
* **[GPT(gpt-4o-mini)]** - 기사 정제 및 요약, 프롬프트 산출
* **[Google Speech to text]** - TTS API. 프롬프트를 기반으로 음성 산출
* **[Cogvideox1.5-5B]** - TTV momdel. 프롬프트를 기반으로 영상 산출출
* **[MoviePy](https://github.com/Zulko/moviepy)** – 영상 병합
* 기타 라이선스는 `requirements.txt` 참고

````

---


