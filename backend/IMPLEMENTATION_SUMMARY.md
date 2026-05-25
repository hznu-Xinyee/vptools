# 视频文字区域自动检测功能 - 实现总结

## 📋 需求概述

在使用视频自动翻译的全屏擦除模式时，需要先通过阿里云OSS获取视频封面截图，然后使用豆包视觉API识别其中的文字区域，最后将识别的区域坐标传递给字幕擦除服务。

## ✅ 已完成的工作

### 1. OSS视频截图功能 (`app/services/oss_service.py`)

**新增方法：**

- `generate_video_snapshot_url(video_url, time_ms, format, width, height, mode)` 
  - 为已有的视频URL添加OSS截图参数
  - 支持公开和已签名的URL
  
- `generate_video_snapshot_url_signed(key, time_ms, format, width, height, mode, expires)`
  - 为私有bucket生成带签名的截图URL
  - 适用于需要权限控制的场景

**特点：**
- 使用阿里云OSS内置的视频截帧功能
- 无需下载视频，实时生成截图
- 支持自定义时间点、格式、分辨率

### 2. 豆包视觉识别服务 (`app/services/doubao_service.py`)

**新增服务类：** `DoubaoService`

**核心方法：**
- `detect_text_regions(image_url)` - 识别图片中的文字区域

**功能：**
- 调用豆包视觉API (doubao-vision-pro-32k模型)
- 识别图片中所有文字区域（字幕、标题、水印等）
- 返回归一化坐标（0.0-1.0）

**返回格式：**
```json
[
  {
    "top_left_x": 0.1,
    "top_left_y": 0.8,
    "bottom_right_x": 0.9,
    "bottom_right_y": 0.95
  }
]
```

### 3. 视频翻译服务集成 (`app/services/video_translation_service.py`)

**更新方法：** `submit_auto_translation()`

**新增逻辑：**
```python
# 当启用全屏擦除且不跳过字幕擦除时
if full_screen_erase and not skip_subtitle_erasure:
    # 1. 生成视频截图URL
    snapshot_url = oss_service.generate_video_snapshot_url(...)
    
    # 2. 检测文字区域
    text_regions = await doubao_service.detect_text_regions(snapshot_url)
    
    # 3. 将区域坐标添加到payload
    payload["erase_ratio_location"] = text_regions
```

**容错机制：**
- 检测失败时自动回退到默认全屏擦除
- 详细的日志记录每个步骤
- 不影响主流程的执行

### 4. 字幕擦除服务更新 (`app/services/volcengine_service.py`)

**更新方法：** `submit_subtitle_erase_task()`

**新增参数：**
- `erase_ratio_location: Optional[List[Dict[str, float]]]` - 文字区域坐标列表

**功能：**
- 支持传递多个擦除区域（最多20个）
- 与火山引擎字幕擦除API完全兼容

## 📁 新增文件

1. **`app/services/doubao_service.py`** - 豆包视觉识别服务
2. **`README_TEXT_DETECTION.md`** - 功能详细文档
3. **`test_text_region_detection.py`** - 测试脚本
4. **`examples_text_detection.py`** - 使用示例代码

## 🔄 工作流程

```
用户提交自动翻译任务 (full_screen_erase=True)
         ↓
生成视频第1秒的截图URL (OSS)
         ↓
调用豆包视觉API识别文字区域
         ↓
将区域坐标添加到 erase_ratio_location
         ↓
提交到字幕擦除服务 (VolcEngine)
         ↓
执行精准的文字区域擦除
```

## 🚀 使用方法

### 方式1: 自动模式（推荐）

提交自动翻译任务时，系统会自动检测文字区域：

```bash
curl -X POST 'http://your-api/video-translation/submit-auto' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -d '{
    "original_filename": "video.mp4",
    "oss_key": "subtitle_erase/123/video.mp4",
    "file_url": "https://your-bucket.oss-cn-shanghai.aliyuncs.com/video.mp4",
    "target_languages": ["en", "ja"],
    "full_screen_erase": true,
    "skip_subtitle_erasure": false
  }'
```

### 方式2: 手动调用

