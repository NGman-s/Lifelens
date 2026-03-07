import asyncio
import logging
import os
import time
from datetime import datetime
from typing import Optional

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


async def periodic_cleanup(
    directory: str,
    days: int = 8,
    interval_hours: int = 24,
    stop_event: Optional[asyncio.Event] = None,
):
    """Run cleanup periodically until stop_event is set."""
    while True:
        await cleanup_old_files(directory, days)
        if stop_event is None:
            await asyncio.sleep(interval_hours * 3600)
            continue
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval_hours * 3600)
            break
        except asyncio.TimeoutError:
            continue
