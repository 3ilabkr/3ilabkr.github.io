import requests
import json
import hmac
import hashlib
import os
from time import gmtime, strftime
from datetime import datetime, timedelta # [수정] timedelta 추가
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
# URL 세탁기
# ============================================================================
def clean_coupang_url(url):
    if "&itemId=" in url:
        return url.split("&itemId=")[0]
    return url

# ============================================================================
# 딥링크 생성
# ============================================================================
def make_deep_link(origin_url):
    dl_path = "/v2/providers/affiliate_open_api/apis/openapi/v1/deeplink"
    dl_data = {"coupangUrls": [origin_url]}
    
    res = call_api("POST", dl_path, data=dl_data)
    
    if res and res.get('rCode') == '0' and res.get('data'):
        return res['data'][0].get('shortenUrl')
    else:
        return origin_url

# 3. 메인 로직 (한국 시간 적용됨)
def get_goldbox_items(limit=10):
    
    # [핵심 수정] 서버 시간(UTC)에 9시간을 더해서 한국 시간(KST)을 만듭니다.
    # -----------------------------------------------------------
    utc_now = datetime.utcnow()
    kst_now = utc_now + timedelta(hours=9)
    date_str = kst_now.strftime("%Y%m%d")
    # -----------------------------------------------------------

    print(f">> 🚀 골드박스 데이터 수집 시작 (날짜: {date_str})...")
    
    path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/goldbox"
    params = {"limit": limit} 
    result = call_api("GET", path, params=params)
    
    items = []
    
    if result and result.get('data'):
        print(f">> 📦 {len(result['data'])}개 상품 발견. 변환 시작...")
        
        for idx, item in enumerate(result['data']):
            price = item.get('productPrice') or item.get('salePrice') or item.get('price') or item.get('originalPrice', 0)
            
            # (1) 원본
            raw_url = item['productUrl']
            # (2) 세탁
            clean_url = clean_coupang_url(raw_url)
            # (3) 딥링크
            short_link = make_deep_link(clean_url)
            
            # ID에도 한국 날짜 적용
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

            if idx == 0:
                print(f"   ✨ [1위 확인] {short_link}")

    print(f">> ✅ 총 {len(items)}개의 상품 처리 완료.")
    return items[:limit]
