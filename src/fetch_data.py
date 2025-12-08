import requests
import json
import hmac
import hashlib
import time
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
        print(f"❌ API 호출 에러: {e}")
        return None

# 3. 데이터 수집 (최적화됨)
def get_goldbox_items(limit=10):
    print(">> 🚀 골드박스 데이터 수집 시작 (자동 수익링크 확보)...")
    
    now = datetime.now()
    date_str = now.strftime("%Y%m%d")
    
    # subId를 넣으면 응답에 이미 '단축 링크'가 들어있습니다.
    path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/goldbox"
    params = {"limit": limit, "subId": "auto_video_bot"}
    result = call_api("GET", path, params=params)
    
    items = []
    
    if result and result.get('data'):
        for idx, item in enumerate(result['data']):
            price = item.get('productPrice') or item.get('salePrice') or item.get('price') or item.get('originalPrice', 0)
            
            # [수정] 별도 변환 없이 바로 사용 (이미 수익 링크임)
            final_link = item['productUrl']
            
            item_id = f"{date_str}-{idx + 1:02d}"

            items.append({
                "id": item_id,
                "date": date_str,
                "rank": idx + 1,
                "name": item['productName'],
                "price": int(price),
                "image_url": item['productImage'],
                "link": final_link 
            })

            # 1위 링크만 샘플로 출력해서 확인
            if idx == 0:
                print(f"💰 [링크 확인] {final_link[:50]}...")

    print(f">> ✅ 총 {len(items)}개의 상품 정보를 처리했습니다.")
    return items[:limit]