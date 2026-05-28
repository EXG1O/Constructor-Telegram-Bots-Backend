from django.core.exceptions import SuspiciousFileOperation
from django.core.files.storage import default_storage


def force_get_file_size(path: str) -> int:
    try:
        return default_storage.size(path)
    except SuspiciousFileOperation, OSError:
        return 0
