import os
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

# 설정값
FONT_PATH = "fonts/GmarketSansBold.ttf" 
CANVAS_SIZE = (1080, 1080)
BG_COLOR = "white"
ACCENT_COLOR = "#E60023"

def draw_text_wrapper(draw, text, font, max_width, start_pos, color="black"):
    lines = []
    words = text.split()
    current_line = words[0]
    for word in words[1:]:
        bbox = draw.textbbox((0, 0), current_line + " " + word, font=font)
        if bbox[2] > max_width: 
            lines.append(current_line)
            current_line = word
        else:
            current_line += " " + word
    lines.append(current_line)

    x, y = start_pos
    for line in lines:
        draw.text((x, y), line, font=font, fill=color)
        y += font.size + 10 
    return y

def load_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except OSError:
        return ImageFont.load_default()

def create_cover(date_str, save_path):
    img = Image.new("RGB", CANVAS_SIZE, BG_COLOR)
    draw = ImageDraw.Draw(img)
    font_lg = load_font(100)
    font_md = load_font(60)

    dt = datetime.strptime(date_str, "%Y%m%d")
    date_text = f"{dt.month}월 {dt.day}일"
    
    draw.text((100, 300), "오늘 단 하루!", font=font_md, fill="black")
    draw.text((100, 400), "쿠팡 골드박스", font=font_lg, fill="black")
    draw.text((100, 520), f"{date_text} 베스트 8", font=font_lg, fill=ACCENT_COLOR)
    draw.text((100, 700), "▶ 옆으로 넘겨서 확인하세요", font=font_md, fill="gray") # 이모지 깨짐 방지
    
    img.save(save_path)
    return os.path.getsize(save_path)

def create_product_card(item, save_path):
    img = Image.new("RGB", CANVAS_SIZE, BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    font_rank = load_font(120)
    font_name = load_font(50)
    font_price = load_font(70)
    font_id = load_font(30) 

    # 1. 이미지 (위치 Y=50)
    try:
        res = requests.get(item['image_url'], timeout=10)
        p_img = Image.open(BytesIO(res.content))
        p_img = p_img.resize((800, 800)) 
        img.paste(p_img, (140, 50)) 
    except Exception as e:
        print(f"   ⚠️ 이미지 실패: {e}")
        return 0

    # 2. 순위
    draw.text((50, 40), str(item['rank']), font=font_rank, fill=ACCENT_COLOR)
    
    # 3. 상품명 (Y=860)
    text_y = 860
    text_y = draw_text_wrapper(draw, item['name'], font_name, 900, (90, text_y))
    
    # 4. 가격
    price_txt = f"{item['price']:,}원" 
    draw.text((90, text_y + 15), price_txt, font=font_price, fill=ACCENT_COLOR)

    # 5. 일련번호
    id_text = f"No. {item['id']}"
    bbox = draw.textbbox((0, 0), id_text, font=font_id)
    text_width = bbox[2] - bbox[0]
    draw.text((1080 - text_width - 50, 1020), id_text, font=font_id, fill="gray")

    img.save(save_path)
    print(f"   📸 상품{item['rank']} 완료")
    return os.path.getsize(save_path)

def create_end_card(save_path):
    img = Image.new("RGB", CANVAS_SIZE, BG_COLOR)
    draw = ImageDraw.Draw(img)
    font_lg = load_font(80)
    font_md = load_font(50)

    draw.text((100, 400), "구매 링크는", font=font_lg, fill="black")
    draw.text((100, 500), "프로필 상단 클릭!", font=font_lg, fill=ACCENT_COLOR)
    draw.text((100, 650), "매일 아침 8시 업데이트", font=font_md, fill="gray")
    
    img.save(save_path)
    return os.path.getsize(save_path)

# [핵심] 이 함수가 꼭 있어야 합니다!
def main(items):
    if not items: return

    date_str = items[0]['date']
    save_dir = f"images/{date_str}"
    if not os.path.exists(save_dir): os.makedirs(save_dir)
    
    print(f"\n📂 저장 폴더: {save_dir}")
    total_size = 0
    count = 0

    total_size += create_cover(date_str, f"{save_dir}/00_cover.jpg")
    count += 1

    for item in items:
        filename = f"{item['rank']:02d}.jpg" 
        save_path = f"{save_dir}/{filename}"
        s = create_product_card(item, save_path)
        if s > 0:
            total_size += s
            count += 1

    total_size += create_end_card(f"{save_dir}/11_end.jpg")
    count += 1
    
    mb_size = total_size / (1024 * 1024)
    print(f"📊 [이미지 생성 완료] 총 {count}장 ({mb_size:.2f} MB)")

if __name__ == "__main__":
    pass
