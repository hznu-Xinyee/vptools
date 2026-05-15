import oss2
import uuid
import io
from datetime import datetime, timedelta
from typing import Optional, BinaryIO
from fastapi import UploadFile
from app.core.config import settings


# Upload progress tracking
upload_progress = {}


class OSSService:
    def __init__(self):
        self.auth = oss2.Auth(
            settings.OSS_ACCESS_KEY_ID,
            settings.OSS_ACCESS_KEY_SECRET
        )
        self.bucket = oss2.Bucket(
            self.auth,
            settings.OSS_ENDPOINT,
            settings.OSS_BUCKET_NAME
        )
    
    def generate_upload_key(self, filename: str, user_id: int) -> str:
        """Generate unique key for file upload"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_str = uuid.uuid4().hex[:8]
        ext = filename.split('.')[-1] if '.' in filename else ''
        return f"subtitle_erase/{user_id}/{timestamp}_{random_str}.{ext}"
    
    def upload_file(self, key: str, file_data: BinaryIO, content_type: str = None) -> bool:
        """Upload file directly to OSS"""
        try:
            headers = {}
            if content_type:
                headers['Content-Type'] = content_type
            self.bucket.put_object(key, file_data, headers=headers)
            return True
        except Exception as e:
            raise Exception(f"OSS upload failed: {str(e)}")
    
    def generate_presigned_url(self, key: str, expires: int = 3600, method: str = 'PUT') -> str:
        """Generate presigned URL for upload/download"""
        return self.bucket.sign_url(method, key, expires)
    
    def generate_download_url(self, key: str, expires: int = 604800) -> str:
        """Generate presigned download URL with long expiration (default 7 days)"""
        return self.bucket.sign_url('GET', key, expires)
    
    def get_file_url(self, key: str) -> str:
        """Get public URL for file"""
        return f"https://{settings.OSS_BUCKET_NAME}.{settings.OSS_ENDPOINT.replace('https://', '')}/{key}"
    
    def file_exists(self, key: str) -> bool:
        """Check if file exists in OSS"""
        return self.bucket.object_exists(key)
    
    def delete_file(self, key: str) -> bool:
        """Delete file from OSS"""
        try:
            self.bucket.delete_object(key)
            return True
        except:
            return False

    def upload_file_multipart(self, file: UploadFile, key: str, upload_id: str = None) -> str:
        """Multipart upload large file to OSS (10MB chunks)"""
        try:
            # Generate upload_id if not provided
            if not upload_id:
                upload_id = uuid.uuid4().hex

            # Initialize progress tracking
            upload_progress[upload_id] = {
                "status": "uploading",
                "progress": 0,
                "total_parts": 0,
                "uploaded_parts": 0,
                "error": None
            }

            # Initialize multipart upload
            oss_upload_id = self.bucket.init_multipart_upload(key).upload_id
            parts = []

            part_size = 10 * 1024 * 1024  # 10MB per part
            part_number = 1

            # Get total file size for progress calculation
            file.file.seek(0, 2)  # Seek to end
            total_size = file.file.tell()
            file.file.seek(0)  # Seek back to beginning

            total_parts = (total_size + part_size - 1) // part_size
            upload_progress[upload_id]["total_parts"] = total_parts

            while True:
                chunk = file.file.read(part_size)
                if not chunk:
                    break

                result = self.bucket.upload_part(
                    key,
                    oss_upload_id,
                    part_number,
                    io.BytesIO(chunk)
                )
                parts.append(oss2.models.PartInfo(part_number, result.etag))

                # Update progress
                upload_progress[upload_id]["uploaded_parts"] = part_number
                upload_progress[upload_id]["progress"] = int((part_number / total_parts) * 100)
                part_number += 1

            # Complete multipart upload
            self.bucket.complete_multipart_upload(key, oss_upload_id, parts)
            upload_progress[upload_id]["status"] = "completed"
            upload_progress[upload_id]["progress"] = 100

            return self.get_file_url(key)
        except Exception as e:
            if upload_id and upload_id in upload_progress:
                upload_progress[upload_id]["status"] = "failed"
                upload_progress[upload_id]["error"] = str(e)
            raise Exception(f"OSS multipart upload failed: {str(e)}")

oss_service = OSSService()
