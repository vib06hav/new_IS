from pathlib import Path
from unittest.mock import MagicMock

from app.storage.service import LocalStorageService, MinioStorageService


def test_local_storage_put_open_materialize_and_delete(tmp_path):
    storage = LocalStorageService(str(tmp_path / "storage"))
    source_path = tmp_path / "source.txt"
    source_path.write_text("hello storage", encoding="utf-8")

    key = storage.put_file(str(source_path), "profiles/users/demo/avatar.txt", "text/plain")
    assert key == "profiles/users/demo/avatar.txt"
    assert storage.exists(key) is True

    with storage.open_stream(key) as handle:
        assert handle.read() == b"hello storage"

    with storage.materialize_to_tempfile(key, suffix=".txt") as materialized_path:
        assert Path(materialized_path).read_text(encoding="utf-8") == "hello storage"

    storage.delete(key)
    assert storage.exists(key) is False


def test_minio_storage_delegates_to_client_methods(monkeypatch, tmp_path):
    fake_client = MagicMock()
    fake_client.bucket_exists.return_value = True
    monkeypatch.setattr("app.storage.service.Minio", lambda *args, **kwargs: fake_client)

    storage = MinioStorageService(
        endpoint="localhost:9000",
        access_key="minioadmin",
        secret_key="minioadmin",
        bucket_name="ag-assets",
        secure=False,
    )

    source_path = tmp_path / "source.pdf"
    source_path.write_bytes(b"%PDF-1.4\n")

    storage.put_file(str(source_path), "applications/demo/source.pdf", "application/pdf")
    fake_client.fput_object.assert_called_once()

    fake_response = MagicMock()
    fake_client.get_object.return_value = fake_response
    with storage.open_stream("applications/demo/source.pdf") as handle:
        assert handle is fake_response
    fake_response.close.assert_called_once()
    fake_response.release_conn.assert_called_once()

    fake_client.stat_object.return_value = object()
    assert storage.exists("applications/demo/source.pdf") is True

    storage.delete("applications/demo/source.pdf")
    fake_client.remove_object.assert_called_once()
