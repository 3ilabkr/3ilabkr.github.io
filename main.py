import sys
import time
import traceback
import os
import json
from datetime import datetime, timedelta

# 모듈 불러오기
from src import fetch_data, make_image, update_db, telegram_bot, git_deploy, upload_insta

# ============================================================================
# [NEW] 토큰 수명 체크 함수
# ============================================================================
def check_token_life():
    try:
        # secrets.json 읽기
        secret_path = "secrets.json"
        if not os.path.exists(secret_path): return

        with open(secret_path, "r", encoding="utf-8") as f:
            secrets = json.load(f)
            
        update_date_str = secrets.get("TOKEN_UPDATE_DATE")
        if not update_date_str:
            print("⚠️ 토큰 발급 날짜(TOKEN_UPDATE_DATE)가 설정되지 않았습니다.")
            return

        # 날짜 계산
        update_date = datetime.strptime(update_date_str, "%Y-%m-%d")
        today = datetime.now()
        elapsed_days = (today - update_date).days
        remaining_days = 60 - elapsed_days

        print(f"\n🔑 [토큰 상태] 발급 후 {elapsed_days}일 경과 (남은 수명: {remaining_days}일)")

        # [알림 조건] 만료 7일 전부터, 혹은 이미 만료되었을 때 알림 발송
        if remaining_days <= 7:
            msg = (
                f"🚨 [토큰 갱신 경보]\n"
                f"인스타그램 토큰 만료까지 {remaining_days}일 남았습니다.\n"
                f"봇이 멈추기 전에 토큰을 갱신하고 secrets.json을 수정해주세요!"
            )
            telegram_bot.send_message(msg)
            print("🚨 텔레그램으로 갱신 경고를 보냈습니다.")
            
    except Exception as e:
        print(f"⚠️ 토큰 날짜 체크 중 오류: {e}")

# ============================================================================
# 메인 실행 로직
# ============================================================================
def run_daily_job():
    step = "대기 중"
    
    try:
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
        
        # [대기] 웹 반영 시간 (2분)
        wait_sec = 5 
        print(f"⏳ 웹 반영 대기 중 ({wait_sec}초)...")
        time.sleep(wait_sec) 

        # 5. 인스타 업로드
        step = "5. 인스타 업로드"
        print(f"\n📸 [{step}] 시작...")
        upload_insta.main(items)

        # 6. [NEW] 토큰 수명 체크 및 성공 알림
        check_token_life()

        success_msg = f"🎉 [작업 성공] 인스타 업로드 완료! (오늘 할 일 끝)"
        # 매일 성공 알림을 받고 싶으면 아래 주석 해제
        # telegram_bot.send_message(success_msg)
        print("\n✨ 전체 작업 성공!")

    except Exception as e:
        # 에러 발생 시 즉시 텔레그램 전송
        error_msg = f"🚨 [작업 실패]\n단계: {step}\n내용: {str(e)}\n\n{traceback.format_exc()[:200]}"
        print(f"\n❌ {error_msg}")
        telegram_bot.send_message(error_msg)
        sys.exit(1)

if __name__ == "__main__":
    run_daily_job()