# 视频文字区域自动检测功能

## 功能概述

在使用视频自动翻译的全屏擦除模式时，系统会自动：
1. 从视频中截取封面图（第1秒）
2. 使用豆包视觉API识别图片中的文字区域
3. 将识别的区域坐标传递给字幕擦除服务
4. 实现精准的文字区域擦除

## 技术实现

### 1. OSS视频截图 (`app/services/oss_service.py`)

新增方法：
- `generate_video_snapshot_url()` - 为视频URL添加OSS截图参数
- `generate_video_snapshot_url_signed()` - 为私有bucket生成带签名的截图URL

使用阿里云OSS的视频截帧功能，通过URL参数实时生成截图，无需下载视频。

**示例：**
```python
from app.services.oss_service import oss_service

# 生成视频第1秒的截图URL
snapshot_url = oss_service.generate_video_snapshot_url(
    video_url="https://your-bucket.oss-cn-shanghai.aliyuncs.com/video.mp4",
    time_ms=1000,      # 截取第1秒
    format='jpg',      # 图片格式
    width=800,         # 宽度
    height=0,          # 高度自动
    mode='fast'        # 快速模式
)
```

### 2. 豆包视觉识别 (`app/services/doubao_service.py`)

新增服务类 `DoubaoService`，提供文字区域检测功能。

**方法：**
- `detect_text_regions(image_url)` - 识别图片中的文字区域

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

坐标使用归一化值（0.0-1.0），其中(0,0)是左上角，(1,1)是右下角。

### 3. 视频翻译服务集成 (`app/services/video_translation_service.py`)

在 `submit_auto_translation()` 方法中自动执行文字区域检测：

**触发条件：**
- `full_screen_erase=True`
- `skip_subtitle_erasure=False`

**处理流程：**
```
1. 生成视频截图URL
   ↓
2. 调用豆包识别文字区域
   ↓
3. 将区域坐标添加到 erase_ratio_location 参数
   ↓
4. 提交到字幕擦除服务
```

**容错机制：**
- 如果检测失败，自动回退到默认全屏擦除
- 所有步骤都有详细的日志记录

### 4. 字幕擦除服务更新 (`app/services/volcengine_service.py`)

更新 `submit_subtitle_erase_task()` 方法，支持 `erase_ratio_location` 参数。

## API使用示例

### 提交自动翻译任务

```bash
curl -X POST 'http://your-api/video-translation/submit-auto' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -d '{
    "original_filename": "test_video.mp4",
    "oss_key": "subtitle_erase/123/video.mp4",
    "file_url": "https://your-bucket.oss-cn-shanghai.aliyuncs.com/video.mp4",
    "target_languages": ["en", "ja"],
    "full_screen_erase": true,
    "skip_subtitle_erasure": false
  }'
```

系统会自动：
1. 检测视频中的文字区域
2. 将检测结果传递给字幕擦除服务
3. 执行精准的文字擦除

### 查看日志

在后端日志中可以看到详细的处理过程：

```
[自动翻译] 任务 123 启用全屏擦除，开始检测文字区域
[自动翻译] 生成视频截图URL: https://...?x-oss-process=video/snapshot,t_1000,f_jpg,w_800,h_0,m_fast
[豆包视觉] 开始检测文字区域，图片URL: https://...
[豆包视觉] 检测到 2 个文字区域
[自动翻译] 提交任务，erase_ratio_location=[...]
```

## 测试

运行测试脚本验证功能：

```bash
cd /opt/VP/backend
python3 test_text_region_detection.py
```

测试脚本会：
1. 测试OSS视频截图URL生成
2. 测试豆包视觉API文字区域识别
3. 验证参数格式是否正确

## 配置要求

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

## 注意事项

1. **豆包视觉API调用**：需要有效的火山引擎API Key，并且账户需要开通豆包视觉服务
2. **OSS截图功能**：需要OSS bucket开启了视频处理功能
3. **超时设置**：豆包视觉API调用超时时间为60秒
4. **容错处理**：如果文字区域检测失败，系统会自动使用默认的全屏擦除
5. **坐标格式**：所有坐标都是归一化值（0.0-1.0），与视频分辨率无关

## 性能优化

- OSS截图是实时生成的，不需要下载视频文件
- 截图使用 `fast` 模式，速度更快
- 截图宽度设置为800px，减少数据传输量
- 豆包API调用是异步的，不会阻塞主流程

## 故障排查

### 问题1：检测不到文字区域

**可能原因：**
- 视频第1秒没有文字
- 图片质量太低
- 豆包API调用失败

**解决方案：**
- 检查视频内容
- 调整截图时间点（修改 `time_ms` 参数）
- 查看日志中的错误信息

### 问题2：擦除效果不理想

**可能原因：**
- 检测的区域不准确
- 文字区域太小或太大

**解决方案：**
- 查看日志中检测到的区域坐标
- 调整豆包API的提示词
- 手动指定擦除区域

## 未来改进

1. 支持多帧检测，提高准确率
2. 支持自定义截图时间点
3. 支持区域合并和优化
4. 添加区域检测结果的可视化预览
