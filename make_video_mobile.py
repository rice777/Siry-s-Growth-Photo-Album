#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
粉粉成长相册 - 手机竖屏版视频
9:16 竖屏比例，适合手机观看
照片放大，适配手机全屏播放
"""

import json
import os
import subprocess
from PIL import Image, ImageDraw, ImageFont

# ==================== 配置 ====================
DATA_JSON = r"E:\lenovo\GrowthAlbum@Github\Siry-s-Growth-Photo-Album\data.json"
PHOTOS_BASE = r"E:\lenovo\GrowthAlbum@Github\Siry-s-Growth-Photo-Album\photos"
OUTPUT_DIR = r"E:\lenovo\粉粉成长记录"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "粉粉的成长时光_手机版.mp4")

# 9:16 竖屏比例 (720x1280)
W, H = 720, 1280
FPS = 30
SHOW_SEC = 3.5

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

# ==================== 创建帧图片 ====================
print("🎨 生成帧图片 (720x1280 竖屏)...", flush=True)
TEMP = r"E:\lenovo\粉粉成长记录\temp_frames"
os.makedirs(TEMP, exist_ok=True)

# 清理旧帧
for f in os.listdir(TEMP):
    os.remove(os.path.join(TEMP, f))

frame_files = []
total = len(all_photos)

for i, photo in enumerate(all_photos):
    if (i+1) % 50 == 0:
        print(f"  处理 {i+1}/{total}", flush=True)

    fn = os.path.join(TEMP, f"p{i:04d}.jpg")
    
    # 深色背景
    bg = Image.new('RGB', (W, H), '#1a1a2e')
    draw = ImageDraw.Draw(bg)
    
    # 加载照片
    photo_img = None
    if os.path.exists(photo['photo_path']):
        try:
            photo_img = Image.open(photo['photo_path']).convert('RGB')
        except:
            pass
    
    if photo_img:
        # 竖屏适配：照片占屏幕 75% 宽度，留空间给文字
        max_w = int(W * 0.85)  # 照片宽度
        max_h = int(H * 0.65)  # 照片高度 (留空间给文字)
        
        pw, ph = photo_img.size
        scale = min(max_w / pw, max_h / ph, 1.0)
        nw, nh = int(pw * scale), int(ph * scale)
        resized = photo_img.resize((nw, nh), Image.Resampling.LANCZOS)
        
        # 居中粘贴到深色背景
        x = (W - nw) // 2
        y = int(H * 0.28)  # 照片居中偏上
        bg.paste(resized, (x, y))
    else:
        # 默认灰色背景
        bg = Image.new('RGB', (W, H), '#333333')
    
    # 添加日期和文字
    date_font = get_font(24)
    caption_font = get_font(20)
    
    # 日期 (金色)
    dt_text = f"📅 {photo['date']}"
    draw.text((20, 15), dt_text, fill='#FFD700', font=date_font)
    
    # 文案 (白色，带阴影)
    if photo['caption']:
        # 文字背景条 (半透明黑色)
        text_bg_y = H - 150
        for y_line in range(text_bg_y, H):
            draw.line([(0, y_line), (W, y_line)], fill=(0, 0, 0, 180))
        
        # 换行处理
        lines = []
        current = ""
        for ch in photo['caption']:
            test = current + ch
            bbox = draw.textbbox((0, 0), test, font=caption_font)
            if bbox[2] - bbox[0] < W - 40:
                current = test
            else:
                if current:
                    lines.append(current)
                current = ch
        if current:
            lines.append(current)
        
        # 绘制文字
        for j, line in enumerate(lines):
            draw.text((20, text_bg_y + 15 + j * 28), line, fill='#FFFFFF', font=caption_font)
    
    # 年龄段标签 (粉色背景)
    age_font = get_font(16)
    draw.rectangle([(W - 120, 10), (W - 20, 35)], fill='#FF69B4')
    draw.text((W - 115, 12), photo['age'], fill='#FFFFFF', font=age_font)
    
    bg.save(fn, 'JPEG', quality=90)
    frame_files.append(fn)

print(f"✅ 生成 {len(frame_files)} 帧（不含片头片尾）", flush=True)

# ==================== 片头片尾 ====================
print("🎬 制作片头片尾...", flush=True)

# 片头
intro = Image.new('RGB', (W, H), '#1a1a2e')
draw = ImageDraw.Draw(intro)
intro_font = get_font(48)
intro_sub = get_font(32)

tb = draw.textbbox((0, 0), "粉粉的成长时光", font=intro_font)
tx = (W - (tb[2] - tb[0])) // 2
ty = (H - (tb[3] - tb[1])) // 2 - 30
draw.text((tx, ty), "粉粉的成长时光", fill='#ff6b8a', font=intro_font)

sb = draw.textbbox((0, 0), "2020 - 2026", font=intro_sub)
draw.text(((W-(sb[2]-sb[0]))//2, ty+(tb[3]-tb[1])+30), "2020 - 2026", fill='#fff', font=intro_sub)
intro_path = os.path.join(TEMP, "intro.jpg")
intro.save(intro_path, 'JPEG', quality=90)

# 片尾
end = Image.new('RGB', (W, H), '#1a1a2e')
draw = ImageDraw.Draw(end)
draw.text((tx, ty), "谢谢你来到我们的世界", fill='#ff6b8a', font=intro_font)
draw.text(((W-(sb[2]-sb[0]))//2, ty+(tb[3]-tb[1])+30), "爱你每一天 💕", fill='#fff', font=intro_sub)
end_path = os.path.join(TEMP, "end.jpg")
end.save(end_path, 'JPEG', quality=90)

# 加入帧列表（片头4秒 + 照片 + 片尾4秒）
all_frames = [intro_path] + frame_files + [end_path]
print(f"✅ 总帧数: {len(all_frames)}（含片头片尾）", flush=True)

# ==================== 生成视频 ====================
print("🎬 生成视频...", flush=True)
list_file = os.path.join(TEMP, "list.txt")
with open(list_file, "w", encoding="utf-8") as f:
    # 片头4秒
    f.write(f"file '{intro_path}'\nduration 4\n")
    # 照片帧
    for fn in frame_files:
        f.write(f"file '{fn}'\nduration {SHOW_SEC}\n")
    # 片尾4秒
    f.write(f"file '{end_path}'\nduration 4\n")

cmd = [
    'ffmpeg', '-y',
    '-f', 'concat', '-safe', '0', '-i', list_file,
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
    '-pix_fmt', 'yuv420p', '-r', str(FPS),
    '-movflags', '+faststart',  # 优化网络播放
    os.path.join(TEMP, "video.mp4")
]

result = subprocess.run(cmd, capture_output=True, text=True)

if result.returncode == 0 and os.path.exists(os.path.join(TEMP, "video.mp4")):
    # 复制输出文件
    import shutil
    shutil.copy2(os.path.join(TEMP, "video.mp4"), OUTPUT_FILE)
    
    file_size = os.path.getsize(OUTPUT_FILE)
    duration = total * SHOW_SEC + 8  # +8 秒（片头4+片尾4）
    
    print(f"\n✅ 手机竖屏版视频生成完成！", flush=True)
    print(f"📁 {OUTPUT_FILE}", flush=True)
    print(f"📄 共 {total} 张照片 + 片头片尾", flush=True)
    print(f"⏱️ 时长: {duration/60:.1f} 分钟", flush=True)
    print(f"📦 大小: {file_size/(1024*1024):.1f} MB", flush=True)
    print(f"📱 分辨率: {W}x{H} (9:16 竖屏)", flush=True)
    print(f"🎵 注意：此版本无背景音乐，如需配乐请指定音乐文件", flush=True)
    
    # 清理临时文件
    import shutil
    shutil.rmtree(TEMP, ignore_errors=True)
else:
    print(f"❌ 视频生成失败: {result.stderr[-500:]}", flush=True)
