import json
import os
from datetime import datetime

# 데이터 저장 경로 (프로젝트 루트의 data 폴더)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "data", "products.json")

def save_to_json(new_items):
    """
    기존 products.json 파일을 읽어서, 새로운 아이템을 추가하고 저장합니다.
    중복된 날짜의 데이터가 있다면 덮어쓰거나 무시하는 로직을 추가할 수 있습니다.
    여기서는 단순 추가(append) 방식을 사용합니다.
    """
    if not new_items:
        print("❌ 저장할 데이터가 없습니다.")
        return

    print(f"\n💾 데이터베이스 저장 시작 ({DATA_FILE})...")

    # 1. 기존 데이터 불러오기
    all_data = []
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                all_data = json.load(f)
        except json.JSONDecodeError:
            print("⚠️ 기존 파일이 깨져있어 새로 만듭니다.")
            all_data = []
    
    # 2. 중복 방지 로직 (오늘 날짜 데이터가 이미 있으면 삭제하고 새로 넣기)
    # (같은 날짜에 여러 번 실행했을 때 데이터가 계속 쌓이는 걸 방지)
    today_str = new_items[0]['date']
    all_data = [item for item in all_data if item.get('date') != today_str]
    
    # 3. 새 데이터 추가
    # 최신 날짜가 위로 오게 하려면: new_items + all_data
    # 과거 날짜가 위로 오게 하려면: all_data + new_items
    updated_data = new_items + all_data 
    
    # 4. 파일로 저장
    # data 폴더가 없으면 생성
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_data, f, indent=2, ensure_ascii=False)
        
    print(f"✅ 총 {len(updated_data)}개의 상품 데이터가 저장되었습니다.")

# 테스트용
if __name__ == "__main__":
    dummy_data = [{"id": "TEST-01", "date": "20990101", "name": "테스트"}]
    save_to_json(dummy_data)