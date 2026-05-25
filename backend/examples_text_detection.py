"""
视频文字区域检测功能使用示例

展示如何在不同场景下使用文字区域检测功能
"""

# ============================================
# 示例1: 自动检测模式（推荐）
# ============================================
# 在提交自动翻译任务时，启用 full_screen_erase=True
# 系统会自动检测文字区域并传递给字幕擦除服务

import httpx
import asyncio

async def example_auto_translation_with_detection():
    """提交自动翻译任务，自动检测文字区域"""

    payload = {
        "original_filename": "my_video.mp4",
        "oss_key": "subtitle_erase/123/20260525_abc123.mp4",
        "file_url": "https://your-bucket.oss-cn-shanghai.aliyuncs.com/video.mp4",
        "target_languages": ["en", "ja", "ko"],
        "full_screen_erase": True,  # 启用全屏擦除
        "skip_subtitle_erasure": False,  # 不跳过字幕擦除
        "subtitle_params": {
            "font": "Alibaba PuHuiTi",
            "font_size": 80,
            "font_color": "#ffffff"
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://your-api/video-translation/submit-auto",
            json=payload,
            headers={"Authorization": "Bearer YOUR_TOKEN"}
        )
        result = response.json()
        print(f"任务已提交，task_id: {result['task_id']}")
        print("系统会自动检测文字区域并执行精准擦除")


# ============================================
# 示例2: 手动调用检测API
# ============================================
# 如果需要单独使用文字区域检测功能

from app.services.oss_service import oss_service
from app.services.doubao_service import doubao_service

async def example_manual_detection():
    """手动检测视频中的文字区域"""

    video_url = "https://your-bucket.oss-cn-shanghai.aliyuncs.com/video.mp4"

    # 步骤1: 生成视频截图URL
    snapshot_url = oss_service.generate_video_snapshot_url(
        video_url=video_url,
        time_ms=1000,  # 截取第1秒
        format='jpg',
        width=800,
        height=0,
        mode='fast'
    )
    print(f"截图URL: {snapshot_url}")

    # 步骤2: 检测文字区域
    regions = await doubao_service.detect_text_regions(snapshot_url)
    print(f"检测到 {len(regions)} 个文字区域:")
    for i, region in enumerate(regions, 1):
        print(f"区域 {i}: {region}")

    return regions


# ============================================
# 示例3: 自定义截图时间点
# ============================================
# 如果视频开头没有文字，可以指定其他时间点

async def example_custom_snapshot_time():
    """使用自定义时间点截图"""

    video_url = "https://your-bucket.oss-cn-shanghai.aliyuncs.com/video.mp4"

    # 截取第5秒的画面
    snapshot_url = oss_service.generate_video_snapshot_url(
        video_url=video_url,
        time_ms=5000,  # 5秒 = 5000毫秒
        format='jpg',
        width=1280,  # 更高的分辨率
        height=0,
        mode='exact'  # 精确模式
    )

    regions = await doubao_service.detect_text_regions(snapshot_url)
    return regions


# ============================================
# 示例4: 私有Bucket的截图
# ============================================
# 如果视频存储在私有Bucket中

async def example_private_bucket():
    """为私有Bucket生成带签名的截图URL"""

    oss_key = "subtitle_erase/123/video.mp4"

    # 生成带签名的截图URL
    snapshot_url = oss_service.generate_video_snapshot_url_signed(
        key=oss_key,
        time_ms=1000,
        format='jpg',
        width=800,
        height=0,
        mode='fast',
        expires=3600  # URL有效期1小时
    )

    regions = await doubao_service.detect_text_regions(snapshot_url)
    return regions


# ============================================
# 示例5: 直接调用字幕擦除API（带区域检测）
# ============================================
# 如果只需要字幕擦除功能

from app.services.volcengine_service import volcengine_service

async def example_subtitle_erase_with_regions():
    """提交字幕擦除任务，指定文字区域"""

    video_url = "https://your-bucket.oss-cn-shanghai.aliyuncs.com/video.mp4"

    # 先检测文字区域
    snapshot_url = oss_service.generate_video_snapshot_url(video_url, time_ms=1000)
    regions = await doubao_service.detect_text_regions(snapshot_url)

    # 提交字幕擦除任务
    result = await volcengine_service.submit_subtitle_erase_task(
        video_url=video_url,
        mode="Text",  # 擦除所有文字
        erase_ratio_location=regions  # 传入检测到的区域
    )

    task_id = result.get('task_id')
    print(f"字幕擦除任务已提交，task_id: {task_id}")

    # 轮询任务状态
    while True:
        status = await volcengine_service.get_task_status(task_id)
        if volcengine_service.is_task_completed(status):
            print(f"任务完成！结果视频: {status['result']['video_url']}")
            break
        await asyncio.sleep(5)


# ============================================
# 示例6: 错误处理
# ============================================
# 处理检测失败的情况

async def example_with_error_handling():
    """带错误处理的文字区域检测"""

    video_url = "https://your-bucket.oss-cn-shanghai.aliyuncs.com/video.mp4"

    try:
        # 生成截图URL
        snapshot_url = oss_service.generate_video_snapshot_url(video_url, time_ms=1000)

        # 检测文字区域
        regions = await doubao_service.detect_text_regions(snapshot_url)

        if not regions:
            print("未检测到文字区域，使用默认全屏擦除")
            regions = [{
                "top_left_x": 0.0,
                "top_left_y": 0.0,
                "bottom_right_x": 1.0,
                "bottom_right_y": 1.0
            }]

        return regions

    except Exception as e:
        print(f"检测失败: {str(e)}")
        print("回退到默认全屏擦除")
        return [{
            "top_left_x": 0.0,
            "top_left_y": 0.0,
            "bottom_right_x": 1.0,
            "bottom_right_y": 1.0
        }]


# ============================================
# 运行示例
# ============================================

if __name__ == "__main__":
    # 运行自动翻译示例
    # asyncio.run(example_auto_translation_with_detection())

    # 运行手动检测示例
    # asyncio.run(example_manual_detection())

    # 运行自定义时间点示例
    # asyncio.run(example_custom_snapshot_time())

    # 运行私有Bucket示例
    # asyncio.run(example_private_bucket())

    # 运行字幕擦除示例
    # asyncio.run(example_subtitle_erase_with_regions())

    # 运行错误处理示例
    asyncio.run(example_with_error_handling())
