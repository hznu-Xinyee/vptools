"""backfill video translation tags

Revision ID: 4a7102af09c7
Revises: 18e286700e23
Create Date: 2026-05-26 16:13:44.678929

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import json
import re


revision: str = '4a7102af09c7'
down_revision: Union[str, None] = '18e286700e23'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    tasks = bind.execute(sa.text("""
        SELECT id, user_id, tags, created_at
        FROM video_translation_tasks
        WHERE tags IS NOT NULL
        AND tags <> ''
    """)).mappings()

    for task in tasks:
        try:
            raw_tags = json.loads(task["tags"])
        except (TypeError, json.JSONDecodeError):
            continue

        if not isinstance(raw_tags, list):
            continue

        seen = set()
        for raw_tag in raw_tags:
            tag_name = normalize_tag_name(raw_tag)
            if not tag_name:
                continue

            normalized_name = normalize_tag_key(tag_name)
            if not normalized_name or normalized_name in seen:
                continue
            seen.add(normalized_name)

            tag_id = bind.execute(sa.text("""
                INSERT INTO video_translation_tags (user_id, name, normalized_name, created_at, updated_at)
                VALUES (:user_id, :name, :normalized_name, COALESCE(:created_at, NOW()), COALESCE(:created_at, NOW()))
                ON CONFLICT (user_id, normalized_name)
                DO UPDATE SET updated_at = GREATEST(video_translation_tags.updated_at, EXCLUDED.updated_at)
                RETURNING id
            """), {
                "user_id": task["user_id"],
                "name": tag_name,
                "normalized_name": normalized_name,
                "created_at": task["created_at"],
            }).scalar_one()

            bind.execute(sa.text("""
                INSERT INTO video_translation_task_tags (task_id, tag_id, created_at)
                VALUES (:task_id, :tag_id, COALESCE(:created_at, NOW()))
                ON CONFLICT (task_id, tag_id) DO NOTHING
            """), {
                "task_id": task["id"],
                "tag_id": tag_id,
                "created_at": task["created_at"],
            })


def downgrade() -> None:
    pass


def normalize_tag_name(value) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).strip())[:100]


def normalize_tag_key(value) -> str:
    return normalize_tag_name(value).lower()
