import requests
import json
import os

def send_message(text):
    """
    텔레그램으로 메시지를 보내는 공용 함수
    """
    token = None
    chat_id = None
    
    # secrets.json에서 키 읽기
    try:
        # main.py에서 실행될 때를 대비해 경로 처리
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        secret_path = os.path.join(base_path, "secrets.json")
        
        if os.path.exists(secret_path):
            with open(secret_path, "r", encoding="utf-8") as f:
                secrets = json.load(f)
                token = secrets.get("TELEGRAM_BOT_TOKEN")
                chat_id = secrets.get("TELEGRAM_CHAT_ID")
        
        # GitHub Actions 환경변수 대비
        if not token: token = os.environ.get("TELEGRAM_BOT_TOKEN")
        if not chat_id: chat_id = os.environ.get("TELEGRAM_CHAT_ID")

        if token and chat_id:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = {"chat_id": chat_id, "text": text}
            requests.post(url, data=data)
        else:
            print("⚠️ 텔레그램 토큰이 없어서 메시지를 못 보냈습니다.")
            
    except Exception as e:
        print(f"⚠️ 텔레그램 전송 중 에러: {e}")