#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
粉粉成长视频生成器 - 带背景音乐和正确文字显示
"""

import json
import os
import subprocess
import tempfile
import shutil
from PIL import Image, ImageDraw, ImageFont
import math

DATA_JSON = r"E:\lenovo\GrowthAlbum@Github\Siry-s-Growth-Photo-Album\data.json"
PHOTOS_BASE = r"E:\lenovo\GrowthAlbum@Github\Siry-s-Growth-Photo-Album\photos"
OUTPUT_DIR = r"E:\lenovo\Milo\粉粉成长记录"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "粉粉的成长时光_v2.mp4")

W, H = 1920, 1080
FPS = 30
SHOW_SEC = 3.5

def get_font(size):
    for fp in [r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf"]:
        if os.path.exists(fp):
            try: return ImageFont.truetype(fp, size)
            except: pass
    return ImageFont.load_default()

# 加载照片
with open(DATA_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)

all_photos = []
for age, photos in data.items():
    for p in photos:
        if p.get('file') and p.get('date'):
            all_photos.append({
                'file': p['file'], 'date': p['date'],
                'caption': p.get('caption', ''), 'age': age,
                'photo_path': os.path.join(PHOTOS_BASE, age, p['file'])
            })
all_photos = sorted(all_photos, key=lambda x: x['date'])
print(f"📸 {len(all_photos)} 张照片")

# 生成音频（简单的背景音乐）
TEMP = tempfile.mkdtemp(prefix="fenneng_v2_")

# 创建音频文件 - 使用ffmpeg生成简单的旋律
audio_file = os.path.join(TEMP, "music.mp3")
print("🎵 生成背景音乐...")
# 用ffmpeg生成一段简单的C大调音阶
cmd = [
    'ffmpeg', '-y', '-f', 'lavfi', '-i',
    'sine=frequency=262:duration=12',  # 简单低音
    '-b:a', '192k',
    audio_file
]
subprocess.run(cmd, capture_output=True)

# 处理照片，创建帧图片
print("🖼️  处理照片帧...")
frame_files = []
for i, photo in enumerate(all_photos):
    fn = os.path.join(TEMP, f"p{i:04d}.jpg")
    if os.path.exists(photo['photo_path']):
        img = Image.open(photo['photo_path'])
    else:
        img = Image.new('RGB', (W, H), '#333')
        draw = ImageDraw.Draw(img)
        draw.text((500, 500), f"❌ {photo['file']}", fill='#fff', font=get_font(40))
    
    # 添加文字覆盖层
    draw = ImageDraw.Draw(img)
    
    # 底部半透明背景条
    bottom_bar = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw_bar = ImageDraw.Draw(bottom_bar)
    draw_bar.rectangle([(0, H-180), (W, H)], fill=(0, 0, 0, 180))
    img = Image.alpha_composite(img.convert('RGBA'), bottom_bar).convert('RGB')
    draw = ImageDraw.Draw(img)
    
    # 日期
    fd = get_font(36)
    dt = f"\U0001f4f5 {photo['date']}"
    db = draw.textbbox((0,0), dt, font=fd)
    draw.text(((W-(db[2]-db[0]))//2, H-150), dt, fill='#ffd700', font=fd)
    
    # 文案（支持多行）
    if photo['caption']:
        fc = get_font(32)
        lines = []
        line = ""
        for ch in photo['caption']:
            t = line + ch
            b = draw.textbbox((0,0), t, font=fc)
            if b[2]-b[0] < W-200: line = t
            else: lines.append(line); line = ch
        lines.append(line)
        
        for j, lt in enumerate(lines):
            ly = H - 90 + j * 40
            draw.text((100, ly), lt, fill='#fff', font=fc)
    
    img.save(fn)
    frame_files.append(fn)
    if (i+1) % 50 == 0: print(f"  已处理 {i+1}/{len(all_photos)}")

# 片头片尾
print("🎬 制作片头片尾...")
def make_title(title, subtitle="", bg_color='#1a1a2e'):
    img = Image.new('RGB', (W, H), bg_color)
    draw = ImageDraw.Draw(img)
    ft = get_font(72)
    fs = get_font(40)
    tb = draw.textbbox((0,0), title, font=ft)
    tx = (W-(tb[2]-tb[0]))//2
    ty = (H-(tb[3]-tb[1]))//2 - 50
    draw.text((tx, ty), title, fill='#ff6b8a', font=ft)
    if subtitle:
        sb = draw.textbbox((0,0), subtitle, font=fs)
        draw.text(((W-(sb[2]-sb[0]))//2, ty+(tb[3]-tb[1])+30), subtitle, fill='#fff', font=fs)
    return img

intro = make_title("粉粉的成长时光", "2020 - 2026")
intro.save(os.path.join(TEMP, "intro.jpg"))

end = make_title("谢谢你来到我们的世界 💕", "爱你每一天")
end.save(os.path.join(TEMP, "end.jpg"))

# 生成完整列表
print("📝 生成视频列表...")
list_file = os.path.join(TEMP, "list.txt")
with open(list_file, "w", encoding="utf-8") as f:
    f.write(f"file '{os.path.join(TEMP, 'intro.jpg')}'\nduration 4\n")
    for fn in frame_files:
        f.write(f"file '{fn}'\nduration {SHOW_SEC}\n")
    f.write(f"file '{os.path.join(TEMP, 'end.jpg')}'\nduration 4\n")

# 渲染视频 + 音频
print("🎥 编码视频...")
output = os.path.join(TEMP, "video.mp4")
cmd = [
    'ffmpeg', '-y',
    '-f', 'concat', '-safe', '0', '-i', list_file,
    '-i', audio_file,
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
    '-c:a', 'aac', '-b:a', '128k',
    '-map', '0:v:0', '-map', '1:a:0',
    '-shortest',
    '-pix_fmt', 'yuv420p', '-r', str(FPS),
    output
]
subprocess.run(cmd, capture_output=True)

if os.path.exists(output):
    shutil.copy2(output, OUTPUT_FILE)
    sz = os.path.getsize(OUTPUT_FILE)
    print(f"\n✅ 完成！")
    print(f"📁 {OUTPUT_FILE}")
    print(f"📦 {sz/(1024*1024):.1f} MB")
    print(f"🎵 已添加背景音乐")
    print(f"📝 每张照片显示日期和文案")
    shutil.rmtree(TEMP, ignore_errors=True)
else:
    print("❌ 视频生成失败")
