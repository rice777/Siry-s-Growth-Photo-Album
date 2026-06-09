#!/usr/bin/env python3
"""
图片压缩工具：将相册照片批量压缩为 WebP 格式，并生成缩略图。
- 原图保留（不覆盖）
- 生成缩略图(1200px宽)到 thumbs/ 目录
- 生成缩略图(400px宽)到 thumb400/ 目录
- 输出 WebP 质量 82，通常可减少 60-70% 体积

用法:
  python compress_photos.py                    # 压缩所有照片（预览模式，不保存）
  python compress_photos.py --first 5          # 只压缩前5张测试
  python compress_photos.py --apply            # 正式执行并保存
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from PIL import Image

# ===================== 配置 =====================
ALBUM_DIR = Path(r"E:\lenovo\GrowthAlbum@Github\Siry-s-Growth-Photo-Album")
PHOTOS_DIR = ALBUM_DIR / "photos"
OUTPUT_BASE = ALBUM_DIR / "compressed"  # 压缩输出目录

THUMB_WIDE = 1200   # 详情页缩略图宽度
THUMB_THIN = 400    # 列表页缩略图宽度
WEBP_QUALITY = 82   # WebP 质量 (1-100)
MAX_WIDTH = 1920    # 原图压缩后的最大宽度

# 支持的图片格式
SUPPORTED_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}


def load_data_json():
    """读取 data.json，返回 {chapter: [(filename, filepath)]}"""
    with open(ALBUM_DIR / "data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    chapters = {}
    for chapter, photos in data.items():
        photos_dir = PHOTOS_DIR / chapter
        if not photos_dir.exists():
            print(f"  ⚠️  照片目录不存在: {photos_dir}")
            continue
        chapter_files = []
        for photo_info in photos:
            filename = photo_info.get('file', '') if isinstance(photo_info, dict) else photo_info
            filepath = photos_dir / filename
            if filepath.exists():
                chapter_files.append((filename, filepath))
        chapters[chapter] = chapter_files
    return chapters


def compress_single(filepath: Path, chapter: str, filename: str):
    """压缩单张图片，返回 (thumb1200_size, thumb400_size, webp_size, original_size)"""
    try:
        original_size = filepath.stat().st_size
        
        # 跳过非图片文件
        if filepath.suffix.lower() not in SUPPORTED_EXTS:
            return None
        
        # 打开图片
        img = Image.open(filepath)
        
        # 转换为 RGB (去除 alpha 通道，适合 WebP)
        if img.mode in ('RGBA', 'LA', 'P'):
            # 用白色背景填充透明区域
            if img.mode == 'P':
                img = img.convert('RGBA')
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'RGBA':
                background.paste(img, mask=img.split()[3])
            elif img.mode in ('LA', 'L'):
                background.paste(img.convert('L'))
            else:
                background = img.convert('RGB')
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # 计算缩放到 MAX_WIDTH 后的尺寸
        orig_w, orig_h = img.size
        if orig_w > MAX_WIDTH:
            ratio = MAX_WIDTH / orig_w
            new_w = int(orig_w * ratio)
            new_h = int(orig_h * ratio)
            img_resized = img.resize((new_w, new_h), Image.LANCZOS)
        else:
            img_resized = img
        
        # 保存 WebP 压缩原图
        thumb_dir = OUTPUT_BASE / chapter
        thumb_dir.mkdir(parents=True, exist_ok=True)
        
        # WebP 文件
        webp_name = filename.rsplit('.', 1)[0] + '.webp'
        webp_path = thumb_dir / f"orig_{webp_name}"
        img_resized.save(webp_path, 'WEBP', quality=WEBP_QUALITY, optimize=True)
        webp_size = webp_path.stat().st_size
        
        # 缩略图 1200px
        thumb1200_dir = thumb_dir / "thumb1200"
        thumb1200_dir.mkdir(exist_ok=True)
        thumb1200_w = min(1200, img_resized.size[0])
        r1200 = thumb1200_w / img_resized.size[0]
        h1200 = int(img_resized.size[1] * r1200)
        img_1200 = img_resized.resize((thumb1200_w, h1200), Image.LANCZOS)
        thumb1200_path = thumb1200_dir / f"orig_{webp_name}"
        img_1200.save(thumb1200_path, 'WEBP', quality=85, optimize=True)
        thumb1200_size = thumb1200_path.stat().st_size
        
        # 缩略图 400px
        thumb400_dir = thumb_dir / "thumb400"
        thumb400_dir.mkdir(exist_ok=True)
        thumb400_w = min(400, img_resized.size[0])
        r400 = thumb400_w / img_resized.size[0]
        h400 = int(img_resized.size[1] * r400)
        img_400 = img_resized.resize((thumb400_w, h400), Image.LANCZOS)
        thumb400_path = thumb400_dir / f"orig_{webp_name}"
        img_400.save(thumb400_path, 'WEBP', quality=75, optimize=True)
        thumb400_size = thumb400_path.stat().st_size
        
        return {
            'original': original_size,
            'webp': webp_size,
            'thumb1200': thumb1200_size,
            'thumb400': thumb400_size,
            'ratio': (webp_size / original_size * 100) if original_size > 0 else 0
        }
    
    except Exception as e:
        return {'error': str(e)}


def main():
    parser = argparse.ArgumentParser(description="相册图片压缩工具")
    parser.add_argument('--first', type=int, help='只测试前 N 张照片')
    parser.add_argument('--apply', action='store_true', help='正式执行并保存（默认只预览）')
    args = parser.parse_args()
    
    chapters = load_data_json()
    total_photos = sum(len(files) for files in chapters.values())
    print(f"📷 共发现 {total_photos} 张照片，{len(chapters)} 个阶段")
    
    # 收集所有照片路径（保持顺序）
    all_photos = []
    for chapter in sorted(chapters.keys()):
        for filename, filepath in chapters[chapter]:
            all_photos.append((chapter, filename, filepath))
    
    if args.first:
        all_photos = all_photos[:args.first]
        print(f"🎯 测试模式：只压缩前 {args.first} 张")
    
    results = []
    total_original = 0
    total_webp = 0
    total_thumb1200 = 0
    total_thumb400 = 0
    
    print(f"\n{'='*80}")
    print(f"开始压缩...")
    print(f"{'='*80}\n")
    
    start_time = time.time()
    
    for i, (chapter, filename, filepath) in enumerate(all_photos, 1):
        result = compress_single(filepath, chapter, filename)
        
        if result is None:
            continue
        
        if 'error' in result:
            print(f"  ❌ [{i}/{len(all_photos)}] {chapter}/{filename}: {result['error']}")
            continue
        
        total_original += result['original']
        total_webp += result['webp']
        total_thumb1200 += result['thumb1200']
        total_thumb400 += result['thumb400']
        
        ratio = result['ratio']
        orig_mb = result['original'] / 1024 / 1024
        webp_mb = result['webp'] / 1024 / 1024
        t1200_mb = result['thumb1200'] / 1024 / 1024
        t400_mb = result['thumb400'] / 1024 / 1024
        
        status = "✅" if args.apply else "👀"
        print(f"  {status} [{i}/{len(all_photos)}] {chapter}/{filename}")
        print(f"       原图: {orig_mb:.2f} MB → WebP: {webp_mb:.2f} MB ({ratio:.0f}%)")
        print(f"       1200px: {t1200_mb:.2f} MB | 400px: {t400_mb:.2f} MB")
        
        results.append({
            'chapter': chapter,
            'filename': filename,
            'result': result
        })
    
    elapsed = time.time() - start_time
    
    print(f"\n{'='*80}")
    print(f"📊 统计报告")
    print(f"{'='*80}")
    print(f"  总耗时: {elapsed:.1f} 秒 ({len(all_photos)} 张)")
    print(f"\n  原图总计: {total_original / 1024 / 1024:.1f} MB")
    print(f"  WebP总计: {total_webp / 1024 / 1024:.1f} MB ({total_webp/total_original*100:.0f}%)")
    print(f"  1200px:   {total_thumb1200 / 1024 / 1024:.1f} MB")
    print(f"  400px:    {total_thumb400 / 1024 / 1024:.1f} MB")
    print(f"\n  单文件合计: {total_webp / 1024 / 1024 + total_thumb1200 / 1024 / 1024 + total_thumb400 / 1024 / 1024:.1f} MB")
    print(f"  压缩比: 原图 → 三档 = {total_original / 1024 / 1024:.1f} MB → {total_webp/1024/1024 + total_thumb1200/1024/1024 + total_thumb400/1024/1024:.1f} MB ({(1 - (total_webp+total_thumb1200+total_thumb400)/total_original)*100:.0f}% 减少)")
    
    if not args.apply:
        print(f"\n⚠️  预览模式！图片未保存。")
        print(f"   确认效果后运行: python {sys.argv[0]} --apply")
    
    # 保存报告
    report_path = ALBUM_DIR / "compress_report.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"压缩报告 (预览模式)\n")
        f.write(f"{'='*60}\n")
        f.write(f"总照片: {total_photos}\n")
        f.write(f"原图总计: {total_original / 1024 / 1024:.1f} MB\n")
        f.write(f"WebP总计: {total_webp / 1024 / 1024:.1f} MB\n")
        f.write(f"1200px缩略图: {total_thumb1200 / 1024 / 1024:.1f} MB\n")
        f.write(f"400px缩略图: {total_thumb400 / 1024 / 1024:.1f} MB\n")
        f.write(f"单文件合计: {total_webp/1024/1024 + total_thumb1200/1024/1024 + total_thumb400/1024/1024:.1f} MB\n")
    
    print(f"\n📄 报告已保存到: {report_path}")
    
    return results


if __name__ == '__main__':
    main()
