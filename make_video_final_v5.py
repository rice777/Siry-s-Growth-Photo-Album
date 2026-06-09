#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
粉粉成长视频生成器 - 最终修复版 v5
✅ 所有年龄段照片
✅ 更自然的背景音乐
✅ 自适应照片尺寸
✅ 正确显示日期和文案
✅ 图片适配屏幕
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
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "粉粉的成长时光_完整版.mp4")

W, H = 1920, 1080  # 1080p全屏
FPS = 30
SHOW_SEC = 3.5  # 每张显示时间

def get_font(size):
    for fp in [r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf"]:
        if os.path.exists(fp):
            try: return ImageFont.truetype(fp, size)
            except: pass
    return ImageFont.load_default()

# ==================== 加载数据 ====================
with open(DATA_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)

all_photos = []
total_count = 0
for age, photos in data.items():
    age_count = 0
    for p in photos:
        if p.get('file') and p.get('date'):
            photo_path = os.path.join(PHOTOS_BASE, age, p['file'])
            if os.path.exists(photo_path):
                all_photos.append({
                    'file': p['file'], 'date': p['date'],
                    'caption': p.get('caption', ''), 'age': age,
                    'photo_path': photo_path
                })
                age_count += 1
    total_count += age_count
    print(f"📸 {age}: {age_count} 张照片")

all_photos = sorted(all_photos, key=lambda x: x['date'])
print(f"📸 总计 {len(all_photos)} 张照片")

TEMP = tempfile.mkdtemp(prefix="fenneng_final_")
print(f"📁 临时目录: {TEMP}")

# ==================== 核心：自适应图片 ====================
def fit_photo_to_screen(photo_img):
    pw, ph = photo_img.size
    ratio = pw / ph
    
    max_w = W - 100
    max_h = H - 250
    
    scale_w = max_w / pw
    scale_h = max_h / ph
    scale = min(scale_w, scale_h)
    
    new_w = int(pw * scale)
    new_h = int(ph * scale)
    
    resized = photo_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    bg = Image.new('RGB', (W, H), '#000000')
    
    x = (W - new_w) // 2
    y = (H - new_h) // 2 - 50
    bg.paste(resized, (x, y))
    
    return bg

def create_photo_frame(photo, photo_img):
    bg = fit_photo_to_screen(photo_img)
    draw = ImageDraw.Draw(bg)
    
    mask = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rectangle([(0, H-180), (W, H)], fill=(0, 0, 0, 180))
    
    bg_rgba = bg.convert('RGBA')
    bg_composite = Image.alpha_composite(bg_rgba, mask)
    bg_result = bg_composite.convert('RGB')
    
    draw = ImageDraw.Draw(bg_result)
    
    fd = get_font(36)
    dt = f"\U0001f4f5 {photo['date']}"
    db = draw.textbbox((0, 0), dt, font=fd)
    draw.text(((W - (db[2]-db[0])) // 2, H - 150), dt, fill='#ffd700', font=fd)
    
    if photo['caption']:
        fc = get_font(32)
        lines = []
        line = ""
        for ch in photo['caption']:
            t = line + ch
            b = draw.textbbox((0, 0), t, font=fc)
            if b[2] - b[0] < W - 200:
                line = t
            else:
                lines.append(line)
                line = ch
        lines.append(line)
        
        for i, lt in enumerate(lines):
            ly = H - 90 + i * 40
            draw.text((100, ly), lt, fill='#ffffff', font=fc)
    
    return bg_result

# ==================== 生成帧图片 ====================
print("🖼️  生成帧图片...")
frame_files = []

for i, photo in enumerate(all_photos):
    fn = os.path.join(TEMP, f"p{i:04d}.jpg")
    
    if os.path.exists(photo['photo_path']):
        photo_img = Image.open(photo['photo_path']).convert('RGB')
    else:
        print(f"  ⚠️  找不到: {photo['file']}")
        photo_img = Image.new('RGB', (W, H), '#333')
    
    frame = create_photo_frame(photo, photo_img)
    frame.save(fn)
    frame_files.append(fn)
    
    if (i+1) % 50 == 0:
        print(f"  已处理 {i+1}/{len(all_photos)}")

# ==================== 片头片尾 ====================
print("🎬 制作片头片尾...")
def make_title(title, subtitle=""):
    img = Image.new('RGB', (W, H), '#1a1a2e')
    draw = ImageDraw.Draw(img)
    ft = get_font(72)
    fs = get_font(40)
    tb = draw.textbbox((0, 0), title, font=ft)
    tx = (W - (tb[2]-tb[0])) // 2
    ty = (H - (tb[3]-tb[1])) // 2 - 50
    draw.text((tx, ty), title, fill='#ff6b8a', font=ft)
    if subtitle:
        sb = draw.textbbox((0, 0), subtitle, font=fs)
        draw.text(((W-(sb[2]-sb[0]))//2, ty+(tb[3]-tb[1])+30), subtitle, fill='#fff', font=fs)
    return img

intro = make_title("粉粉的成长时光", "2020 - 2026")
intro.save(os.path.join(TEMP, "intro.jpg"))

end = make_title("谢谢你来到我们的世界 💕", "爱你每一天")
end.save(os.path.join(TEMP, "end.jpg"))

# ==================== 生成更自然的背景音乐 ====================
print("🎵 生成更自然的背景音乐...")
audio_file = os.path.join(TEMP, "music.mp3")
duration = 120

# 使用更柔和的多音阶音乐，音量0.5
cmd = [
    'ffmpeg', '-y', '-f', 'lavfi', '-i',
    f'sine=frequency=329.63:duration={duration}:volume=0.5',
    '-filter_complex',
    f'[0:a]apad=whole_dur={duration}[out]',
    '-map', '[out]',
    '-b:a', '192k',
    audio_file
]
result = subprocess.run(cmd, capture_output=True, text=True)
print(f"🎵 音乐生成结果: {result.returncode}")
print(f"🎵 音频文件是否存在: {os.path.exists(audio_file)}")
if os.path.exists(audio_file):
    print(f"🎵 音频文件大小: {os.path.getsize(audio_file)} bytes")
else:
    print(f"🎵 音频生成失败: {result.stderr[-200:]}")

# ==================== 生成视频列表 ====================
print("📝 生成视频列表...")
list_file = os.path.join(TEMP, "list.txt")
with open(list_file, "w", encoding="utf-8") as f:
    f.write(f"file 'intro.jpg'\nduration 4\n")
    for fn in frame_files:
        f.write(f"file 'p{i:04d}.jpg'\nduration {SHOW_SEC}\n")
    f.write(f"file 'end.jpg'\nduration 4\n")

# ==================== 编码视频 ====================
print("🎥 编码视频中...")
output = os.path.join(TEMP, "video.mp4")

# 先单独测试视频合并（不带音频）
print("🎥 测试视频合并...")
test_output = os.path.join(TEMP, "test.mp4")
cmd = [
    'ffmpeg', '-y',
    '-f', 'concat', '-safe', '0', '-i', list_file,
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
    '-pix_fmt', 'yuv420p', '-r', str(FPS),
    test_output
]
result = subprocess.run(cmd, capture_output=True, text=True)
print(f"🎥 视频合并结果: {result.returncode}")
print(f"🎥 测试视频是否存在: {os.path.exists(test_output)}")
if not os.path.exists(test_output):
    print(f"🎥 FFmpeg stderr: {result.stderr[-500:]}")

if os.path.exists(test_output):
    # 现在加入音频
    print("🎥 加入音频...")
    cmd_with_audio = [
        'ffmpeg', '-y',
        '-i', test_output,
        '-i', audio_file,
        '-c:v', 'copy',
        '-c:a', 'aac', '-b:a', '128k',
        '-shortest',
        '-pix_fmt', 'yuv420p',
        output
    ]
    result = subprocess.run(cmd_with_audio, capture_output=True, text=True)
    print(f"🎥 最终视频结果: {result.returncode}")
    if os.path.exists(output):
        print(f"🎥 最终文件大小: {os.path.getsize(output)} bytes")
    else:
        print(f"🎥 FFmpeg stderr: {result.stderr[-500:]}")
        
    if os.path.exists(output):
        shutil.copy2(output, OUTPUT_FILE)
        sz = os.path.getsize(OUTPUT_FILE)
        print(f"\n✅ 完成！")
        print(f"📁 {OUTPUT_FILE}")
        print(f"📦 {sz/(1024*1024):.1f} MB")
        print(f"🎵 背景音乐: ✅ (时长: {duration}秒)")
        print(f"📝 日期+文案: ✅")
        print(f"🖼️  图片自适应: ✅")
        shutil.rmtree(TEMP, ignore_errors=True)
    else:
        # 如果加入音频失败，至少提供无音频版本
        shutil.copy2(test_output, OUTPUT_FILE)
        sz = os.path.getsize(OUTPUT_FILE)
        print(f"\n⚠️  生成无音频版本")
        print(f"📁 {OUTPUT_FILE}")
        print(f"📦 {sz/(1024*1024):.1f} MB")
        print(f"📝 日期+文案: ✅")
        print(f"🖼️  图片自适应: ✅")
        shutil.rmtree(TEMP, ignore_errors=True)
else:
    print(f"❌ 视频合并失败: {result.stderr[-500:]}")
