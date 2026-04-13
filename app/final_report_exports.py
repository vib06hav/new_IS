from __future__ import annotations

import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from uuid import UUID

from app.config import settings
from app.models.final_report import FinalReport
from app.storage import StorageService, storage_key_for_final_report_export


FINAL_REPORT_EXPORT_CONTENT_TYPE = "application/json"


def persist_final_report_export(
    *,
    storage: StorageService,
    application_id: UUID | str,
    content: dict,
) -> tuple[str, str]:
    temp_dir = Path(settings.UPLOAD_DIRECTORY)
    temp_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json", dir=temp_dir, mode="w", encoding="utf-8") as temp_file:
        json.dump(content, temp_file, ensure_ascii=False, indent=2)
        temp_path = temp_file.name

    export_key = storage_key_for_final_report_export(application_id)
    try:
        storage.put_file(temp_path, export_key, FINAL_REPORT_EXPORT_CONTENT_TYPE)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
    return export_key, FINAL_REPORT_EXPORT_CONTENT_TYPE


def sync_final_report_export(
    *,
    storage: StorageService,
    final_report: FinalReport,
) -> None:
    export_key, export_content_type = persist_final_report_export(
        storage=storage,
        application_id=final_report.application_id,
        content=final_report.content,
    )
    final_report.export_key = export_key
    final_report.export_content_type = export_content_type


@contextmanager
def final_report_export_stream(
    *,
    storage: StorageService,
    final_report: FinalReport,
) -> Iterator[tuple[object, str]]:
    if final_report.export_key and storage.exists(final_report.export_key):
        with storage.open_stream(final_report.export_key) as handle:
            yield handle, final_report.export_content_type or FINAL_REPORT_EXPORT_CONTENT_TYPE
        return

    temp_dir = Path(settings.UPLOAD_DIRECTORY)
    temp_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json", dir=temp_dir, mode="w", encoding="utf-8") as temp_file:
        json.dump(final_report.content, temp_file, ensure_ascii=False, indent=2)
        temp_path = temp_file.name

    try:
        with open(temp_path, "rb") as handle:
            yield handle, FINAL_REPORT_EXPORT_CONTENT_TYPE
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
