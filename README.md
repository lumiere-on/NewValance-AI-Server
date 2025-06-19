# NewValance-AI-Server
## 이화여자대학교 캡스톤디자인과창업프로젝트 3조 쌈뽕워리어즈 AI server
=======

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

## 프로젝트 내 AI 개요
- **목표** : NewValance는 긴 글의 뉴스를 읽을 여유가 없는 현대인들이 빠르고 간편하게 사회 이슈를 습득할 수 있도록 뉴스 숏폼 영상을 제공하는 서비스이다. 뉴스 숏폼 영상은 뉴스 사이트에서 크롤링한 기사 자료를 바탕으로 GPT-4o-mini API를 이용한 텍스트 요약 및 가공, Text-To-Video 모델을 이용한 비디오 생성, Text-To-Speech API를 이용한 음성 생성 과정을 거친 뒤 영상 편집 라이브러리를 통해 위 과정으로 생성된 아웃풋들을 하나의 숏폼 영상으로 합산하여 생성된다
- **주요 기능**
1. 뉴스 크롤링
2. gpt-4o-mini를 이용한 기사 정제 및 요약
3-1. TTS를 이용해 음성 생성
3-2. TTV를 이용해 영상 생성
4. 썸네일·태그 자동 생성 & S3 업로드

---

## ⚡소스 코드 구조
```
app/
 ├─ api/        
  ├─ endpoints          # services에서 정의한 함수들을 endpoint로 실행
  └─ init.py           # router 정의
 ├─ services/        # crawler, gpt, tts, ttv, moviepy …
 ├─ core             # 설정, 로거
 ├─ main.py          # FastAPI 엔트리
 └─ init.py           # fastapi 초기화
requirements.txt      #설치할 라이브러리 및 모듈들 모음
execute.py
```

### 소스 코드 설명 
```
services/
 ├─ crawler.py          # 네이버 뉴스 크롤링
 ├─ gpt.py              #  기사 정체 -> 요약 -> 프롬프트 산출
 ├─ tags.py              # 기사의 태그 산출
 ├─ tts.py              # TTS API로 음성 산출
 ├─ ttv.py              # TTV 모델로 음성 산출
 ├─ moviepy.py           # 음성, 영상, 자막을 하나의 숏폼으로 합산
 ├─ to_request.py       #BE서버에 메타데이터 전송
 ├─ storage.py              # S3에 영상과 썸네일 업로드
 └─logger.py             # 코드 실행 시 로그 산출
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
!python execute.py    # (≒ uvicorn + ngrok)
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
```
---

## 🧪 테스트 방법

```bash
!python execute.py
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


>>>>>>> dev
