import os
import datetime
import sys

def push_to_github():
    print("\n🚀 [깃허브 배포] 업로드 프로세스 시작...")
    
    # 1. 깃허브 저장소 연결 확인 (혹시 .git 폴더가 없을까봐)
    if not os.path.exists(".git"):
        print("❌ [오류] 현재 폴더에 .git 설정이 없습니다.")
        print("   터미널에서 'git init'과 'git remote add...' 설정을 먼저 해야 합니다.")
        return False

    try:
        # 2. 변경사항 담기 (git add)
        # 윈도우/맥 호환을 위해 os.system 사용
        print("   - 변경된 파일 스캔 중...")
        os.system("git add .")
        
        # 3. 커밋하기 (git commit)
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        commit_message = f"Auto update: {now}"
        print(f"   - 커밋 메시지 작성: {commit_message}")
        
        # 변경사항이 없으면 commit에서 에러가 날 수 있으니 || true 같은 처리가 좋지만
        # 파이썬에서는 그냥 실행하고 넘어갑니다.
        os.system(f'git commit -m "{commit_message}"')
        
        # 4. 밀어넣기 (git push)
        print("   - 깃허브 서버로 전송 중 (Push)...")
        # 윈도우 CMD에서는 한글 출력이 깨질 수 있어서 영어로 로그 남김
        result = os.system("git push origin main") 
        # 만약 'main' 브랜치가 아니라 'master'라면 "git push origin master"로 수정 필요

        if result == 0:
            print("✅ [성공] 깃허브 배포가 완료되었습니다!")
            return True
        else:
            print("⚠️ [주의] Push 과정에서 무언가 이상합니다. (에러코드 반환됨)")
            return False
        
    except Exception as e:
        print(f"❌ 배포 중 치명적 에러 발생: {e}")
        return False

# 이 파일만 단독으로 실행해서 테스트할 때 사용
if __name__ == "__main__":
    push_to_github()