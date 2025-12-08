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
# [NEW] URL 세탁기 (pageKey 살리고 itemId부터 자르기)
# ============================================================================
def clean_coupang_url(url):
    """
    입력: ...?lptag=...&pageKey=1234&itemId=5678...
    출력: ...?lptag=...&pageKey=1234
    """
    if "&itemId=" in url:
        return url.split("&itemId=")[0]
    return url

# ============================================================================
# [NEW] 딥링크 생성 (선생님 코드 반영)
# ============================================================================
def make_deep_link(origin_url):
    dl_path = "/v2/providers/affiliate_open_api/apis/openapi/v1/deeplink"
    
    # subId 제거, URL만 보냄
    dl_data = {"coupangUrls": [origin_url]}
    
    res = call_api("POST", dl_path, data=dl_data)
    
    if res and res.get('rCode') == '0' and res.get('data'):
        return res['data'][0].get('shortenUrl')
    else:
        # 에러 시 원본 반환
        return origin_url

# 3. 메인 로직
def get_goldbox_items(limit=10):
    print(">> 🚀 골드박스 원본 데이터 수집 중...")
    
    now = datetime.now()
    date_str = now.strftime("%Y%m%d")
    
    # 1. subId 없이 요청
    path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/goldbox"
    params = {"limit": limit} 
    result = call_api("GET", path, params=params)
    
    items = []
    
    if result and result.get('data'):
        print(f">> 📦 {len(result['data'])}개 상품 발견. 링크 정리 및 변환 시작...")
        
        for idx, item in enumerate(result['data']):
            price = item.get('productPrice') or item.get('salePrice') or item.get('price') or item.get('originalPrice', 0)
            
            # (1) 원본 URL
            raw_url = item['productUrl']
            
            # (2) [세탁] itemId 뒤쪽만 자르기 (pageKey는 살림)
            clean_url = clean_coupang_url(raw_url)
            
            # (3) 딥링크 변환
            short_link = make_deep_link(clean_url)
            
            item_id = f"{date_str}-{idx + 1:02d}"

            items.append({
                "id": item_id,
                "date": date_str,
                "rank": idx + 1,
                "name": item['productName'],
                "price": int(price),
                "image_url": item['productImage'],
                "link": short_link
            })

            # [확인] 1위 상품 변환 로그
            if idx == 0:
                print(f"   ✨ [1위 변환 테스트]")
                print(f"      - 원본: {raw_url[:60]}...")
                print(f"      - 정리: {clean_url}")
                print(f"      - 결과: {short_link}")

    print(f">> ✅ 총 {len(items)}개의 상품 처리 완료.")
    return items[:limit]