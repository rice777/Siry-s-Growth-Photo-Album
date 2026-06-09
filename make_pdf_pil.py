#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
粉粉成长相册 - PDF打印版生成器
每页A4布局，照片+日期+文案
使用PIL直接生成PDF，无需额外依赖
"""

import json
import os
from PIL import Image, ImageDraw, ImageFont

# ==================== 配置 ====================
DATA_JSON = r"E:\lenovo\GrowthAlbum@Github\Siry-s-Growth-Photo-Album\data.json"
PHOTOS_BASE = r"E:\lenovo\GrowthAlbum@Github\Siry-s-Growth-Photo-Album\photos"
OUTPUT_DIR = r"E:\lenovo\粉粉成长记录"
OUTPUT_PDF = os.path.join(OUTPUT_DIR, "粉粉的成长时光_打印版.pdf")

# A4 尺寸 200 DPI
A4_W, A4_H = 2000, 2828
MARGIN = 80

def get_font(size):
    for fp in [
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\simsun.ttc",
    ]:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except:
                pass
    return ImageFont.load_default()

def wrap_text(draw, text, font, max_width):
    lines = []
    current_line = ""
    for ch in text:
        test_line = current_line + ch
        bw = draw.textbbox((0, 0), test_line, font=font)
        if bw[2] - bw[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = ch
    if current_line:
        lines.append(current_line)
    return lines

# ==================== 加载数据 ====================
print("📖 加载相册数据...", flush=True)
with open(DATA_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)

all_photos = []
for age, photos in data.items():
    for p in photos:
        if p.get('file') and p.get('date'):
            all_photos.append({
                'file': p['file'],
                'date': p['date'],
                'caption': p.get('caption', ''),
                'age': age,
                'photo_path': os.path.join(PHOTOS_BASE, age, p['file'])
            })

all_photos = sorted(all_photos, key=lambda x: x['date'])
print(f"📸 共 {len(all_photos)} 张照片", flush=True)

# ==================== 字体 ====================
font_date = get_font(42)
font_caption = get_font(34)
font_age = get_font(28)
font_cover_title = get_font(80)
font_cover_sub = get_font(48)

# ==================== 生成每页JPEG ====================
print("🎨 生成页面...", flush=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
page_jpgs = []

for i, photo in enumerate(all_photos):
    if (i+1) % 50 == 0:
        print(f"  处理 {i+1}/{len(all_photos)}", flush=True)

    page = Image.new('RGB', (A4_W, A4_H), '#FFF5F8')
    draw = ImageDraw.Draw(page)

    # 顶部装饰线
    draw.line([(MARGIN, 25*20//10), (A4_W - MARGIN, 25*20//10)], fill='#FFB6C1', width=4)

    # 年龄段标签
    age_bbox = draw.textbbox((0, 0), photo['age'], font=font_age)
    age_w = age_bbox[2] - age_bbox[0]
    age_h = age_bbox[3] - age_bbox[1]
    draw.rounded_rectangle(
        [MARGIN + 10, 10*20//10, MARGIN + 10 + age_w + 20, 10*20//10 + age_h + 10],
        radius=15, fill='#FF69B4'
    )
    draw.text((MARGIN + 20, 15*20//10), photo['age'], fill='#FFFFFF', font=font_age)

    # 照片区域
    max_photo_w = A4_W - 2 * MARGIN
    max_photo_h = 1200

    if os.path.exists(photo['photo_path']):
        try:
            photo_img = Image.open(photo['photo_path']).convert('RGB')
            pw, ph = photo_img.size
            scale = min(max_photo_w / pw, max_photo_h / ph, 1.0)
            nw, nh = int(pw * scale), int(ph * scale)
            resized = photo_img.resize((nw, nh), Image.Resampling.LANCZOS)
            bg = Image.new('RGB', (max_photo_w, max_photo_h), '#FFFFFF')
            bg.paste(resized, ((max_photo_w - nw) // 2, (max_photo_h - nh) // 2))
            page.paste(bg, (MARGIN, 35*20//10))
            photo_img.close()
        except:
            pass

    # 日期
    dt_text = f"📅 {photo['date']}"
    dt_bbox = draw.textbbox((0, 0), dt_text, font=font_date)
    draw.text((MARGIN, max_photo_h + 35*20//10 + 25), dt_text, fill='#FF8C69', font=font_date)

    # 文案
    caption = photo['caption'] if photo['caption'] else '美好时光'
    max_text_w = A4_W - 2 * MARGIN
    lines = wrap_text(draw, caption, font_caption, max_text_w)
    caption_y = max_photo_h + 35*20//10 + 25 + (dt_bbox[3] - dt_bbox[1]) + 25
    for j, line in enumerate(lines):
        draw.text((MARGIN, caption_y + j * 48), line, fill='#4A4A4A', font=font_caption)

    # 底部装饰线
    draw.line([(MARGIN, A4_H - 25*20//10), (A4_W - MARGIN, A4_H - 25*20//10)], fill='#FFB6C1', width=2)

    jpg_path = os.path.join(OUTPUT_DIR, f"pdf_page_{i:04d}.jpg")
    page.save(jpg_path, 'JPEG', quality=92)
    page_jpgs.append(jpg_path)
    page.close()

print(f"✅ 生成 {len(page_jpgs)} 页JPEG", flush=True)

# ==================== 封面 ====================
print("📝 生成封面...", flush=True)
cover = Image.new('RGB', (A4_W, A4_H), '#FFE4F0')
draw = ImageDraw.Draw(cover)

tb = draw.textbbox((0, 0), "粉粉的成长时光", font=font_cover_title)
tx = (A4_W - (tb[2] - tb[0])) // 2
ty = (A4_H - (tb[3] - tb[1])) // 2 - 80
draw.text((tx, ty), "粉粉的成长时光", fill='#FF69B4', font=font_cover_title)

sb = draw.textbbox((0, 0), "2020 - 2026", font=font_cover_sub)
sx = (A4_W - (sb[2] - sb[0])) // 2
draw.text((sx, ty + (tb[3] - tb[1]) + 50), "2020 - 2026", fill='#FF8C69', font=font_cover_sub)

cover_path = os.path.join(OUTPUT_DIR, 'pdf_cover.jpg')
cover.save(cover_path, 'JPEG', quality=92)
cover.close()

# 合并封面 + 内容页为PDF
print(f"💾 合并为PDF...", flush=True)
all_jpgs = [cover_path] + page_jpgs

# 使用PIL save_all将多张图片合并为PDF
imgs = []
for jpg in all_jpgs:
    imgs.append(Image.open(jpg))

imgs[0].save(
    OUTPUT_PDF,
    'PDF',
    save_all=True,
    append_images=imgs[1:],
    resolution=200.0,
    quality=90,
    duration=1000,
)

# 清理临时文件
print("🧹 清理临时文件...", flush=True)
for jpg in all_jpgs:
    try:
        os.remove(jpg)
    except:
        pass
for img in imgs:
    img.close()

file_size = os.path.getsize(OUTPUT_PDF)
print(f"\n✅ PDF生成完成！", flush=True)
print(f"📁 {OUTPUT_PDF}", flush=True)
print(f"📄 共 {len(all_jpgs)} 页（含封面）", flush=True)
print(f"📦 大小: {file_size/(1024*1024):.1f} MB", flush=True)
print("\n🎉 全部完成！", flush=True)
