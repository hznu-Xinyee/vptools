"""
Test script for MediaKit audio separation
"""
import asyncio
import sys
from app.services.mediakit_service import mediakit_service
from app.services.oss_service import oss_service

async def test_audio_separation():
    """Test audio separation using MediaKit"""
    
    # Test audio file OSS key
    audio_oss_key = "audio_extraction/63_original.wav"
    
    # Generate presigned URL for MediaKit access
    test_audio_url = oss_service.generate_presigned_url(audio_oss_key, expires=3600, method='GET')
    
    print(f"Testing audio separation with input: {test_audio_url}")
    
    # Submit audio separation task
    print("Submitting audio separation task to MediaKit...")
    demix_job_id = await mediakit_service.submit_separate_voice_task(audio_url=test_audio_url)
    
    if not demix_job_id:
        print("ERROR: Failed to submit audio separation task")
        return False
    
    print(f"SUCCESS: Task submitted with ID: {demix_job_id}")
    
    # Wait for job completion
    print("Waiting for job completion...")
    max_attempts = 60
    for attempt in range(max_attempts):
        await asyncio.sleep(10)
        demix_status = await mediakit_service.get_task_status(demix_job_id)
        status = demix_status.get('status') if demix_status else 'None'
        print(f"Status check {attempt + 1}/{max_attempts}: {status}")
        
        if mediakit_service.is_task_completed(demix_status):
            print("SUCCESS: Audio separation completed successfully!")
            print(f"Result: {demix_status.get('result')}")
            
            result = demix_status.get("result", {})
            voice_audio_url = result.get("voice_audio_url")
            background_audio_url = result.get("background_audio_url")
            
            print(f"\nVoice audio URL: {voice_audio_url}")
            print(f"Background audio URL: {background_audio_url}")
            
            return True
        
        elif mediakit_service.is_task_failed(demix_status):
            print(f"ERROR: Job failed with status: {demix_status}")
            return False
    
    print("ERROR: Job timed out")
    return False

if __name__ == "__main__":
    try:
        result = asyncio.run(test_audio_separation())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
