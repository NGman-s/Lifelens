import asyncio
import logging
import os
import time
from datetime import datetime
from typing import Iterable, Optional

logger = logging.getLogger(__name__)


async def cleanup_old_files(directory: str, days: int = 8):
    """Delete files in the specified directory that are older than the given number of days."""
    if not os.path.exists(directory):
        return

    now = time.time()
    cutoff_time = now - (days * 86400)

    logger.info("[%s] Starting cleanup for directory: %s", datetime.now(), directory)

    count = 0
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)

        if not os.path.isfile(file_path):
            continue

        try:
            file_mtime = os.path.getmtime(file_path)
            if file_mtime < cutoff_time:
                os.remove(file_path)
                count += 1
                logger.info("Deleted old file: %s", filename)
        except Exception:
            logger.exception("Error checking/deleting file %s", filename)

    logger.info("[%s] Cleanup finished. Deleted %s files.", datetime.now(), count)


def enforce_storage_limit(
    directory: str,
    max_total_size_bytes: int,
    protected_paths: Optional[Iterable[str]] = None,
):
    """Delete the oldest files until the directory fits within the configured size limit."""
    if max_total_size_bytes <= 0 or not os.path.exists(directory):
        return

    protected = {
        os.path.abspath(path)
        for path in (protected_paths or [])
        if path
    }

    files = []
    total_size = 0
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if not os.path.isfile(file_path):
            continue

        try:
            size = os.path.getsize(file_path)
            mtime = os.path.getmtime(file_path)
        except OSError:
            logger.exception("Error reading file metadata for %s", file_path)
            continue

        files.append((mtime, file_path, size))
        total_size += size

    if total_size <= max_total_size_bytes:
        return

    files.sort(key=lambda item: item[0])
    deleted_count = 0
    for _, file_path, size in files:
        if total_size <= max_total_size_bytes:
            break
        if os.path.abspath(file_path) in protected:
            continue

        try:
            os.remove(file_path)
            total_size -= size
            deleted_count += 1
            logger.info("Deleted file to enforce storage limit: %s", os.path.basename(file_path))
        except OSError:
            logger.exception("Error deleting file %s while enforcing storage limit", file_path)

    logger.info(
        "[%s] Storage limit check finished. Current size=%s bytes, deleted=%s files.",
        datetime.now(),
        total_size,
        deleted_count,
    )


async def periodic_cleanup(
    directory: str,
    days: int = 8,
    interval_hours: int = 24,
    stop_event: Optional[asyncio.Event] = None,
    max_total_size_bytes: Optional[int] = None,
):
    """Run cleanup periodically until stop_event is set."""
    while True:
        await cleanup_old_files(directory, days)
        if max_total_size_bytes:
            enforce_storage_limit(directory, max_total_size_bytes)
        if stop_event is None:
            await asyncio.sleep(interval_hours * 3600)
            continue
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval_hours * 3600)
            break
        except asyncio.TimeoutError:
            continue
