"""
Test script for ICE audio separation (MusicDemix)
"""
import asyncio
import sys
from app.services.ice_service import ice_service
from app.services.oss_service import oss_service
from app.core.config import settings

async def test_audio_separation():
    """Test audio separation using ICE MusicDemix"""
    
    # Test audio file URL (you can replace with your own test audio URL)
    test_audio_url = "https://montage-oss.oss-cn-shanghai.aliyuncs.com/audio_extraction/63_original.wav"
    
    print(f"Testing audio separation with input: {test_audio_url}")
    
    # Generate output URLs
    task_id = "test_001"
    background_oss_key = f"audio_separation/{task_id}_background.wav"
    vocal_oss_key = f"audio_separation/{task_id}_vocal.wav"
    background_url = f"oss://{settings.OSS_BUCKET_NAME}/{background_oss_key}"
    vocal_url = f"oss://{settings.OSS_BUCKET_NAME}/{vocal_oss_key}"
    
    print(f"Background output URL: {background_url}")
    print(f"Vocal output URL: {vocal_url}")
    
    # Submit MusicDemix job
    print("Submitting MusicDemix job to ICE...")
    demix_job_id = await ice_service.submit_music_demix_job(
        input_audio_url=test_audio_url,
        output_background_url=background_url,
        output_vocal_url=vocal_url
    )
    
    if not demix_job_id:
        print("ERROR: Failed to submit MusicDemix job")
        return False
    
    print(f"SUCCESS: Job submitted with ID: {demix_job_id}")
    
    # Wait for job completion
    print("Waiting for job completion...")
    max_attempts = 60
    for attempt in range(max_attempts):
        await asyncio.sleep(10)
        demix_status = await ice_service.get_i_production_job(demix_job_id)
        status = demix_status.get('status') if demix_status else 'None'
        print(f"Status check {attempt + 1}/{max_attempts}: {status}")
        
        if demix_status and demix_status.get("status") == "Finished":
            print("SUCCESS: Audio separation completed successfully!")
            print(f"Result: {demix_status.get('result')}")
            
            # Check if output files exist in OSS
            print("\nChecking output files in OSS...")
            background_exists = oss_service.file_exists(background_oss_key)
            vocal_exists = oss_service.file_exists(vocal_oss_key)
            print(f"Background audio exists: {background_exists}")
            print(f"Vocal audio exists: {vocal_exists}")
            
            if background_exists:
                background_url = oss_service.get_file_url(background_oss_key)
                print(f"Background audio URL: {background_url}")
            
            return True
        
        elif demix_status and demix_status.get("status") == "Failed":
            print(f"ERROR: Job failed with result: {demix_status.get('result')}")
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
