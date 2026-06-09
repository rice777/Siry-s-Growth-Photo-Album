# 相册加速方案总结

## 现状
- 相册托管在 GitHub Pages: https://rice777.github.io/Siry-s-Growth-Photo-Album/
- CDN: jsDelivr (国内访问速度约 40MB/s，已验证可行)
- 照片总计: 201 张，共 538.6 MB
- 每张照片平均 2.7 MB，最大 7.8 MB

## 已实施的优化：图片压缩

### 压缩策略
使用 Pillow 将 JPG 转为 WebP，并生成三档尺寸：
| 规格 | 宽度 | 质量 | 用途 | 总大小 |
|------|------|------|------|--------|
| 原图 WebP | 1920px | 82 | 灯箱全屏查看 | 162.4 MB |
| thumb1200 | 1200px | 85 | 列表页中等预览 | 58.2 MB |
| thumb400 | 400px | 75 | 列表页快速预览 | 7.0 MB |

### 压缩效果
- 原图 538.6 MB → 三档合计 227.7 MB (减少 58%)
- **首次加载仅需 400px: 7.0 MB (减少 98.7%)**

### 目录结构
```
compressed/
├── 0-1岁/
│   ├── orig_文件名.webp          # 原图压缩
│   ├── thumb1200/orig_文件名.webp  # 1200px
│   └── thumb400/orig_文件名.webp   # 400px
├── 1-2岁/
│   ├── orig_文件名.webp
│   ├── thumb1200/orig_文件名.webp
│   └── thumb400/orig_文件名.webp
└── ...
```

## 待实施的优化：三轨加载

### 加载策略
1. 列表页: 加载 400px 缩略图 (7 MB 总计)
2. 点击卡片: 预加载 1200px 缩略图用于灯箱
3. 灯箱内长按/双击: 加载原图查看细节

### 实现方式
- `PHOTOS_PATH` 指向 `compressed/` 目录
- 根据图片类型选择不同 URL:
  - 列表页: `compressed/{chapter}/thumb400/orig_{name}.webp`
  - 灯箱: `compressed/{chapter}/orig_{name}.webp`

## 云存储方案对比

### 方案 A: 又拍云 (推荐)
- 免费额度: 存储 10GB + 流量 10GB/月
- 优势: 国内 CDN，速度快，免备案
- 劣势: 需要实名认证激活
- 配置:
  1. 注册 https://www.upyun.com/
  2. 创建存储桶 (如 `siry-album`)
  3. 配置 CDN 加速域名
  4. 使用 CLI 上传压缩后的图片
  5. 开启图片处理 (自动缩略图/WebP)

### 方案 B: 腾讯云 COS
- 免费额度: 存储 50GB + 流量 10GB/月
- 优势: 流量更大，自动获得 myqcloud.com 域名
- 劣势: 需要备案
- 配置:
  1. 注册腾讯云
  2. 创建 COS 存储桶
  3. 配置 CDN 加速
  4. 使用 COSBrowser 或 CLI 上传

### 方案 C: 保持 jsDelivr
- 当前方案，国内访问速度约 40MB/s
- 无额外成本
- 依赖 jsDelivr 在中国的服务稳定性

## 下一步计划
1. ✅ 图片压缩完成
2. ⏳ 修改 index.html 使用压缩图片
3. ⏳ 测试加载效果
4. ⏳ 评估是否需要云存储方案
