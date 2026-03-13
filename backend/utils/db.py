import base64
import io
import os
import random
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

import qrcode
from zoneinfo import ZoneInfoNotFoundError

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "data" / "lifelens.db"
DB_PATH = Path(os.getenv("LIFELENS_DB_PATH", str(DEFAULT_DB_PATH)))
try:
    SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")
except ZoneInfoNotFoundError:
    # Windows Python environments may not ship IANA tzdata.
    SHANGHAI_TZ = timezone(timedelta(hours=8))


def _resolve_db_path() -> Path:
    db_path = Path(DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


def _utc_iso(dt: datetime) -> str:
    return (
        dt.astimezone(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _now_utc_iso() -> str:
    return _utc_iso(datetime.now(timezone.utc))


def _validate_or_create_user_id(user_id: Optional[str] = None) -> str:
    normalized = str(user_id or "").strip()
    if not normalized:
        return str(uuid.uuid4())

    try:
        return str(uuid.UUID(normalized))
    except ValueError as exc:
        raise ValueError("用户标识无效") from exc


def _build_qr_payload(friend_code: str) -> str:
    return f"lifelens:add:{friend_code}"


def _build_qr_image_data_url(payload: str) -> str:
    image = qrcode.make(payload)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _build_user_payload(row: sqlite3.Row) -> dict:
    friend_code = str(row["friend_code"])
    qr_payload = _build_qr_payload(friend_code)
    return {
        "user_id": row["user_id"],
        "friend_code": friend_code,
        "qr_payload": qr_payload,
        "qr_image_data_url": _build_qr_image_data_url(qr_payload),
    }


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_resolve_db_path()), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db() -> None:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                friend_code TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS friendships (
                user_id TEXT NOT NULL,
                friend_user_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                PRIMARY KEY (user_id, friend_user_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (friend_user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS diet_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                main_name TEXT NOT NULL,
                total_calories INTEGER NOT NULL,
                total_traffic_light TEXT NOT NULL,
                summary TEXT NOT NULL,
                image_url TEXT,
                image_expires_at TEXT,
                recorded_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_friendships_user_id ON friendships(user_id)"
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_diet_records_user_recorded_at
            ON diet_records(user_id, recorded_at)
            """
        )
        conn.commit()


def _generate_unique_friend_code(cursor: sqlite3.Cursor, max_attempts: int = 64) -> str:
    for _ in range(max_attempts):
        candidate = f"{random.randint(0, 999999):06d}"
        cursor.execute("SELECT 1 FROM users WHERE friend_code = ?", (candidate,))
        if not cursor.fetchone():
            return candidate
    raise RuntimeError("生成好友口令失败，请稍后重试")


def get_or_create_user(user_id: Optional[str] = None) -> dict:
    normalized_user_id = _validate_or_create_user_id(user_id)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id, friend_code FROM users WHERE user_id = ?",
            (normalized_user_id,),
        )
        row = cursor.fetchone()
        if row:
            return _build_user_payload(row)

        friend_code = _generate_unique_friend_code(cursor)
        cursor.execute(
            """
            INSERT INTO users (user_id, friend_code, created_at)
            VALUES (?, ?, ?)
            """,
            (normalized_user_id, friend_code, _now_utc_iso()),
        )
        conn.commit()
        return {
            "user_id": normalized_user_id,
            "friend_code": friend_code,
            "qr_payload": _build_qr_payload(friend_code),
            "qr_image_data_url": _build_qr_image_data_url(
                _build_qr_payload(friend_code)
            ),
        }


def _ensure_current_user(cursor: sqlite3.Cursor, user_id: str) -> None:
    cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
    if cursor.fetchone():
        return

    payload = get_or_create_user(user_id)
    cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (payload["user_id"],))
    if not cursor.fetchone():
        raise LookupError("当前用户不存在")


def add_friend(
    user_id: str,
    friend_code: Optional[str] = None,
    target_user_id: Optional[str] = None,
) -> dict:
    current_user_id = _validate_or_create_user_id(user_id)
    normalized_friend_code = str(friend_code or "").strip()
    normalized_target_user_id = str(target_user_id or "").strip()

    if int(bool(normalized_friend_code)) + int(bool(normalized_target_user_id)) != 1:
        raise ValueError("请提供好友口令或好友用户标识中的一种")

    with get_db() as conn:
        cursor = conn.cursor()
        _ensure_current_user(cursor, current_user_id)

        if normalized_friend_code:
            if not normalized_friend_code.isdigit() or len(normalized_friend_code) != 6:
                raise ValueError("好友口令必须为 6 位数字")
            cursor.execute(
                "SELECT user_id, friend_code FROM users WHERE friend_code = ?",
                (normalized_friend_code,),
            )
        else:
            normalized_target_user_id = _validate_or_create_user_id(normalized_target_user_id)
            cursor.execute(
                "SELECT user_id, friend_code FROM users WHERE user_id = ?",
                (normalized_target_user_id,),
            )

        target_row = cursor.fetchone()
        if not target_row:
            raise LookupError("好友不存在")

        target_user_id = target_row["user_id"]
        if target_user_id == current_user_id:
            raise ValueError("不能添加自己为好友")

        cursor.execute(
            """
            SELECT 1
            FROM friendships
            WHERE user_id = ? AND friend_user_id = ?
            """,
            (current_user_id, target_user_id),
        )
        created = cursor.fetchone() is None

        created_at = _now_utc_iso()
        cursor.execute(
            """
            INSERT OR IGNORE INTO friendships (user_id, friend_user_id, created_at)
            VALUES (?, ?, ?)
            """,
            (current_user_id, target_user_id, created_at),
        )
        cursor.execute(
            """
            INSERT OR IGNORE INTO friendships (user_id, friend_user_id, created_at)
            VALUES (?, ?, ?)
            """,
            (target_user_id, current_user_id, created_at),
        )
        conn.commit()

        return {
            "friend_user_id": target_user_id,
            "friend_code": target_row["friend_code"],
            "created": created,
        }


def save_diet_record(
    user_id: str,
    *,
    main_name: str,
    total_calories: int,
    total_traffic_light: str,
    summary: str,
    image_url: str = "",
    image_expires_at: str = "",
    recorded_at: Optional[str] = None,
) -> dict:
    current_user_id = _validate_or_create_user_id(user_id)
    main_name = str(main_name or "").strip()
    summary = str(summary or "").strip()
    traffic_light = str(total_traffic_light or "").strip().lower()

    if not main_name:
        raise ValueError("菜名不能为空")
    if not summary:
        raise ValueError("饮食摘要不能为空")
    if traffic_light not in {"green", "yellow", "red"}:
        raise ValueError("饮食状态无效")

    try:
        calories = int(total_calories)
    except (TypeError, ValueError) as exc:
        raise ValueError("热量格式无效") from exc

    if calories < 0:
        raise ValueError("热量不能为负数")

    with get_db() as conn:
        cursor = conn.cursor()
        _ensure_current_user(cursor, current_user_id)
        normalized_recorded_at = recorded_at or _now_utc_iso()
        cursor.execute(
            """
            INSERT INTO diet_records (
                user_id,
                main_name,
                total_calories,
                total_traffic_light,
                summary,
                image_url,
                image_expires_at,
                recorded_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                current_user_id,
                main_name,
                calories,
                traffic_light,
                summary,
                str(image_url or ""),
                str(image_expires_at or ""),
                normalized_recorded_at,
            ),
        )
        record_id = cursor.lastrowid
        conn.commit()
        return {"id": record_id, "recorded_at": normalized_recorded_at}


def _build_today_utc_range(reference_time: Optional[datetime] = None) -> tuple[str, str]:
    now = reference_time.astimezone(timezone.utc) if reference_time else datetime.now(timezone.utc)
    local_now = now.astimezone(SHANGHAI_TZ)
    local_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    local_end = local_start + timedelta(days=1)
    return _utc_iso(local_start), _utc_iso(local_end)


def get_today_friend_feed(user_id: str, reference_time: Optional[datetime] = None) -> dict:
    current_user_id = _validate_or_create_user_id(user_id)
    window_start, window_end = _build_today_utc_range(reference_time)

    with get_db() as conn:
        cursor = conn.cursor()
        _ensure_current_user(cursor, current_user_id)
        cursor.execute(
            "SELECT COUNT(*) AS total FROM friendships WHERE user_id = ?",
            (current_user_id,),
        )
        total_friends = int(cursor.fetchone()["total"])

        cursor.execute(
            """
            SELECT
                d.id,
                d.user_id AS friend_user_id,
                u.friend_code,
                d.main_name,
                d.total_calories,
                d.total_traffic_light,
                d.summary,
                d.image_url,
                d.image_expires_at,
                d.recorded_at
            FROM friendships f
            INNER JOIN diet_records d ON d.user_id = f.friend_user_id
            INNER JOIN users u ON u.user_id = f.friend_user_id
            WHERE f.user_id = ?
              AND d.recorded_at >= ?
              AND d.recorded_at < ?
            ORDER BY d.recorded_at DESC, d.id DESC
            """,
            (current_user_id, window_start, window_end),
        )

        items = [
            {
                "id": row["id"],
                "friend_user_id": row["friend_user_id"],
                "friend_code": row["friend_code"],
                "main_name": row["main_name"],
                "total_calories": row["total_calories"],
                "total_traffic_light": row["total_traffic_light"],
                "summary": row["summary"],
                "image_url": row["image_url"] or "",
                "image_expires_at": row["image_expires_at"] or "",
                "recorded_at": row["recorded_at"],
            }
            for row in cursor.fetchall()
        ]

        return {"total_friends": total_friends, "items": items}


def cleanup_expired_diet_records(retention_days: int) -> int:
    try:
        normalized_days = int(retention_days)
    except (TypeError, ValueError):
        return 0

    if normalized_days <= 0:
        return 0

    cutoff = _utc_iso(datetime.now(timezone.utc) - timedelta(days=normalized_days))
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM diet_records WHERE recorded_at < ?", (cutoff,))
        deleted = cursor.rowcount or 0
        conn.commit()
        return deleted
