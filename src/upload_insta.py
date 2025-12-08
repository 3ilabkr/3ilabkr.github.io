import requests
import json
import os
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
    
    # 환경변수 처리 (GitHub Actions용)
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
# 2. 개별 이미지 업로드 (컨테이너 생성)
# ============================================================================
def upload_single_image(image_url):
    # 페이스북(인스타) 서버에 "이 사진 좀 가져가세요" 하고 URL을 보냄
    url = f"https://graph.facebook.com/v19.0/{PAGE_ID}/media"
    payload = {
        "image_url": image_url,
        "is_carousel_item": "true",
        "access_token": TOKEN
    }
    res = requests.post(url, data=payload)
    try:
        # 성공하면 '컨테이너 ID'라는 영수증을 줍니다.
        return res.json()['id']
    except KeyError:
        print(f"❌ 이미지 업로드 실패: {res.text}")
        return None

# ============================================================================
# 3. 캐러셀(묶음) 게시물 발행
# ============================================================================
def publish_carousel(creation_ids, caption):
    # 1단계: 흩어진 컨테이너 ID들을 하나로 묶기 (CAROUSEL)
    url_step1 = f"https://graph.facebook.com/v19.0/{PAGE_ID}/media"
    payload_step1 = {
        "media_type": "CAROUSEL",
        "children": ",".join(creation_ids), # ID들을 쉼표로 연결
        "caption": caption,
        "access_token": TOKEN
    }
    res1 = requests.post(url_step1, data=payload_step1)
    
    if "id" not in res1.json():
        print(f"❌ 캐러셀 생성 실패: {res1.text}")
        return False
        
    creation_id = res1.json()['id']

    # 2단계: 최종 게시 버튼 누르기 (Publish)
    url_step2 = f"https://graph.facebook.com/v19.0/{PAGE_ID}/media_publish"
    payload_step2 = {
        "creation_id": creation_id,
        "access_token": TOKEN
    }
    res2 = requests.post(url_step2, data=payload_step2)
    
    if "id" in res2.json():
        print(f"🎉 인스타그램 업로드 성공! (Post ID: {res2.json()['id']})")
        return True
    else:
        print(f"❌ 게시 실패: {res2.text}")
        return False

# ============================================================================
# 4. 메인 실행 로직
# ============================================================================
def main(items):
    print("\n🚀 [인스타그램 업로드] 시작...")
    
    if not GITHUB_ID or not PAGE_ID or not TOKEN:
        print("❌ 설정(secrets.json)에 인스타 정보가 없습니다. 건너뜁니다.")
        return

    date_str = items[0]['date']
    
    # ---------------------------------------------------------
    # [중요] 10장 제한에 맞춰 이미지 선정
    # ---------------------------------------------------------
    image_urls = []
    base_url = f"https://{GITHUB_ID}.github.io/images/{date_str}"
    
    # 1. 표지 (00_cover.jpg)
    image_urls.append(f"{base_url}/00_cover.jpg")
    
    # 2. 상품 1위~8위 (01.jpg ~ 08.jpg)
    # (인스타는 최대 10장이라 9, 10위는 부득이하게 제외하거나 구성 변경 필요)
    target_items = items[:8] 
    for item in target_items:
        image_urls.append(f"{base_url}/{item['rank']:02d}.jpg")
        
    # 3. 엔딩 (11_end.jpg)
    image_urls.append(f"{base_url}/11_end.jpg")

    # ---------------------------------------------------------
    # 본문 텍스트(Caption) 만들기
    # ---------------------------------------------------------
    dt_display = f"{date_str[4:6]}월 {date_str[6:8]}일"
    caption = f"🔥 {dt_display} 3ILAB 골드박스 BEST 10 🔥\n\n"
    caption += "오늘 단 하루 특가! 놓치면 손해인 상품들을 모았습니다.\n"
    caption += f"👉 구매 링크는 프로필 상단 링크 클릭!\n"
    caption += f"👉 상품 번호로 검색하면 더 빠르게 찾을 수 있어요.\n\n"
    
    # 본문에는 10개 상품 정보를 다 적어줍니다. (사진은 8개라도 정보는 다 주는 게 좋음)
    for item in items:
        caption += f"[{item['rank']}위] {item['name']}\n"
        caption += f"💰 {item['price']:,}원 (No.{item['id']})\n\n"
        
    caption += ".\n.\n#쿠팡 #골드박스 #특가 #할인 #쇼핑 #살림템 #자취템 #육아템 #3ILAB"

    # ---------------------------------------------------------
    # 업로드 진행
    # ---------------------------------------------------------
    container_ids = []
    print(f"   📸 이미지 {len(image_urls)}장 업로드 준비 중...")
    print(f"      (출처: {base_url})")
    
    for url in image_urls:
        c_id = upload_single_image(url)
        if c_id:
            container_ids.append(c_id)
        else:
            print("❌ 중단: 이미지 컨테이너 생성 실패 (URL 문제일 수 있음)")
            return

    # 최종 발행
    print("   📝 게시물 발행 요청...")
    publish_carousel(container_ids, caption)

if __name__ == "__main__":
    print("이 파일은 main.py를 통해 실행해야 합니다.")