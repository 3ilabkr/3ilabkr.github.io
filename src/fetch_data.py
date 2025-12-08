import requests
import json
import hmac
import hashlib
import os
from time import gmtime, strftime
from datetime import datetime
import urllib.parse

# 1. API KEY 로드
def load_api_keys():
    access_key = None
    secret_key = None
    secret_file_path = "secrets.json"
    if os.path.exists(secret_file_path):
        try:
            with open(secret_file_path, "r", encoding="utf-8") as f:
                secrets = json.load(f)
                access_key = secrets.get("COUPANG_ACCESS_KEY")
                secret_key = secrets.get("COUPANG_SECRET_KEY")
        except Exception: pass

    if not access_key: access_key = os.environ.get("COUPANG_ACCESS_KEY")
    if not secret_key: secret_key = os.environ.get("COUPANG_SECRET_KEY")

    if not access_key or not secret_key:
        raise ValueError("❌ API Key가 없습니다!")
    return access_key, secret_key

ACCESS_KEY, SECRET_KEY = load_api_keys()

# 2. 인증 헤더 생성
def generate_hmac(method, url, secret_key, access_key):
    path, *query = url.split("?")
    datetime_gmt = strftime('%y%m%d', gmtime()) + 'T' + strftime('%H%M%S', gmtime()) + 'Z'
    message = datetime_gmt + method + path + (query[0] if query else "")
    signature = hmac.new(bytes(secret_key, "utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()
    return "CEA algorithm=HmacSHA256, access-key={}, signed-date={}, signature={}".format(access_key, datetime_gmt, signature)

def call_api(method, path, params=None, data=None):
    DOMAIN = "https://api-gateway.coupang.com"
    if params:
        query = urllib.parse.urlencode(params)
        path_with_query = f"{path}?{query}"
    else:
        path_with_query = path
    full_url = f"{DOMAIN}{path_with_query}"

    authorization = generate_hmac(method, path_with_query, SECRET_KEY, ACCESS_KEY)
    headers = {"Authorization": authorization, "Content-Type": "application/json;charset=UTF-8"}

    try:
        if method == "GET": response = requests.get(full_url, headers=headers)
        elif method == "POST": response = requests.post(full_url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ API 호출 에러 ({path}): {e}")
        return None

# ============================================================================
# [NEW] 딥링크 개별 생성 (단축 URL 만들기)
# ============================================================================
def make_deep_link(origin_url):
    dl_path = "/v2/providers/affiliate_open_api/apis/openapi/v1/deeplink"
    dl_data = {
        "coupangUrls": [origin_url],
        "subId": "auto_video_bot"
    }
    
    res = call_api("POST", dl_path, data=dl_data)
    
    if res and res.get('rCode') == '0' and res.get('data'):
        # shortenUrl(단축)이 있으면 그걸 쓰고, 없으면 landingUrl 사용
        return res['data'][0].get('shortenUrl') or res['data'][0].get('landingUrl')
    else:
        return None

# 3. 메인 로직
def get_goldbox_items(limit=10):
    print(">> 🚀 골드박스 원본 데이터 수집 중...")
    
    now = datetime.now()
    date_str = now.strftime("%Y%m%d")
    
    # [변경] subId를 뺍니다! (그래야 원본 링크가 옴)
    path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/goldbox"
    params = {"limit": limit} 
    result = call_api("GET", path, params=params)
    
    items = []
    
    if result and result.get('data'):
        print(f">> 📦 {len(result['data'])}개 상품 발견. 딥링크 변환 시작...")
        
        for idx, item in enumerate(result['data']):
            price = item.get('productPrice') or item.get('salePrice') or item.get('price') or item.get('originalPrice', 0)
            
            # 1. 원본 링크 가져오기
            origin_url = item['productUrl']
            
            # [요청하신 기능] 원본 링크 출력해서 눈으로 확인
            if idx < 3: # 너무 많으니 상위 3개만 출력
                print(f"   [원본-{idx+1}] {origin_url[:60]}...")

            # 2. 딥링크 변환 (짧은 주소 받기)
            short_link = make_deep_link(origin_url)
            
            if not short_link:
                print(f"   ⚠️ 변환 실패: {item['productName'][:10]}... (원본 사용)")
                short_link = origin_url
            
            item_id = f"{date_str}-{idx + 1:02d}"

            items.append({
                "id": item_id,
                "date": date_str,
                "rank": idx + 1,
                "name": item['productName'],
                "price": int(price),
                "image_url": item['productImage'],
                "link": short_link  # 여기에 짧은 링크가 들어갑니다
            })

            if idx == 0:
                print(f"   💰 [단축 확인] {short_link}")

    print(f">> ✅ 총 {len(items)}개의 상품 처리 완료.")
    return items[:limit]