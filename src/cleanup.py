import os
import shutil
from datetime import datetime, timedelta

def delete_old_folders(days=30):
    print(f"\n🧹 [데이터 정리] {days}일 지난 이미지 삭제 시작...")
    
    # images 폴더 경로
    base_dir = "images"
    if not os.path.exists(base_dir):
        print("   - images 폴더가 없어서 넘어갑니다.")
        return

    # 기준 날짜 계산 (오늘 - 30일)
    cutoff_date = datetime.now() - timedelta(days=days)
    cutoff_str = cutoff_date.strftime("%Y%m%d")
    print(f"   - 삭제 기준일: {cutoff_str} 이전 데이터")

    deleted_count = 0

    # 폴더 하나씩 검사
    for folder_name in os.listdir(base_dir):
        folder_path = os.path.join(base_dir, folder_name)
        
        # 폴더인지 확인
        if not os.path.isdir(folder_path):
            continue

        # 폴더 이름(20251208)이 날짜 형식이 맞는지 확인
        try:
            # 폴더명이 날짜(8자리 숫자)인지 체크
            if len(folder_name) == 8 and folder_name.isdigit():
                # 날짜 비교 (문자열 비교로도 충분함: "20240101" < "20240201")
                if folder_name < cutoff_str:
                    print(f"   🗑️ 삭제 중: {folder_name} (오래된 데이터)")
                    shutil.rmtree(folder_path) # 폴더 통째로 삭제
                    deleted_count += 1
        except Exception as e:
            print(f"   ⚠️ 에러 발생 ({folder_name}): {e}")

    if deleted_count == 0:
        print("   ✨ 삭제할 오래된 폴더가 없습니다.")
    else:
        print(f"   ✅ 총 {deleted_count}개의 오래된 폴더를 삭제했습니다.")

# 테스트용
if __name__ == "__main__":
    # 테스트 할 때는 0일(오늘 이전 전부)로 설정해서 잘 지워지나 확인 가능
    delete_old_folders(days=30)