```python
from app.services.oss_service import oss_service
from app.services.doubao_service import doubao_service

# 生成截图URL
snapshot_url = oss_service.generate_video_snapshot_url(
    video_url="https://your-video-url.mp4",
    time_ms=1000
)

# 检测文字区域
regions = await doubao_service.detect_text_regions(snapshot_url)
print(f"检测到 {len(regions)} 个文字区域")
```

## 🧪 测试

运行测试脚本：

```bash
cd /opt/VP/backend
python3 test_text_region_detection.py
```

测试内容：
1. ✓ OSS视频截图URL生成
2. ✓ 豆包视觉API文字区域识别
3. ✓ 参数格式验证

## 📊 日志示例

```
[自动翻译] 任务 123 启用全屏擦除，开始检测文字区域
[自动翻译] 生成视频截图URL: https://...?x-oss-process=video/snapshot,t_1000,f_jpg,w_800,h_0,m_fast
[豆包视觉] 开始检测文字区域，图片URL: https://...
[豆包视觉] API响应: {...}
[豆包视觉] 检测到 2 个文字区域
[自动翻译] 提交任务，erase_ratio_location=[
  {"top_left_x": 0.1, "top_left_y": 0.8, "bottom_right_x": 0.9, "bottom_right_y": 0.95},
  {"top_left_x": 0.05, "top_left_y": 0.05, "bottom_right_x": 0.3, "bottom_right_y": 0.15}
]
```

## ⚙️ 配置要求

确保 `.env` 文件中配置了以下环境变量：

```env
# OSS配置
OSS_ACCESS_KEY_ID=your_access_key_id
OSS_ACCESS_KEY_SECRET=your_access_key_secret
OSS_ENDPOINT=https://oss-cn-shanghai.aliyuncs.com
OSS_BUCKET_NAME=your_bucket_name

# 豆包/火山引擎配置
VOLCENGINE_API_KEY=your_volcengine_api_key
```

## 🎯 技术亮点

1. **零下载** - 使用OSS URL参数实时生成截图，无需下载视频
2. **智能识别** - 豆包视觉API自动识别所有文字区域
3. **自动容错** - 检测失败时自动回退到默认全屏擦除
4. **异步处理** - 不阻塞主流程，提高性能
5. **详细日志** - 每个步骤都有日志记录，便于调试

## 📈 性能优化

- OSS截图使用 `fast` 模式，速度更快
- 截图宽度设置为800px，减少数据传输
- 豆包API调用超时60秒，避免长时间等待
- 异步处理，不影响其他任务

## 🔧 故障排查

### 问题1: 检测不到文字区域

**原因：** 视频第1秒可能没有文字

**解决：** 
- 查看日志中的截图URL，手动访问确认
- 调整截图时间点（修改代码中的 `time_ms` 参数）

### 问题2: 豆包API调用失败

**原因：** API Key无效或账户未开通服务

**解决：**
- 检查 `VOLCENGINE_API_KEY` 配置
- 确认账户已开通豆包视觉服务
- 查看日志中的详细错误信息

### 问题3: 擦除效果不理想

**原因：** 检测的区域不准确

**解决：**
- 查看日志中检测到的区域坐标
- 调整豆包API的提示词（在 `doubao_service.py` 中）
- 考虑使用多帧检测提高准确率

## 🔮 未来改进方向

1. **多帧检测** - 检测多个时间点，提高准确率
2. **区域优化** - 自动合并相邻区域，减少擦除次数
3. **可视化预览** - 在前端显示检测到的区域
4. **自定义提示词** - 允许用户自定义豆包API的提示词
5. **缓存机制** - 缓存检测结果，避免重复调用

## 📞 技术支持

如有问题，请查看：
- 详细文档：`README_TEXT_DETECTION.md`
- 使用示例：`examples_text_detection.py`
- 测试脚本：`test_text_region_detection.py`

## ✨ 总结

本次实现完整地集成了视频文字区域自动检测功能，从视频截图、文字识别到字幕擦除形成了完整的自动化流程。系统具有良好的容错机制和详细的日志记录，便于调试和维护。

**核心优势：**
- 🚀 全自动化 - 用户无需手动操作
- 🎯 精准识别 - 豆包视觉API准确识别文字区域
- 🛡️ 容错机制 - 失败时自动回退，不影响主流程
- 📝 详细日志 - 每个步骤都有记录，便于排查问题
