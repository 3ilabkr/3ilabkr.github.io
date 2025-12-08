import sys
import traceback
from src import fetch_data, make_image, update_db, telegram_bot # 우리가 만든 모듈들

def run_daily_job():
    step = "대기 중"
    
    try:
        # --- 1단계: 데이터 수집 ---
        step = "1. 쿠팡 데이터 수집"
        print(f"\n🚀 [{step}] 시작...")
        
        items = fetch_data.get_goldbox_items(limit=10)
        
        if not items:
            raise Exception("수집된 상품이 0개입니다. API를 확인하세요.")
        
        print(f"✅ {len(items)}개 데이터 확보 완료.")

        # --- 2단계: 이미지 생성 ---
        step = "2. 이미지 생성"
        print(f"\n🎨 [{step}] 시작...")
        
        # make_image 모듈의 메인 로직을 함수화해서 호출하는 게 좋지만,
        # 지금은 간단히 모듈 내 기능을 직접 호출한다고 가정
        # (make_image.py를 수정해서 main() 함수를 밖에서 부를 수 있게 해야 함)
        # 여기서는 make_image.main()을 호출한다고 가정합니다.
        make_image.main(items) 
        
        print("✅ 이미지 생성 완료.")

        # 3. [NEW] 데이터베이스 저장
        step = "3. DB 업데이트"
        print(f"\n💾 [{step}] 시작...")
        update_db.save_to_json(items)
        print("✅ DB 저장 완료.")


        # --- (나중에 추가될) 3단계: 깃허브 업로드 ---
        # step = "3. 깃허브 배포"
        # git_deploy.main()

        # --- (나중에 추가될) 4단계: 인스타 업로드 ---
        # step = "4. 인스타 업로드"
        # upload_insta.main()

        # --- 모든 과정 성공 시 ---
        success_msg = (
            "🎉 [작업 성공]\n"
            "모든 자동화 작업이 완료되었습니다.\n"
            f"- 수집 상품: {len(items)}개\n"
            "- 이미지 생성 완료"
        )
        telegram_bot.send_message(success_msg)
        print("\n✨ 전체 작업 성공!")

    except Exception as e:
        # --- 에러 발생 시 ---
        error_msg = (
            f"🚨 [작업 실패]\n"
            f"에러 발생 단계: {step}\n"
            f"에러 내용: {str(e)}\n\n"
            f"▼ 상세 로그:\n{traceback.format_exc()[:200]}" # 로그 200자만 보냄
        )
        print(f"\n❌ {error_msg}")
        telegram_bot.send_message(error_msg)
        sys.exit(1) # 에러 코드로 종료 (GitHub Actions가 실패를 알 수 있게)

if __name__ == "__main__":
    run_daily_job()