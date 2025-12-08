import requests
import json
import os

# 1. 설정 및 키 로드
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

# 2. 개별 이미지 업로드
def upload_single_image(image_url):
    url = f"https://graph.facebook.com/v19.0/{PAGE_ID}/media"
    payload = {
        "image_url": image_url,
        "is_carousel_item": "true",
        "access_token": TOKEN
    }
    res = requests.post(url, data=payload)
    
    if res.status_code != 200 or "id" not in res.json():
        error_msg = res.json().get('error', {}).get('message', '알 수 없는 오류')
        # 여기서 에러 내용을 자세히 출력
        print(f"❌ [이미지 업로드 실패] {error_msg}")
        return None
        
    return res.json()['id']

# 3. 캐러셀 게시
def publish_carousel(creation_ids, caption):
    # 컨테이너 묶기
    url_step1 = f"https://graph.facebook.com/v19.0/{PAGE_ID}/media"
    payload_step1 = {
        "media_type": "CAROUSEL",
        "children": ",".join(creation_ids),
        "caption": caption,
        "access_token": TOKEN
    }
    res1 = requests.post(url_step1, data=payload_step1)
    
    if "id" not in res1.json():
        print(f"❌ [캐러셀 생성 실패] {res1.text}")
        return False
        
    creation_id = res1.json()['id']

    # 최종 게시
    url_step2 = f"https://graph.facebook.com/v19.0/{PAGE_ID}/media_publish"
    payload_step2 = {
        "creation_id": creation_id,
        "access_token": TOKEN
    }
    res2 = requests.post(url_step2, data=payload_step2)
    
    if "id" in res2.json():
        print(f"🎉 인스타그램 업로드 성공! (ID: {res2.json()['id']})")
        return True
    else:
        print(f"❌ [최종 게시 실패] {res2.text}")
        return False

# 4. 메인 실행
def main(items):
    print("\n🚀 [인스타그램 업로드] 시작...")
    
    if not GITHUB_ID or not PAGE_ID or not TOKEN:
        raise Exception("secrets.json에 인스타 정보가 없습니다.")

    date_str = items[0]['date']
    
    # 이미지 URL 준비
    image_urls = []
    base_url = f"https://{GITHUB_ID}.github.io/images/{date_str}"
    
    image_urls.append(f"{base_url}/00_cover.jpg") # 표지
    for item in items[:8]: # 상품 8개
        image_urls.append(f"{base_url}/{item['rank']:02d}.jpg")
    image_urls.append(f"{base_url}/11_end.jpg") # 엔딩

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
    print(f"   📸 이미지 {len(image_urls)}장 업로드 시도...")
    
    for url in image_urls:
        c_id = upload_single_image(url)
        if c_id:
            container_ids.append(c_id)
        else:
            raise Exception("이미지 컨테이너 생성 중단 (권한/URL 문제)")

    print("   📝 게시물 발행 요청...")
    publish_carousel(container_ids, caption)

if __name__ == "__main__":
    pass