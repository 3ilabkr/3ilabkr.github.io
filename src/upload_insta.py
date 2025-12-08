import requests
import json
import os
import sys
import time

# ============================================================================
# 1. 설정 및 키 로드
# ============================================================================
def load_secrets():
    secrets = {}
    path = "secrets.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            secrets = json.load(f)
    
    return {
        "GITHUB_ID": secrets.get("GITHUB_ID") or os.environ.get("GITHUB_ID"),
        "PAGE_ID": secrets.get("INSTA_PAGE_ID") or os.environ.get("INSTA_PAGE_ID"),
        "TOKEN": secrets.get("INSTA_ACCESS_TOKEN") or os.environ.get("INSTA_ACCESS_TOKEN")
    }

KEYS = load_secrets()
GITHUB_ID = KEYS["GITHUB_ID"]
PAGE_ID = KEYS["PAGE_ID"]
TOKEN = KEYS["TOKEN"]

# ============================================================================
# [NEW] 토큰 및 권한 사전 점검
# ============================================================================
def check_token_status():
    print("   🕵️ [진단] 토큰 및 권한 상태 확인 중...")
    url = f"https://graph.facebook.com/v19.0/me/accounts?access_token={TOKEN}"
    res = requests.get(url)
    
    if res.status_code == 200:
        data = res.json()
        print("   ✅ [진단] 토큰 유효함. 연결된 페이지 목록:")
        if 'data' in data:
            for page in data['data']:
                print(f"      - 페이지 이름: {page.get('name')} (ID: {page.get('id')})")
                if page.get('id') == PAGE_ID:
                    print("      ✨ (현재 설정된 PAGE_ID와 일치합니다! OK)")
    else:
        print(f"   ❌ [진단] 토큰 문제 발생!")
        print(f"      응답 코드: {res.status_code}")
        print(f"      에러 내용: {res.text}")
        raise Exception("토큰이 유효하지 않거나 권한이 없습니다.")

# ============================================================================
# 2. 개별 이미지 업로드 (컨테이너 생성)
# ============================================================================
def upload_single_image(image_url, index):
    print(f"   📤 [업로드 {index+1}] 이미지 전송 중...")
    
    url = f"https://graph.facebook.com/v19.0/{PAGE_ID}/media"
    payload = {
        "image_url": image_url,
        "is_carousel_item": "true",
        "access_token": TOKEN
    }
    res = requests.post(url, data=payload)
    
    # [디버그] 실패 시 상세 정보 출력
    if res.status_code != 200 or "id" not in res.json():
        print(f"\n❌ [ERROR] {index+1}번째 이미지 업로드 실패!")
        print(f"   - URL: {image_url}")
        print(f"   - 응답 코드: {res.status_code}")
        print(f"   - 상세 에러(RAW): {res.text}") # 페이스북이 보낸 진짜 에러 메시지
        raise Exception(f"{index+1}번 이미지 업로드 중단")
        
    container_id = res.json()['id']
    print(f"      ✅ 성공 (Container ID: {container_id})")
    return container_id

# ============================================================================
# 3. 캐러셀 게시
# ============================================================================
def publish_carousel(creation_ids, caption):
    print("\n   📦 [패키징] 캐러셀 컨테이너 묶는 중...")
    
    # 1. 컨테이너 묶기
    url_step1 = f"https://graph.facebook.com/v19.0/{PAGE_ID}/media"
    payload_step1 = {
        "media_type": "CAROUSEL",
        "children": ",".join(creation_ids),
        "caption": caption,
        "access_token": TOKEN
    }
    res1 = requests.post(url_step1, data=payload_step1)
    
    if "id" not in res1.json():
        print(f"\n❌ [ERROR] 캐러셀 생성(묶기) 실패!")
        print(f"   - 응답 코드: {res1.status_code}")
        print(f"   - 상세 에러(RAW): {res1.text}")
        raise Exception("캐러셀 생성 실패")
        
    creation_id = res1.json()['id']
    print(f"      ✅ 성공 (Creation ID: {creation_id})")

    # 2. 최종 게시
    print("   🚀 [발행] 최종 게시 요청 중...")
    url_step2 = f"https://graph.facebook.com/v19.0/{PAGE_ID}/media_publish"
    payload_step2 = {
        "creation_id": creation_id,
        "access_token": TOKEN
    }
    res2 = requests.post(url_step2, data=payload_step2)
    
    if "id" in res2.json():
        print(f"\n🎉 [성공] 인스타그램 업로드 완료! (Post ID: {res2.json()['id']})")
        return True
    else:
        print(f"\n❌ [ERROR] 최종 발행 실패!")
        print(f"   - 응답 코드: {res2.status_code}")
        print(f"   - 상세 에러(RAW): {res2.text}")
        raise Exception("최종 게시 실패")

# ============================================================================
# 4. 메인 실행
# ============================================================================
def main(items):
    print("\n🚀 [인스타그램 업로드 (디버그 모드)] 시작...")
    
    if not GITHUB_ID or not PAGE_ID or not TOKEN:
        print("❌ secrets.json 정보가 누락되었습니다.")
        return

    # 1. 토큰 상태 먼저 체크
    check_token_status()

    date_str = items[0]['date']
    
    # 이미지 URL 준비 (총 10장)
    image_urls = []
    base_url = f"https://{GITHUB_ID}.github.io/images/{date_str}"
    
    image_urls.append(f"{base_url}/00_cover.jpg") # 1
    for item in items[:8]: # 2~9
        image_urls.append(f"{base_url}/{item['rank']:02d}.jpg")
    image_urls.append(f"{base_url}/11_end.jpg") # 10

    print(f"\n📸 업로드할 이미지 수: {len(image_urls)}장")
    print(f"   (표지 + 상품 8개 + 엔딩)")

    # 본문 작성
    dt_display = f"{date_str[4:6]}월 {date_str[6:8]}일"
    caption = f"🔥 {dt_display} 3ILAB 골드박스 BEST 10 🔥\n\n"
    caption += "오늘 단 하루 특가! 놓치면 손해인 상품들을 모았습니다.\n"
    caption += f"👉 구매 링크는 프로필 상단 링크 클릭!\n"
    caption += f"👉 상품 번호로 검색하면 더 빠르게 찾을 수 있어요.\n\n"
    
    for item in items:
        caption += f"[{item['rank']}위] {item['name']}\n"
        caption += f"💰 {item['price']:,}원 (No.{item['id']})\n\n"
        
    caption += ".\n.\n#쿠팡 #골드박스 #특가 #할인 #쇼핑 #살림템 #자취템 #육아템 #3ILAB"

    # 업로드 실행
    container_ids = []
    
    try:
        for i, url in enumerate(image_urls):
            c_id = upload_single_image(url, i)
            container_ids.append(c_id)
            # 너무 빨리 요청하면 차단될 수 있으니 1초 쉼
            time.sleep(1)

        # 모두 성공하면 게시
        publish_carousel(container_ids, caption)
        
    except Exception as e:
        print(f"\n🚨 [CRITICAL ERROR] 업로드 프로세스 중단됨: {e}")
        # 메인 프로그램이 알 수 있게 다시 에러 던짐
        raise e

if __name__ == "__main__":
    pass