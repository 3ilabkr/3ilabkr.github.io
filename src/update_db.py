import json
import os
from datetime import datetime

# 데이터 저장 경로 (프로젝트 루트의 data 폴더)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "data", "products.json")
# HTML 파일은 루트에 저장 (github pages가 인식하도록)
HTML_FILE = os.path.join(BASE_DIR, "index.html")

def save_to_json(new_items):
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
    
    # 2. 중복 방지 로직 (선생님 기존 방식 유지)
    # 오늘 날짜 데이터가 이미 있다면 삭제 (덮어쓰기 위함)
    today_str = new_items[0]['date']
    all_data = [item for item in all_data if item.get('date') != today_str]
    
    # 3. 새 데이터 추가 (최신 날짜가 위로 오게)
    updated_data = new_items + all_data 
    
    # 4. JSON 파일로 저장
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_data, f, indent=4, ensure_ascii=False)
        
    print(f"✅ 총 {len(updated_data)}개의 상품 데이터가 저장되었습니다.")

    # 5. [NEW] HTML 파일(웹사이트 화면) 자동 업데이트
    update_html_file(updated_data)

def update_html_file(data):
    if not data: return
    
    # 최신 날짜 데이터 추출
    latest_date = data[0]['date']
    today_items = [item for item in data if item['date'] == latest_date]
    
    # 날짜 포맷 (20251209 -> 12월 9일)
    dt = datetime.strptime(latest_date, "%Y%m%d")
    date_display = f"{dt.month}월 {dt.day}일"

    # HTML 내용 작성 (요청하신 디자인 적용)
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>3ILAB 골드박스</title>
        <link href="https://fonts.googleapis.com/css2?family=Nanum+Gothic:wght@400;700;800&display=swap" rel="stylesheet">
        <style>
            :root {{ --primary-color: #E60023; --bg-color: #f8f9fa; }}
            body {{ font-family: 'Nanum Gothic', sans-serif; background-color: var(--bg-color); margin: 0; padding: 0; padding-bottom: 50px; }}
            
            /* 1. 쿠팡 파트너스 문구 (최상단, 흐릿하게) */
            .disclaimer {{
                font-size: 0.7rem; color: #ccc; text-align: center; 
                padding: 10px 0 5px 0; background-color: #fff;
            }}

            /* 2. 코웨이 홍보 배너 (중간 강조) */
            .promo-banner {{
                display: block;
                background-color: #fff; 
                border: 2px solid #03c75a; /* 네이버 그린 */
                border-radius: 12px;
                padding: 15px;
                text-align: center;
                margin: 20px auto;
                max-width: 90%;
                box-shadow: 0 4px 6px rgba(0,0,0,0.05);
                text-decoration: none; color: #333;
                transition: transform 0.2s;
            }}
            .promo-banner:hover {{ transform: translateY(-2px); }}
            .promo-banner b {{ color: #03c75a; }}

            .container {{ max-width: 1000px; margin: 0 auto; padding: 0 15px; }}
            .section-title {{ color: #333; border-left: 5px solid var(--primary-color); padding-left: 10px; margin: 30px 0 15px 0; font-size: 1.3rem; }}

            /* 상품 카드 디자인 */
            .product-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 15px; }}
            .card {{ background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.05); cursor: pointer; transition: transform 0.2s; }}
            .card:hover {{ transform: translateY(-3px); box-shadow: 0 5px 15px rgba(0,0,0,0.15); }}
            
            /* 이미지 비율 고정 (잘림 방지) */
            .card-img-top {{ width: 100%; aspect-ratio: 1 / 1; object-fit: contain; background-color: white; }}
            
            .card-body {{ padding: 12px; }}
            .rank-badge {{ background: var(--primary-color); color: white; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 0.8rem; margin-right: 5px; }}
            .product-title {{ font-size: 0.9rem; margin: 5px 0; height: 2.7em; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }}
            .product-price {{ font-size: 1.1rem; font-weight: 800; color: var(--primary-color); }}
            .product-id {{ font-size: 0.7rem; color: #ccc; text-align: right; margin-top: 5px; }}

            /* 달력 및 검색 */
            .calendar-area {{ background: white; padding: 15px; border-radius: 10px; display: flex; gap: 10px; flex-wrap: wrap; justify-content: center; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 20px; }}
            .date-btn {{ border: 1px solid #ddd; background: white; padding: 8px 15px; border-radius: 20px; cursor: pointer; font-size: 0.9rem; transition: 0.2s; }}
            .date-btn:hover {{ background: #eee; }}
            .date-btn.active {{ background: var(--primary-color); color: white; border-color: var(--primary-color); }}
            .search-box {{ width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 8px; margin-bottom: 20px; box-sizing: border-box; }}
            .loading {{ text-align: center; padding: 50px; color: #999; }}

            @media (max-width: 600px) {{ .product-grid {{ grid-template-columns: repeat(2, 1fr); gap: 10px; }} }}
        </style>
    </head>
    <body>

        <div class="disclaimer">
            이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.
        </div>

        <div class="container">
            <a href="https://naver.me/GWideWE6" target="_blank" class="promo-banner">
                📢 <b>[설문조사]</b> 코웨이 제품 가장 유리한 조건으로<br>상담 받으러 가기 (클릭) 👇
            </a>

            <h2 class="section-title">🔥 {date_display} 골드박스 Top 10</h2>
            
            <div id="today-list" class="product-grid">
                {''.join([f'''
                <div class="card" onclick="window.open('{item['link']}', '_blank')">
                    <img src="{item['image_url']}" class="card-img-top" loading="lazy" 
                         onerror="this.src='https://via.placeholder.com/500x500/eee/999?text=No+Image'">
                    <div class="card-body">
                        <div><span class="rank-badge">{item['rank']}위</span></div>
                        <div class="product-title">{item['name']}</div>
                        <div class="product-price">{item['price']:,}원</div>
                        <div class="product-id">No. {item['id']}</div>
                    </div>
                </div>
                ''' for item in today_items])}
            </div>

            <hr style="margin: 40px 0; border: 0; border-top: 1px solid #ddd;">

            <h2 class="section-title">📅 지난 날짜 & 검색</h2>
            <input type="text" id="search-input" class="search-box" placeholder="상품명이나 번호로 검색" onkeyup="doSearch()">
            <div class="calendar-area" id="calendar-buttons"></div>
            <div id="archive-list" class="product-grid">
                <div style="text-align: center; width: 100%; color: #aaa; padding: 20px;">
                    날짜를 클릭하거나 검색하면 과거 상품이 나옵니다.
                </div>
            </div>
        </div>

        <script>
            // 파이썬이 데이터를 여기에 심어줍니다
            const allProducts = {json.dumps(data, ensure_ascii=False)};

            // 초기화
            function initApp() {{
                const dates = [...new Set(allProducts.map(item => item.date))].sort().reverse();
                
                // 달력 버튼 만들기
                const calContainer = document.getElementById('calendar-buttons');
                dates.forEach(date => {{
                    const btn = document.createElement('button');
                    btn.className = 'date-btn';
                    const label = date.substring(4,6) + "/" + date.substring(6,8);
                    btn.innerText = label;
                    btn.onclick = () => {{
                        document.querySelectorAll('.date-btn').forEach(b => b.classList.remove('active'));
                        btn.classList.add('active');
                        renderArchive(date);
                    }};
                    calContainer.appendChild(btn);
                }});
            }}

            // 과거 데이터 렌더링
            function renderArchive(targetDate) {{
                const container = document.getElementById('archive-list');
                container.innerHTML = "";
                const items = allProducts.filter(item => item.date === targetDate).sort((a, b) => a.rank - b.rank);
                
                items.forEach(item => {{
                    const rankStr = String(item.rank).padStart(2, '0');
                    const imgPath = `images/${{item.date}}/${{rankStr}}.jpg`;
                    const html = `
                    <div class="card" onclick="window.open('${{item.link}}', '_blank')">
                        <img src="${{imgPath}}" class="card-img-top" onerror="this.src='https://via.placeholder.com/500?text=Expired'">
                        <div class="card-body">
                            <div><span class="rank-badge">${{item.date.substring(4)}} / ${{item.rank}}위</span></div>
                            <div class="product-title">${{item.name}}</div>
                            <div class="product-price">${{item.price.toLocaleString()}}원</div>
                        </div>
                    </div>`;
                    container.innerHTML += html;
                }});
            }}

            // 검색 기능
            function doSearch() {{
                const keyword = document.getElementById('search-input').value.toLowerCase();
                const container = document.getElementById('archive-list');
                if (keyword.length < 2) return;
                
                container.innerHTML = "";
                const results = allProducts.filter(item => 
                    item.name.toLowerCase().includes(keyword) || item.id.toLowerCase().includes(keyword)
                );

                if (results.length === 0) {{
                    container.innerHTML = "<div class='loading'>검색 결과가 없습니다.</div>";
                    return;
                }}

                results.forEach(item => {{
                    const imgPath = `images/${{item.date}}/${{String(item.rank).padStart(2,'0')}}.jpg`;
                    const html = `
                    <div class="card" onclick="window.open('${{item.link}}', '_blank')">
                        <img src="${{imgPath}}" class="card-img-top" onerror="this.src='https://via.placeholder.com/500?text=Expired'">
                        <div class="card-body">
                            <div><span class="rank-badge">${{item.date.substring(4)}} / ${{item.rank}}위</span></div>
                            <div class="product-title">${{item.name}}</div>
                            <div class="product-price">${{item.price.toLocaleString()}}원</div>
                        </div>
                    </div>`;
                    container.innerHTML += html;
                }});
            }}

            // 실행
            initApp();
        </script>
    </body>
    </html>
    """
    
    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)
    print("✨ [HTML 업데이트] 디자인이 적용된 index.html 생성 완료!")

if __name__ == "__main__":
    pass
