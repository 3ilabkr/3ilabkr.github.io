import sys
import time
import traceback
import os
import json
import requests  # [추가] 웹 확인용
from datetime import datetime, timedelta

# 모듈 불러오기
from src import fetch_data, make_image, update_db, telegram_bot, git_deploy, upload_insta, cleanup

# ============================================================================
# [NEW] 웹 이미지 반영 확인 함수 (스마트 대기)
# ============================================================================
def wait_for_image_server(github_id, date_str, max_retries=20):
    """
    깃허브 페이지에 이미지가 실제로 떴는지 30초마다 확인합니다.
    최대 10분(30초 * 20회)까지 기다립니다.
    """
    # 확인해볼 샘플 이미지 (표지)
    target_url = f"https://{github_id}.github.io/images/{date_str}/00_cover.jpg"
    print(f"\n📡 [웹 반영 확인] 이미지 서버 응답 대기 중...")
    print(f"   - 타겟 URL: {target_url}")

    for i in range(max_retries):
        try:
            # 헤더만 살짝 찔러보기 (용량 아끼기 위해 head 요청)
            response = requests.head(target_url)
            
            # 200 OK가 뜨면 이미지가 웹에 반영된 것임
            if response.status_code == 200:
                print(f"   ✅ [성공] 이미지가 웹에 노출되었습니다! (시도 {i+1}/{max_retries})")
                return True
            else:
                print(f"   ⏳ [대기] 아직 반영 안 됨 (응답코드: {response.status_code})... 30초 뒤 재시도 ({i+1}/{max_retries})")
        except Exception as e:
            print(f"   ⚠️ 체크 중 에러: {e}")
        
        # 30초 휴식
        time.sleep(30)
    
    print("❌ [실패] 10분이 지나도 이미지가 뜨지 않습니다.")
    return False

# ============================================================================
# 토큰 수명 체크 함수
# ============================================================================
def check_token_life():
    try:
        secret_path = "secrets.json"
        if not os.path.exists(secret_path): return

        with open(secret_path, "r", encoding="utf-8") as f:
            secrets = json.load(f)
            
        update_date_str = secrets.get("TOKEN_UPDATE_DATE")
        if not update_date_str: return

        update_date = datetime.strptime(update_date_str, "%Y-%m-%d")
        today = datetime.now()
        elapsed_days = (today - update_date).days
        remaining_days = 60 - elapsed_days

        print(f"\n🔑 [토큰 상태] 발급 후 {elapsed_days}일 경과 (남은 수명: {remaining_days}일)")

        if remaining_days <= 7:
            msg = f"🚨 [토큰 갱신 경보] 인스타 토큰 만료 {remaining_days}일 전입니다!"
            telegram_bot.send_message(msg)
            
    except Exception as e:
        print(f"⚠️ 토큰 날짜 체크 중 오류: {e}")

# ============================================================================
# 메인 실행 로직
# ============================================================================
def run_daily_job():
    step = "대기 중"
    
    try:
        # secrets.json에서 ID 미리 읽기 (URL 체크용)
        github_id = None
        if os.path.exists("secrets.json"):
            with open("secrets.json", "r", encoding="utf-8") as f:
                github_id = json.load(f).get("GH_ID") # 이름 바꾼 GH_ID 사용
        if not github_id: github_id = os.environ.get("GH_ID") # 액션 환경변수
        
        # 1. 데이터 수집
        step = "1. 데이터 수집"
        print(f"\n🚀 [{step}] 시작...")
        items = fetch_data.get_goldbox_items(limit=10)
        if not items: raise Exception("수집된 상품이 0개입니다.")
        print(f"✅ {len(items)}개 데이터 확보 완료")

        # 2. 이미지 생성
        step = "2. 이미지 생성"
        print(f"\n🎨 [{step}] 시작...")
        make_image.main(items)
        print("✅ 이미지 생성 완료")

        # 3. DB 업데이트
        step = "3. DB 업데이트"
        print(f"\n💾 [{step}] 시작...")
        update_db.save_to_json(items)
        print("✅ DB 저장 완료")

        # 4. 깃허브 배포
        step = "4. 깃허브 배포"
        print(f"\n☁️ [{step}] 시작...")
        git_deploy.push_to_github()
        
        # ------------------------------------------------------------------
        # [수정됨] 무작정 기다리는 대신, 실제로 떴는지 확인하는 '스마트 대기' 적용
        # ------------------------------------------------------------------
        if github_id:
            is_ready = wait_for_image_server(github_id, items[0]['date'])
            if not is_ready:
                raise Exception("이미지가 깃허브 페이지에 반영되지 않았습니다. (시간 초과)")
        else:
            print("⚠️ GITHUB_ID를 찾을 수 없어 2분 강제 대기합니다.")
            time.sleep(120)

        # 5. 인스타 업로드
        step = "5. 인스타 업로드"
        print(f"\n📸 [{step}] 시작...")
        upload_insta.main(items)

        # 6. 데이터 청소
        step = "6. 데이터 청소"
        cleanup.delete_old_folders(days=30)

        # 7. 토큰/결과 알림
        check_token_life()
        success_msg = f"🎉 [작업 성공] 3ILAB 골드박스 업로드 완료!\n- {len(items)}개 상품 처리됨"
        telegram_bot.send_message(success_msg) 
        
        print("\n✨ 전체 작업 성공!")

    except Exception as e:
        error_msg = f"🚨 [작업 실패]\n단계: {step}\n내용: {str(e)}\n\n{traceback.format_exc()[:200]}"
        print(f"\n❌ {error_msg}")
        telegram_bot.send_message(error_msg)
        sys.exit(1)

if __name__ == "__main__":
    run_daily_job()
