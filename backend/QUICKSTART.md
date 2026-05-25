# 视频文字区域自动检测 - 快速开始指南

## 🎯 功能说明

在视频自动翻译中使用全屏擦除模式时，系统会自动：
1. 从视频截取封面图
2. 使用豆包AI识别文字区域
3. 精准擦除识别到的文字区域

## 🚀 快速使用

### 前端调用示例

```javascript
// 提交自动翻译任务
const response = await fetch('/video-translation/submit-auto', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_TOKEN'
  },
  body: JSON.stringify({
    original_filename: 'my_video.mp4',
    oss_key: 'subtitle_erase/123/video.mp4',
    file_url: 'https://your-bucket.oss-cn-shanghai.aliyuncs.com/video.mp4',
    target_languages: ['en', 'ja', 'ko'],
    full_screen_erase: true,        // 启用全屏擦除
    skip_subtitle_erasure: false    // 不跳过字幕擦除
  })
});

const result = await response.json();
console.log('任务ID:', result.task_id);
// 系统会自动检测文字区域并执行精准擦除
```

### 后端调用示例

```python
from app.services.video_translation_service import video_translation_service

# 提交自动翻译任务（会自动检测文字区域）
result = await video_translation_service.submit_auto_translation(
    task_id=123,
    oss_key='subtitle_erase/123/video.mp4',
    file_url='https://your-bucket.oss-cn-shanghai.aliyuncs.com/video.mp4',
    original_filename='video.mp4',
    target_languages=['en', 'ja'],
    full_screen_erase=True,
    skip_subtitle_erasure=False
)
```

## 📋 修改的文件

### 1. `app/services/oss_service.py`
- ✅ 新增 `generate_video_snapshot_url()` - 生成视频截图URL
- ✅ 新增 `generate_video_snapshot_url_signed()` - 生成带签名的截图URL

### 2. `app/services/doubao_service.py` (新文件)
- ✅ 新增 `DoubaoService` 类
- ✅ 新增 `detect_text_regions()` - 检测文字区域

### 3. `app/services/video_translation_service.py`
- ✅ 更新 `submit_auto_translation()` - 集成文字区域检测
- ✅ 添加自动检测逻辑和容错机制

### 4. `app/services/volcengine_service.py`
- ✅ 更新 `submit_subtitle_erase_task()` - 支持 `erase_ratio_location` 参数

## 🧪 测试

```bash
cd /opt/VP/backend
python3 test_text_region_detection.py
```

## 📊 查看日志

```bash
tail -f /opt/VP/backend/backend.log | grep -E "自动翻译|豆包视觉"
```

日志示例：
```
[自动翻译] 任务 123 启用全屏擦除，开始检测文字区域
[豆包视觉] 检测到 2 个文字区域
[自动翻译] 提交任务，erase_ratio_location=[...]
```

## ⚙️ 配置检查

确保 `.env` 文件包含：

```env
# OSS配置
OSS_ACCESS_KEY_ID=your_key
OSS_ACCESS_KEY_SECRET=your_secret
OSS_ENDPOINT=https://oss-cn-shanghai.aliyuncs.com
OSS_BUCKET_NAME=your_bucket

# 豆包配置
VOLCENGINE_API_KEY=your_volcengine_key
```

## 🔍 工作原理

```
用户提交任务
    ↓
检查: full_screen_erase=True && skip_subtitle_erasure=False
    ↓
生成视频截图URL (OSS)
    ↓
调用豆包识别文字区域
    ↓
将区域坐标添加到请求
    ↓
提交到字幕擦除服务
```

## 💡 关键参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `full_screen_erase` | 启用全屏擦除模式 | `false` |
| `skip_subtitle_erasure` | 跳过字幕擦除 | `false` |
| `time_ms` | 截图时间点（毫秒） | `1000` (第1秒) |
| `width` | 截图宽度 | `800` |
| `mode` | 截图模式 | `fast` |

## 🛡️ 容错机制

- ✅ 检测失败时自动回退到默认全屏擦除
- ✅ 详细的日志记录每个步骤
- ✅ 不影响主流程的执行
- ✅ 超时保护（60秒）

## 📚 更多文档

- 详细文档：`README_TEXT_DETECTION.md`
- 实现总结：`IMPLEMENTATION_SUMMARY.md`
- 使用示例：`examples_text_detection.py`

## ❓ 常见问题

**Q: 检测不到文字区域怎么办？**
A: 系统会自动回退到默认全屏擦除，不影响使用。

**Q: 如何调整截图时间点？**
A: 修改 `video_translation_service.py` 中的 `time_ms` 参数。

**Q: 支持哪些视频格式？**
A: 支持 mp4, flv, ts, avi, mov, wmv, mkv 等主流格式。

**Q: 检测准确率如何？**
A: 使用豆包视觉Pro模型，准确率较高。如需提高，可调整提示词。

## ✅ 验证清单

- [ ] 环境变量配置正确
- [ ] 运行测试脚本通过
- [ ] 查看日志确认功能正常
- [ ] 提交测试任务验证效果

## 🎉 完成！

现在你可以使用视频文字区域自动检测功能了！系统会自动识别并精准擦除视频中的文字区域。
