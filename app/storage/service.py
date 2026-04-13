from __future__ import annotations

import mimetypes
import os
import shutil
import tempfile
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
from typing import BinaryIO, Iterator
from uuid import UUID

try:
    from minio import Minio
    from minio.error import S3Error
except ImportError:  # pragma: no cover - dependency may be absent in some local test envs
    Minio = None

    class S3Error(Exception):
        code = ""

from app.config import settings


def storage_key_for_source_pdf(application_id: UUID | str) -> str:
    return f"applications/{application_id}/source.pdf"


def storage_key_for_profile_image(user_id: UUID | str, extension: str) -> str:
    normalized_extension = extension.lower().lstrip(".")
    return f"profiles/users/{user_id}/avatar.{normalized_extension}"


def storage_key_for_final_report_export(application_id: UUID | str) -> str:
    return f"reports/{application_id}/exports/final-report.json"


class StorageService:
    def put_file(self, local_path: str, key: str, content_type: str) -> str:
        raise NotImplementedError

    def delete(self, key: str) -> None:
        raise NotImplementedError

    def exists(self, key: str) -> bool:
        raise NotImplementedError

    @contextmanager
    def open_stream(self, key: str) -> Iterator[BinaryIO]:
        raise NotImplementedError

    @contextmanager
    def materialize_to_tempfile(self, key: str, suffix: str = "") -> Iterator[str]:
        raise NotImplementedError


class LocalStorageService(StorageService):
    def __init__(self, root_directory: str):
        self.root_directory = Path(root_directory)
        self.root_directory.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, key: str) -> Path:
        normalized = Path(key.replace("\\", "/"))
        return self.root_directory / normalized

    def put_file(self, local_path: str, key: str, content_type: str) -> str:
        target_path = self._resolve_path(key)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(local_path, target_path)
        return key

    def delete(self, key: str) -> None:
        target_path = self._resolve_path(key)
        if target_path.exists():
            target_path.unlink()

    def exists(self, key: str) -> bool:
        return self._resolve_path(key).exists()

    @contextmanager
    def open_stream(self, key: str) -> Iterator[BinaryIO]:
        target_path = self._resolve_path(key)
        if not target_path.exists():
            raise FileNotFoundError(key)
        handle = target_path.open("rb")
        try:
            yield handle
        finally:
            handle.close()

    @contextmanager
    def materialize_to_tempfile(self, key: str, suffix: str = "") -> Iterator[str]:
        source_path = self._resolve_path(key)
        if not source_path.exists():
            raise FileNotFoundError(key)

        temp_dir = Path(settings.UPLOAD_DIRECTORY)
        temp_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=temp_dir) as temp_file:
            with source_path.open("rb") as source_file:
                shutil.copyfileobj(source_file, temp_file)
            temp_path = temp_file.name
        try:
            yield temp_path
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


class MinioStorageService(StorageService):
    def __init__(
        self,
        *,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        secure: bool,
    ):
        if Minio is None:
            raise RuntimeError("The 'minio' package is required when STORAGE_BACKEND=minio")
        self.bucket_name = bucket_name
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)

    def put_file(self, local_path: str, key: str, content_type: str) -> str:
        self.client.fput_object(
            self.bucket_name,
            key,
            local_path,
            content_type=content_type,
        )
        return key

    def delete(self, key: str) -> None:
        try:
            self.client.remove_object(self.bucket_name, key)
        except S3Error as exc:
            if exc.code != "NoSuchKey":
                raise

    def exists(self, key: str) -> bool:
        try:
            self.client.stat_object(self.bucket_name, key)
            return True
        except S3Error as exc:
            if exc.code == "NoSuchKey":
                return False
            raise

    @contextmanager
    def open_stream(self, key: str) -> Iterator[BinaryIO]:
        response = self.client.get_object(self.bucket_name, key)
        try:
            yield response
        finally:
            response.close()
            response.release_conn()

    @contextmanager
    def materialize_to_tempfile(self, key: str, suffix: str = "") -> Iterator[str]:
        temp_dir = Path(settings.UPLOAD_DIRECTORY)
        temp_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=temp_dir) as temp_file:
            temp_path = temp_file.name
        try:
            self.client.fget_object(self.bucket_name, key, temp_path)
            yield temp_path
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


@lru_cache(maxsize=1)
def get_storage_service() -> StorageService:
    if settings.STORAGE_BACKEND == "minio":
        return MinioStorageService(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            bucket_name=settings.MINIO_BUCKET,
            secure=settings.MINIO_SECURE,
        )
    return LocalStorageService(settings.UPLOAD_DIRECTORY)


def infer_extension_from_content_type(content_type: str | None, filename: str | None = None) -> str:
    if content_type:
        guessed = mimetypes.guess_extension(content_type)
        if guessed:
            return guessed.lstrip(".")
    if filename:
        suffix = Path(filename).suffix
        if suffix:
            return suffix.lstrip(".")
    return "bin"
