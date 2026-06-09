#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
粉粉成长视频生成器 - 优化版（直接用ffmpeg拼接，不生成中间帧）
"""

import json
import os
import subprocess
import tempfile
import shutil
from PIL import Image, ImageDraw, ImageFont

DATA_JSON = r"E:\lenovo\GrowthAlbum@Github\Siry-s-Growth-Photo-Album\data.json"
PHOTOS_BASE = r"E:\lenovo\GrowthAlbum@Github\Siry-s-Growth-Photo-Album\photos"
OUTPUT_DIR = r"E:\lenovo\Milo\粉粉成长记录"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "粉粉的成长时光.mp4")

W, H = 1920, 1080
FPS = 30
SHOW_SEC = 4  # 每张显示4秒

def get_font(size):
    for fp in [r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf"]:
        if os.path.exists(fp):
            try: return ImageFont.truetype(fp, size)
            except: pass
    return ImageFont.load_default()

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

TEMP = tempfile.mkdtemp(prefix="fenneng_")

def make_frame(photo, photo_img):
    bg = Image.new('RGB', (W, H), '#000')
    draw = ImageDraw.Draw(bg)
    
    pw, ph = photo_img.size
    mw, mh = W-100, H-350
    s = min(mw/pw, mh/ph, 1.0)
    nw, nh = int(pw*s), int(ph*s)
    r = photo_img.resize((nw, nh), Image.Resampling.LANCZOS)
    x = (W-nw)//2
    y = (H-nh)//2 - 50
    bg.paste(r, (x, y))
    
    fd = get_font(36)
    fc = get_font(32)
    dt = f"\U0001f4f5 {photo['date']}"
    db = draw.textbbox((0,0), dt, font=fd)
    draw.text(((W-(db[2]-db[0]))//2, y+nh+20), dt, fill='#ffd700', font=fd)
    
    if photo['caption']:
        lines = []
        line = ""
        for ch in photo['caption']:
            t = line + ch
            b = draw.textbbox((0,0), t, font=fc)
            if b[2]-b[0] < W-200: line = t
            else: lines.append(line); line = ch
        lines.append(line)
        for i, lt in enumerate(lines):
            draw.text((50, y+nh+80+i*45), lt, fill='#ccc', font=fc)
    
    return bg

# 生成所有照片帧文件
frame_files = []
for i, photo in enumerate(all_photos):
    fn = os.path.join(TEMP, f"p{i:04d}.jpg")
    if os.path.exists(photo['photo_path']):
        img = Image.open(photo['photo_path'])
    else:
        img = Image.new('RGB', (W, H), '#333')
        draw = ImageDraw.Draw(img)
        draw.text((500, 500), f"❌ {photo['file']}", fill='#fff', font=get_font(40))
    img.save(fn)
    frame_files.append((fn, photo))
    if (i+1) % 50 == 0: print(f"  已处理 {i+1}/{len(all_photos)}")

print(f"\n🎬 生成 {len(frame_files)} 张帧图片")

# 创建 ffmpeg 输入列表
list_file = os.path.join(TEMP, "input_list.txt")
with open(list_file, "w", encoding="utf-8") as f:
    for fn, _ in frame_files:
        f.write(f"file '{fn}'\nduration {SHOW_SEC}\n")

# 生成片头和片尾
intro_fn = os.path.join(TEMP, "intro.jpg")
intro = Image.new('RGB', (W, H), '#1a1a2e')
draw = ImageDraw.Draw(intro)
fd = get_font(72)
fs = get_font(40)
tb = draw.textbbox((0,0), "粉粉的成长时光", font=fd)
tx = (W-(tb[2]-tb[0]))//2
ty = (H-(tb[3]-tb[1]))//2 - 50
draw.text((tx, ty), "粉粉的成长时光", fill='#ff6b8a', font=fd)
sb = draw.textbbox((0,0), "2020 - 2026", font=fs)
draw.text(((W-(sb[2]-sb[0]))//2, ty+(tb[3]-tb[1])+30), "2020 - 2026", fill='#fff', font=fs)
intro.save(intro_fn)

end_fn = os.path.join(TEMP, "end.jpg")
end = Image.new('RGB', (W, H), '#1a1a2e')
draw = ImageDraw.Draw(end)
tb2 = draw.textbbox((0,0), "谢谢你来到我们的世界 💕", font=fd)
draw.text(((W-(tb2[2]-tb2[0]))//2, (H-60)//2), "谢谢你来到我们的世界 💕", fill='#ff6b8a', font=fd)
sb2 = draw.textbbox((0,0), "爱你每一天", font=fs)
draw.text(((W-(sb2[2]-sb2[0]))//2, (H-60)//2+80), "爱你每一天", fill='#fff', font=fs)
end.save(end_fn)

# 构建完整列表
full_list = os.path.join(TEMP, "full_list.txt")
with open(full_list, "w", encoding="utf-8") as f:
    f.write(f"file '{intro_fn}'\nduration 4\n")
    for fn, _ in frame_files:
        f.write(f"file '{fn}'\nduration {SHOW_SEC}\n")
    f.write(f"file '{end_fn}'\nduration 4\n")

print(f"🎥 编码视频中...（这可能需要几分钟）")
cmd = [
    'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', full_list,
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
    '-pix_fmt', 'yuv420p', '-r', str(FPS),
    OUTPUT_FILE
]
result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode == 0:
    sz = os.path.getsize(OUTPUT_FILE)
    print(f"\n✅ 完成！")
    print(f"📁 {OUTPUT_FILE}")
    print(f"📦 {sz/(1024*1024):.1f} MB")
    shutil.rmtree(TEMP, ignore_errors=True)
else:
    print(f"❌ 失败: {result.stderr[-500:]}")
