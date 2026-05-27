#!/usr/bin/env python3
"""
脚本功能：
1. 读取音色列表文件
2. 为每个音色生成"你好"的语音预览
3. 将音色信息导入到数据库
"""

import os
import sys
from pathlib import Path
from elevenlabs.client import ElevenLabs
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.custom_voice import CustomVoice
from app.core.database import Base

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 配置
ELEVENLABS_API_KEY = "sk_8165256a99e32b490b47abc0e2cf707dc747e3f42359ce7e"
VOICE_LIST_FILE = "/Users/montageai/Desktop/vp_dev/txt.txt"
HELLO_VOICES_DIR = os.path.join(os.path.dirname(__file__), "frontend", "public", "hello_voices")

# 语言映射（根据音色名称推断语言）
LANGUAGE_MAP = {
    "韩语": "ko",
    "德语": "de",
    "日语": "ja",
    "法语": "fr",
    "西班牙语": "es",
    "马来语": "ms",
    "印尼语": "id",
    "俄语": "ru",
    "意大利语": "it"
}

# 各语言的"你好"
GREETINGS = {
    "ko": "안녕하세요",
    "de": "Hallo",
    "ja": "こんにちは",
    "fr": "Bonjour",
    "es": "Hola",
    "ms": "Helo",
    "id": "Halo",
    "ru": "Привет",
    "it": "Ciao"
}


def get_database_url():
    """从环境变量或.env文件获取数据库URL"""
    if os.environ.get("DATABASE_URL"):
        return os.environ["DATABASE_URL"]

    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, _, value = line.partition("=")
                    if key.strip() == "DATABASE_URL":
                        return value.strip().strip('"').strip("'")

    raise RuntimeError("DATABASE_URL is not set")


def parse_voice_list(file_path):
    """解析音色列表文件"""
    voices = []
    current_language = None
    current_gender = None

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # 跳过行号
            parts = line.split('\t', 1)
            if len(parts) == 2:
                content = parts[1]
            else:
                content = line

            # 检查是否是语言标签
            is_language_tag = False
            for lang_name, lang_code in LANGUAGE_MAP.items():
                if lang_name in content:
                    current_language = lang_code
                    if "男声" in content:
                        current_gender = "male"
                    elif "女声" in content:
                        current_gender = "female"
                    is_language_tag = True
                    logger.info(f"检测到语言标签: {content} -> {lang_code} ({current_gender})")
                    break

            # 如果不是语言标签，则是voice_id
            if not is_language_tag and current_language and current_gender:
                voice_id = content
                voices.append({
                    'voice_id': voice_id,
                    'language': current_language,
                    'gender': current_gender,
                    'name': f"{LANGUAGE_MAP.get(current_language, current_language).upper()} {current_gender} - {voice_id[:8]}"
                })

    return voices


def generate_voice_preview(client, voice_id, language, output_path):
    """生成音色预览"""
    text = GREETINGS.get(language, "Hello")

    try:
        logger.info(f"生成音色预览: {voice_id} ({language}) - '{text}'")
        audio = client.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id="eleven_flash_v2_5",
            output_format="mp3_44100_128",
        )

        with open(output_path, "wb") as f:
            for chunk in audio:
                f.write(chunk)

        logger.info(f"✓ 成功生成: {output_path}")
        return True
    except Exception as e:
        logger.error(f"✗ 生成失败 {voice_id}: {e}")
        return False


def import_to_database(voices, db_session, user_id=1):
    """将音色导入数据库"""
    success_count = 0
    skip_count = 0

    for voice_data in voices:
        # 检查是否已存在
        existing = db_session.query(CustomVoice).filter(
            CustomVoice.voice_id == voice_data['voice_id']
        ).first()

        if existing:
            logger.info(f"跳过已存在的音色: {voice_data['voice_id']}")
            skip_count += 1
            continue

        # 创建新记录
        db_voice = CustomVoice(
            user_id=user_id,
            name=voice_data['name'],
            voice_id=voice_data['voice_id'],
            language=voice_data['language'],
            gender=voice_data['gender'],
            description=f"Auto-imported {voice_data['language']} {voice_data['gender']} voice"
        )

        db_session.add(db_voice)
        success_count += 1
        logger.info(f"✓ 导入音色: {voice_data['name']}")

    db_session.commit()
    return success_count, skip_count


def main():
    logger.info("=" * 60)
    logger.info("开始批量生成音色预览并导入数据库")
    logger.info("=" * 60)

    # 1. 解析音色列表
    logger.info(f"\n步骤 1: 解析音色列表文件 {VOICE_LIST_FILE}")
    voices = parse_voice_list(VOICE_LIST_FILE)
    logger.info(f"共找到 {len(voices)} 个音色")

    # 2. 创建输出目录
    os.makedirs(HELLO_VOICES_DIR, exist_ok=True)
    logger.info(f"\n步骤 2: 创建输出目录 {HELLO_VOICES_DIR}")

    # 3. 生成音色预览
    logger.info(f"\n步骤 3: 生成音色预览")
    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

    success_count = 0
    skip_count = 0
    fail_count = 0

    for i, voice in enumerate(voices, 1):
        output_path = os.path.join(HELLO_VOICES_DIR, f"{voice['voice_id']}.mp3")

        # 如果文件已存在，跳过
        if os.path.exists(output_path):
            logger.info(f"[{i}/{len(voices)}] 跳过已存在: {voice['voice_id']}")
            skip_count += 1
            continue

        # 生成预览
        logger.info(f"[{i}/{len(voices)}] 处理中...")
        if generate_voice_preview(client, voice['voice_id'], voice['language'], output_path):
            success_count += 1
        else:
            fail_count += 1

    logger.info(f"\n音色预览生成完成:")
    logger.info(f"  - 成功: {success_count}")
    logger.info(f"  - 跳过: {skip_count}")
    logger.info(f"  - 失败: {fail_count}")

    # 4. 导入数据库
    logger.info(f"\n步骤 4: 导入音色到数据库")
    try:
        database_url = get_database_url()
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        import_success, import_skip = import_to_database(voices, db, user_id=1)

        logger.info(f"\n数据库导入完成:")
        logger.info(f"  - 新增: {import_success}")
        logger.info(f"  - 跳过: {import_skip}")

        db.close()
    except Exception as e:
        logger.error(f"数据库导入失败: {e}")
        return 1

    logger.info("\n" + "=" * 60)
    logger.info("所有任务完成！")
    logger.info("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
