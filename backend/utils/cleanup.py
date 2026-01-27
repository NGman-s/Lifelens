import os
import time
import asyncio
from datetime import datetime, timedelta

async def cleanup_old_files(directory: str, days: int = 8):
    """
    Delete files in the specified directory that are older than the given number of days.
    """
    if not os.path.exists(directory):
        return

    now = time.time()
    cutoff_time = now - (days * 86400)  # days * seconds per day

    print(f"[{datetime.now()}] Starting cleanup for directory: {directory}")

    count = 0
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)

        # Skip directories
        if not os.path.isfile(file_path):
            continue

        try:
            file_mtime = os.path.getmtime(file_path)
            if file_mtime < cutoff_time:
                os.remove(file_path)
                count += 1
                print(f"Deleted old file: {filename}")
        except Exception as e:
            print(f"Error checking/deleting file {filename}: {e}")

    print(f"[{datetime.now()}] Cleanup finished. Deleted {count} files.")

async def periodic_cleanup(directory: str, days: int = 8, interval_hours: int = 24):
    """
    Run cleanup periodically.
    """
    while True:
        await cleanup_old_files(directory, days)
        await asyncio.sleep(interval_hours * 3600)
