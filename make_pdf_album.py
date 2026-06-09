#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
粉粉成长相册 - PDF打印版生成器
A4纸布局，照片+日期+文案，适合打印
"""

import json
import os
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas

# ==================== 配置 ====================
DATA_JSON = r"E:\lenovo\GrowthAlbum@Github\Siry-s-Growth-Photo-Album\data.json"
PHOTOS_BASE = r"E:\lenovo\GrowthAlbum@Github\Siry-s-Growth-Photo-Album\photos"
OUTPUT_PDF = r"E:\lenovo\粉粉成长记录\粉粉的成长时光_打印版.pdf"

# PDF 页面设置 (A4: 210 x 297 mm)
PAGE_WIDTH = A4[0]  # 210mm
PAGE_HEIGHT = A4[1]  # 297mm
MARGIN = 15 * mm  # 页边距

# 布局参数 - 每页一张大图 + 底部文案
PHOTO_AREA_TOP = 20 * mm      # 照片区顶部
PHOTO_AREA_HEIGHT = 200 * mm  # 照片区域高度
TEXT_AREA_TOP = PHOTO_AREA_TOP + PHOTO_AREA_HEIGHT + 10 * mm  # 文字区域顶部
TEXT_AREA_HEIGHT = PAGE_HEIGHT - TEXT_AREA_TOP - 10 * mm  # 文字区域高度

def get_font(size):
    """获取中文字体"""
    for fp in [
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\simsun.ttc",
        r"C:\Windows\Fonts\fangsong.ttf"
    ]:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except:
                pass
    return ImageFont.load_default()

def scale_photo_for_cover(photo_img, max_w, max_h):
    """缩放照片保持比例，居中裁剪到指定区域"""
    pw, ph = photo_img.size
    ratio = pw / ph
    area_ratio = max_w / max_h
    
    if ratio > area_ratio:
        # 照片更宽，按高度缩放
        new_h = max_h
        new_w = int(ph * ratio * (max_h / ph))
        if new_w > max_w:
            new_w = max_w
    else:
        # 照片更高，按宽度缩放
        new_w = max_w
        new_w = int(pw)
        new_h = int(ph * (max_w / pw))
    
    # 更准确的缩放
    scale_w = max_w / pw
    scale_h = max_h / ph
    scale = min(scale_w, scale_h)
    new_w = int(pw * scale)
    new_h = int(ph * scale)
    
    resized = photo_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # 创建白色背景
    bg = Image.new('RGB', (max_w, max_h), '#FFFFFF')
    x = (max_w - new_w) // 2
    y = (max_h - new_h) // 2
    bg.paste(resized, (x, y))
    return bg

# ==================== 加载数据 ====================
print("📖 加载相册数据...")
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
print(f"📸 共 {len(all_photos)} 张照片")

# ==================== 创建PDF ====================
print("🎨 生成PDF打印版...")
c = canvas.Canvas(OUTPUT_PDF, pagesize=A4)
c.setTitle("粉粉的成长时光 - 打印版")
c.setAuthor("粉粉的成长相册")

# 标题页
c.setFillAlpha(1)
c.setFillColor(HexColor('#FFE4F0'))
c.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)

# 标题
title_font = get_font(60)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 注册字体
font_registered = False
for font_name, font_path in [
    ('msyh', r'C:\Windows\Fonts\msyh.ttc'),
    ('simhei', r'C:\Windows\Fonts\simhei.ttf'),
    ('simsun', r'C:\Windows\Fonts\simsun.ttc'),
]:
    if os.path.exists(font_path):
        try:
            TTFont(font_name, font_path)
            pdfmetrics.registerFont(TTFont(font_name, font_path))
            pdfmetrics.setFonts([font_name])
            font_registered = True
            print(f"✅ 字体注册成功: {font_name}")
            break
        except Exception as e:
            print(f"⚠️ 字体注册失败: {font_name}: {e}")

if not font_registered:
    print("❌ 无法注册中文字体，使用默认字体")

for i, photo in enumerate(all_photos):
    print(f"  处理 {i+1}/{len(all_photos)}: {photo['file']}")
    
    # 每页开始新页
    c.showPage()
    
    # 背景 - 淡粉色
    c.setFillColor(HexColor('#FFF5F8'))
    c.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
    
    # 顶部装饰线
    c.setStrokeColor(HexColor('#FFB6C1'))
    c.setLineWidth(2)
    c.line(20*mm, PAGE_HEIGHT - 25*mm, PAGE_WIDTH - 20*mm, PAGE_HEIGHT - 25*mm)
    
    # 年龄段标签
    c.setFillColor(HexColor('#FF69B4'))
    c.roundRect(25*mm, PAGE_HEIGHT - 35*mm, 30*mm, 10*mm, 3*mm, fill=1, stroke=0)
    if font_registered:
        c.setFont('msyh', 9)
        c.drawString(26.5*mm, PAGE_HEIGHT - 34*mm, photo['age'])
    
    # 加载照片
    photo_img = None
    if os.path.exists(photo['photo_path']):
        try:
            photo_img = Image.open(photo['photo_path']).convert('RGB')
        except:
            print(f"  ⚠️  无法打开: {photo['photo_path']}")
    
    if photo_img:
        # 缩放照片到合适大小
        max_photo_w = int((PAGE_WIDTH - 40*mm))
        max_photo_h = int(180*mm)
        scaled = scale_photo_for_cover(photo_img, max_photo_w, max_photo_h)
        
        # 将PIL图像保存到临时文件供reportlab使用
        import tempfile
        tmp_path = os.path.join(tempfile.gettempdir(), f"pdf_photo_{i}.jpg")
        scaled.save(tmp_path, 'JPEG', quality=90)
        
        # 插入照片
        photo_x = 25 * mm
        photo_y = PHOTO_AREA_TOP
        c.drawImage(tmp_path, photo_x, photo_y, 
                     width=max_photo_w, height=max_photo_h,
                     preserveAspectRatio=True, anchor='c')
        
        # 删除临时文件
        import os
        try:
            os.remove(tmp_path)
        except:
            pass
    
    # 日期和文案区域
    text_y = TEXT_AREA_TOP
    
    # 日期
    if font_registered:
        c.setFillColor(HexColor('#FF8C69'))
        c.setFont('msyh', 14)
        date_text = f"📅 {photo['date']}"
        c.drawString(25*mm, text_y, date_text)
        
        # 文案
        c.setFillColor(HexColor('#4A4A4A'))
        c.setFont('msyh', 12)
        caption = photo['caption'] if photo['caption'] else '美好时光'
        
        # 文字换行
        max_text_width = PAGE_WIDTH - 50*mm
        char_width = 6.5  # 约等于一个中文字宽度
        max_chars_per_line = int(max_text_width / char_width)
        
        lines = []
        current_line = ""
        for ch in caption:
            current_line += ch
            if len(current_line) >= max_chars_per_line:
                lines.append(current_line)
                current_line = ""
        if current_line:
            lines.append(current_line)
        
        line_height = 18 * mm
        for j, line in enumerate(lines):
            c.drawString(25*mm, text_y - 15*mm - j * line_height, line)
    
    # 底部装饰
    c.setStrokeColor(HexColor('#FFB6C1'))
    c.setLineWidth(1)
    c.line(20*mm, 20*mm, PAGE_WIDTH - 20*mm, 20*mm)

# 保存PDF
c.save()
print(f"\n✅ PDF生成完成！")
print(f"📁 {OUTPUT_PDF}")
print(f"📄 共 {len(all_photos) + 1} 页（含封面）")
