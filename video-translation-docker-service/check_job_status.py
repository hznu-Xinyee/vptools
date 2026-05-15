#!/usr/bin/env python3
import json
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_ice20201109.client import Client as ICEClient
from alibabacloud_ice20201109 import models as ice_models
from app.config import settings

JOB_ID = "82ce8a8a7f6d4726909b5e77c0cade4c"

def create_ice_client():
    """Create ICE client"""
    config = open_api_models.Config(
        access_key_id=settings.ALIYUN_ICE_ACCESS_KEY_ID,
        access_key_secret=settings.ALIYUN_ICE_ACCESS_KEY_SECRET
    )
    config.endpoint = settings.ALIYUN_ICE_ENDPOINT
    config.region_id = settings.ALIYUN_ICE_REGION_ID
    return ICEClient(config)

def check_job_status():
    """Check ICE job status"""
    client = create_ice_client()
    
    try:
        request = ice_models.GetMediaProducingJobRequest(
            job_id=JOB_ID
        )
        
        response = client.get_media_producing_job(request)
        job_info = response.body.media_producing_job
        
        print("=" * 50)
        print("任务状态:")
        print("=" * 50)
        print(f"Job ID: {job_info.job_id}")
        print(f"Status: {job_info.status}")
        print(f"Code: {job_info.code}")
        print(f"Message: {job_info.message}")
        print(f"Media ID: {job_info.media_id}")
        print(f"Media URL: {job_info.media_url}")
        print("=" * 50)
        
        if job_info.status == "Failed":
            print("\n任务失败详情:")
            print(f"错误码: {job_info.code}")
            print(f"错误信息: {job_info.message}")
            
            # Print timeline for debugging
            if job_info.timeline:
                print("\nTimeline:")
                print(json.dumps(json.loads(job_info.timeline), indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    check_job_status()
