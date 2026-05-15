#!/usr/bin/env python3
import json
import asyncio
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_ice20201109.client import Client as ICEClient
from alibabacloud_ice20201109 import models as ice_models
from app.config import settings

# Test media ID
MEDIA_ID = "22fe3fa04c9271f184c1f6f6c7496302"

def manual_wrap_text(text, max_chars=18):
    """Manually wrap text at spaces for English, by character for Chinese"""
    # Check if text contains English characters
    if any(c.isalpha() and ord(c) < 128 for c in text):
        # English: wrap at spaces
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            if not current_line:
                current_line = word
            elif len(current_line) + 1 + len(word) <= max_chars:
                current_line += " " + word
            else:
                lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return "\n".join(lines)
    else:
        # Chinese: wrap by character count
        if len(text) <= max_chars:
            return text
        
        lines = []
        for i in range(0, len(text), max_chars):
            lines.append(text[i:i + max_chars])
        
        return "\n".join(lines)

def create_ice_client():
    """Create ICE client"""
    config = open_api_models.Config(
        access_key_id=settings.ALIYUN_ICE_ACCESS_KEY_ID,
        access_key_secret=settings.ALIYUN_ICE_ACCESS_KEY_SECRET
    )
    config.endpoint = settings.ALIYUN_ICE_ENDPOINT
    config.region_id = settings.ALIYUN_ICE_REGION_ID
    return ICEClient(config)

def test_render():
    """Test ICE rendering with subtitle at 75% and video muted"""
    client = create_ice_client()
    
    # Test text with manual wrapping
    test_text = "This is a test subtitle that should be displayed at 75% from the top position with manual line wrapping"
    wrapped_text = manual_wrap_text(test_text, max_chars=25)
    print(f"原始文本: {test_text}")
    print(f"手动换行后: {wrapped_text}")
    print()
    
    # Create timeline with:
    # 1. Video track with Gain=0 to mute
    # 2. Subtitle at Y=0.75 (75% from top)
    # 3. Manual line wrapping (no AdaptMode)
    timeline = {
        "VideoTracks": [
            {
                "MainTrack": True,
                "VideoTrackClips": [
                    {
                        "MediaId": MEDIA_ID,
                        "Effects": [
                            {
                                "Type": "Volume",
                                "Gain": 0
                            }
                        ]
                    }
                ]
            }
        ],
        "SubtitleTracks": [
            {
                "SubtitleTrackClips": [
                    {
                        "Type": "Text",
                        "Content": wrapped_text,
                        "TimelineIn": 0,
                        "TimelineOut": 10,
                        "Alignment": "TopCenter",
                        "FontSize": 84,
                        "FontColor": "#ffffff",
                        "Outline": 2,
                        "OutlineColour": "#000000",
                        "Y": 0.75
                    }
                ]
            }
        ]
    }
    
    print("=" * 50)
    print("ICE Timeline 配置:")
    print("=" * 50)
    print(json.dumps(timeline, indent=2, ensure_ascii=False))
    print("=" * 50)
    
    # Output configuration
    output_key = f"{settings.ALIYUN_ICE_OUTPUT_PATH}/test_ice_render.mp4"
    output_url = f"https://montage-oss.oss-cn-shanghai.aliyuncs.com/{output_key}"
    
    print(f"\n输出URL: {output_url}")
    
    try:
        # Submit rendering job
        request = ice_models.SubmitMediaProducingJobRequest(
            timeline=json.dumps(timeline, ensure_ascii=False),
            output_media_target="oss-object",
            output_media_config=json.dumps({"MediaURL": output_url}, ensure_ascii=False),
            source="OpenAPI"
        )
        
        print("\n正在提交ICE渲染任务...")
        response = client.submit_media_producing_job(request)
        
        print("\n" + "=" * 50)
        print("任务已提交成功!")
        print("=" * 50)
        print(f"Job ID: {response.body.job_id}")
        print(f"Project ID: {response.body.project_id}")
        print(f"Media ID: {response.body.media_id}")
        print("=" * 50)
        print(f"\n输出视频将保存到: {output_url}")
        print("\n请稍等几分钟后访问上述URL查看渲染结果")
        print("\n验证要点:")
        print("1. 视频应该没有声音（已静音）")
        print("2. 字幕应该在距离顶部75%的位置显示")
        print("3. 字幕应该手动换行，每行不超过22个字符，只在空格处换行")
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    print("ICE 渲染测试脚本")
    print(f"测试视频 Media ID: {MEDIA_ID}")
    print()
    
    success = test_render()
    sys.exit(0 if success else 1)
