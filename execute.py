import os, subprocess, threading, time, nest_asyncio
from pyngrok import ngrok

# 1) FastAPI 백그라운드 ----------------------------------------
def run_uvicorn():
    proc = subprocess.Popen(
        ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    for line in proc.stdout:
        print("🖥️", line.rstrip())

threading.Thread(target=run_uvicorn, daemon=True).start()
# 2) 서버 부팅 대기 -------------------------------------------
print("⏳  FastAPI booting…")
while True:
    try:
        import requests, urllib3
        urllib3.disable_warnings()
        requests.get("http://127.0.0.1:8000", timeout=1, verify=False)
        break
    except Exception:
        time.sleep(1)
print("✅  FastAPI up!")

# 3) ngrok 터널 연결 ------------------------------------------
nest_asyncio.apply()
public_url = ngrok.connect(8000).public_url
print("🌐 PUBLIC  :", public_url)
print("🔗 SWAGGER :", public_url + "/swagger")

# 셀 끊기지 않도록 대기 (필요하면 다른 셀에서 API 호출)
while True:
    time.sleep(300)
