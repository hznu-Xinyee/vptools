import os
import subprocess
import tempfile
import logging
from typing import BinaryIO
from app.core.config import settings

logger = logging.getLogger(__name__)


class AudioConversionService:
    async def convert_to_audio(self, input_file: BinaryIO, input_filename: str) -> bytes:
        """Convert video/audio file to audio (mp3 format) and return binary data"""
        try:
            # Create temporary file for input
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(input_filename)[1]) as input_temp:
                input_temp.write(input_file.read())
                input_temp_path = input_temp.name
            
            # Create temporary file for output
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as output_temp:
                output_temp_path = output_temp.name
            
            # Use ffmpeg to convert to audio
            cmd = [
                "ffmpeg",
                "-i", input_temp_path,
                "-vn",
                "-acodec", "libmp3lame",
                "-y",
                output_temp_path
            ]
            
            logger.info(f"Converting file: {input_filename} to audio")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                raise Exception(f"Audio conversion failed: {result.stderr}")
            
            # Read the converted audio as binary
            with open(output_temp_path, 'rb') as audio_file:
                audio_data = audio_file.read()
            
            logger.info(f"Audio conversion successful, size: {len(audio_data)} bytes")
            
            # Clean up temporary files
            os.unlink(input_temp_path)
            os.unlink(output_temp_path)
            
            return audio_data
        except Exception as e:
            logger.error(f"Audio conversion error: {str(e)}")
            raise
    
    async def convert_oss_file_to_audio(self, input_oss_key: str) -> bytes:
        """Convert OSS file to audio and return binary data"""
        try:
            from app.services.oss_service import oss_service
            
            # Download file from OSS
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(input_oss_key)[1]) as input_temp:
                oss_service.bucket.get_object_to_file(input_oss_key, input_temp.name)
                input_temp_path = input_temp.name
            
            # Create temporary file for output
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as output_temp:
                output_temp_path = output_temp.name
            
            # Use ffmpeg to convert to audio
            cmd = [
                "ffmpeg",
                "-i", input_temp_path,
                "-vn",
                "-acodec", "libmp3lame",
                "-y",
                output_temp_path
            ]
            
            logger.info(f"Converting OSS file: {input_oss_key} to audio")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                raise Exception(f"Audio conversion failed: {result.stderr}")
            
            # Read the converted audio as binary
            with open(output_temp_path, 'rb') as audio_file:
                audio_data = audio_file.read()
            
            logger.info(f"Audio conversion successful, size: {len(audio_data)} bytes")
            
            # Clean up temporary files
            os.unlink(input_temp_path)
            os.unlink(output_temp_path)
            
            return audio_data
        except Exception as e:
            logger.error(f"Audio conversion error: {str(e)}")
            raise


audio_conversion_service = AudioConversionService()
