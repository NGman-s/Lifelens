import asyncio
import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageOps, UnidentifiedImageError
import pillow_avif
from pydantic import BaseModel
import uvicorn

from services.vision_service import (
    VisionServiceError,
    analyze_food_image,
    generate_alternative_suggestions,
)
from utils.cleanup import enforce_storage_limit, periodic_cleanup

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

ALLOWED_IMAGE_FORMATS = {
    "JPEG": ".jpg",
    "PNG": ".png",
    "WEBP": ".webp",
    "BMP": ".bmp",
    "AVIF": ".avif",
}
DISALLOWED_CONTENT_TYPES = {"image/svg+xml", "text/html"}
CHUNK_SIZE = 1024 * 1024
RESAMPLING_LANCZOS = getattr(getattr(Image, "Resampling", Image), "LANCZOS")

BASE_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = BASE_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)


class UploadValidationError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _load_int(name, default, min_value=1, max_value=None, aliases=None):
    raw_value = str(default).strip()
    source_name = name
    for candidate in [name, *(aliases or [])]:
        env_value = os.getenv(candidate)
        if env_value is None or not str(env_value).strip():
            continue
        raw_value = str(env_value).strip()
        source_name = candidate
        break

    try:
        parsed = int(raw_value)
    except (TypeError, ValueError):
        logger.warning("Invalid %s=%s, fallback to %s", source_name, raw_value, default)
        return default

    if parsed < min_value or (max_value is not None and parsed > max_value):
        logger.warning("Invalid %s=%s, fallback to %s", source_name, raw_value, default)
        return default

    return parsed


MAX_UPLOAD_SIZE_MB = _load_int("MAX_UPLOAD_SIZE_MB", 10)
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
THUMBNAIL_RETENTION_DAYS = _load_int(
    "THUMBNAIL_RETENTION_DAYS",
    30,
    aliases=["UPLOAD_RETENTION_DAYS"],
)
THUMBNAIL_MAX_EDGE = _load_int("THUMBNAIL_MAX_EDGE", 512)
THUMBNAIL_QUALITY = _load_int("THUMBNAIL_QUALITY", 70, min_value=1, max_value=100)
UPLOAD_STORAGE_LIMIT_MB = _load_int("UPLOAD_STORAGE_LIMIT_MB", 3072)
UPLOAD_STORAGE_LIMIT_BYTES = UPLOAD_STORAGE_LIMIT_MB * 1024 * 1024


@asynccontextmanager
async def lifespan(app: FastAPI):
    _migrate_legacy_webp_thumbnails()
    stop_event = asyncio.Event()
    cleanup_task = asyncio.create_task(
        periodic_cleanup(
            str(UPLOADS_DIR),
            days=THUMBNAIL_RETENTION_DAYS,
            interval_hours=24,
            stop_event=stop_event,
            max_total_size_bytes=UPLOAD_STORAGE_LIMIT_BYTES,
        )
    )
    app.state.cleanup_stop_event = stop_event
    app.state.cleanup_task = cleanup_task
    try:
        yield
    finally:
        stop_event.set()
        await cleanup_task


app = FastAPI(title="LifeLens API", version="1.0.0", lifespan=lifespan)


def _load_cors_origins():
    raw = os.getenv("CORS_ALLOW_ORIGINS", "*").strip()
    if raw == "*":
        return ["*"]
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def _safe_int(value, default=0):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_traffic_light(value, default="yellow"):
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"green", "yellow", "red"}:
            return normalized
    return default


def _normalize_items(items):
    normalized_items = []
    if not isinstance(items, list):
        return normalized_items

    for item in items:
        if not isinstance(item, dict):
            continue
        tags = item.get("nutrition_tags")
        if not isinstance(tags, list):
            tags = []
        normalized_items.append(
            {
                "name": str(item.get("name") or "未知菜品"),
                "calories": _safe_int(item.get("calories"), 0),
                "unit": str(item.get("unit") or "kcal"),
                "nutrition_tags": [str(tag) for tag in tags if tag is not None],
                "traffic_light": _normalize_traffic_light(
                    item.get("traffic_light"), "yellow"
                ),
            }
        )
    return normalized_items


def _normalize_analysis_result(result):
    if not isinstance(result, dict):
        raise ValueError("Invalid analysis response format")

    items = _normalize_items(result.get("items"))
    fallback_name = items[0]["name"] if items else "未知菜品"
    fallback_traffic = items[0]["traffic_light"] if items else "yellow"

    total_analysis = result.get("total_analysis")
    if not isinstance(total_analysis, dict):
        total_analysis = {}

    confidence = _safe_float(total_analysis.get("confidence"), 0.0)
    confidence = max(0.0, min(1.0, confidence))

    return {
        "main_name": str(result.get("main_name") or fallback_name),
        "total_calories": _safe_int(result.get("total_calories"), 0),
        "total_traffic_light": _normalize_traffic_light(
            result.get("total_traffic_light"), fallback_traffic
        ),
        "warning_message": str(result.get("warning_message") or ""),
        "thought_process": str(result.get("thought_process") or ""),
        "items": items,
        "total_analysis": {
            "summary": str(total_analysis.get("summary") or "暂无分析摘要"),
            "suggestion": str(total_analysis.get("suggestion") or "暂无建议"),
            "confidence": confidence,
        },
    }


def _normalize_alternatives_result(result):
    if not isinstance(result, dict):
        raise ValueError("Invalid alternatives response format")
    return {
        "ordering_hint": str(result.get("ordering_hint") or "暂无点餐建议"),
        "cooking_hint": str(result.get("cooking_hint") or "暂无烹饪建议"),
    }


def _error_response(message, status_code=500, trace_id=None):
    payload = {
        "code": status_code,
        "message": str(message),
    }
    if trace_id:
        payload["trace_id"] = trace_id
    return JSONResponse(status_code=status_code, content=payload)


def _delete_file(file_path):
    if not file_path:
        return
    path = Path(file_path)
    if path.exists():
        path.unlink(missing_ok=True)


def _to_utc_iso(dt):
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _build_image_expiration():
    return _to_utc_iso(datetime.now(timezone.utc) + timedelta(days=THUMBNAIL_RETENTION_DAYS))


def _migrate_legacy_webp_thumbnails():
    migrated_count = 0
    for webp_path in UPLOADS_DIR.glob("*.webp"):
        jpg_path = webp_path.with_suffix(".jpg")

        if jpg_path.exists():
            webp_path.unlink(missing_ok=True)
            migrated_count += 1
            continue

        try:
            with Image.open(webp_path) as source_image:
                image = _prepare_thumbnail_image(source_image)
                image.save(
                    jpg_path,
                    "JPEG",
                    quality=THUMBNAIL_QUALITY,
                    optimize=True,
                )
            webp_path.unlink(missing_ok=True)
            migrated_count += 1
        except Exception:
            logger.exception("Failed to migrate legacy thumbnail %s", webp_path.name)

    if migrated_count:
        logger.info("Migrated %s legacy WebP thumbnails to JPEG", migrated_count)


def _parse_user_context(raw_user_context):
    try:
        parsed = json.loads(raw_user_context)
    except json.JSONDecodeError as exc:
        raise UploadValidationError("用户档案格式无效", status_code=400) from exc

    if not isinstance(parsed, dict):
        raise UploadValidationError("用户档案格式无效", status_code=400)

    health_conditions = parsed.get("health_conditions")
    if not isinstance(health_conditions, list):
        parsed["health_conditions"] = []
    else:
        parsed["health_conditions"] = [str(item) for item in health_conditions]

    return parsed


def _detect_image_format(file_path):
    try:
        with Image.open(file_path) as image:
            image.verify()
        with Image.open(file_path) as image:
            detected_format = (image.format or "").upper()
    except (UnidentifiedImageError, OSError) as exc:
        logger.warning("Rejected invalid image file %s: %s", file_path, exc)
        raise UploadValidationError("仅支持 JPG、PNG、WEBP、BMP、AVIF 图片", 415) from exc

    if detected_format not in ALLOWED_IMAGE_FORMATS:
        raise UploadValidationError("仅支持 JPG、PNG、WEBP、BMP、AVIF 图片", 415)
    return detected_format


def _prepare_thumbnail_image(source_image):
    image = ImageOps.exif_transpose(source_image)
    has_alpha = "A" in image.getbands() or (
        image.mode == "P" and "transparency" in image.info
    )
    if has_alpha:
        alpha_image = image.convert("RGBA")
        background = Image.new("RGB", alpha_image.size, (255, 255, 255))
        background.paste(alpha_image, mask=alpha_image.getchannel("A"))
        return background
    if image.mode not in {"RGB", "L"}:
        return image.convert("RGB")
    if image.mode == "L":
        return image.convert("RGB")
    return image


def _create_thumbnail(source_path, trace_id):
    try:
        with Image.open(source_path) as source_image:
            image = _prepare_thumbnail_image(source_image)
            image.thumbnail((THUMBNAIL_MAX_EDGE, THUMBNAIL_MAX_EDGE), RESAMPLING_LANCZOS)
            jpeg_path = UPLOADS_DIR / f"{trace_id}.jpg"
            image.save(
                jpeg_path,
                "JPEG",
                quality=THUMBNAIL_QUALITY,
                optimize=True,
            )
            return jpeg_path
    except UploadValidationError:
        raise
    except Exception as exc:
        logger.exception("Failed to create thumbnail trace_id=%s", trace_id)
        raise UploadValidationError("生成缩略图失败，请重试", 500) from exc


async def _store_upload_file(upload_file: UploadFile, trace_id: str):
    content_type = (upload_file.content_type or "").lower().strip()
    if content_type in DISALLOWED_CONTENT_TYPES:
        raise UploadValidationError("仅支持 JPG、PNG、WEBP、BMP、AVIF 图片", 415)

    temp_path = UPLOADS_DIR / f"{trace_id}.upload"
    total_size = 0
    try:
        with temp_path.open("wb") as buffer:
            while True:
                chunk = await upload_file.read(CHUNK_SIZE)
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > MAX_UPLOAD_SIZE_BYTES:
                    raise UploadValidationError(
                        f"上传图片不能超过 {MAX_UPLOAD_SIZE_MB}MB",
                        413,
                    )
                buffer.write(chunk)

        if total_size == 0:
            raise UploadValidationError("上传文件不能为空", 400)

        detected_format = _detect_image_format(temp_path)
        final_path = UPLOADS_DIR / f"{trace_id}{ALLOWED_IMAGE_FORMATS[detected_format]}"
        temp_path.replace(final_path)
        return final_path
    except UploadValidationError:
        _delete_file(temp_path)
        raise
    except Exception as exc:
        _delete_file(temp_path)
        logger.exception("Failed to store uploaded file trace_id=%s", trace_id)
        raise UploadValidationError("上传图片失败，请重试", 500) from exc
    finally:
        await upload_file.close()


CORS_ORIGINS = _load_cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=CORS_ORIGINS != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")


class AlternativeRequest(BaseModel):
    analysis_result: dict
    user_context: dict


@app.get("/")
async def root():
    return {"message": "LifeLens API is running"}


@app.get("/api/v1/health")
async def health():
    return {
        "status": "ok",
        "service": "lifelens-api",
        "max_upload_size_mb": MAX_UPLOAD_SIZE_MB,
        "thumbnail_retention_days": THUMBNAIL_RETENTION_DAYS,
        "thumbnail_max_edge": THUMBNAIL_MAX_EDGE,
        "thumbnail_quality": THUMBNAIL_QUALITY,
        "upload_storage_limit_mb": UPLOAD_STORAGE_LIMIT_MB,
    }


@app.post("/api/v1/vision/analyze")
async def analyze_vision(file: UploadFile = File(...), user_context: str = Form(...)):
    trace_id = str(uuid.uuid4())
    source_file_path = None
    thumbnail_path = None

    try:
        parsed_user_context = _parse_user_context(user_context)
        source_file_path = await _store_upload_file(file, trace_id)
        analysis_result = await analyze_food_image(str(source_file_path), parsed_user_context)
        thumbnail_path = _create_thumbnail(source_file_path, trace_id)
        _delete_file(source_file_path)
        source_file_path = None

        # Keep the latest thumbnail available even if the directory is already over quota.
        enforce_storage_limit(
            str(UPLOADS_DIR),
            UPLOAD_STORAGE_LIMIT_BYTES,
            protected_paths=[str(thumbnail_path)],
        )

        normalized_result = _normalize_analysis_result(analysis_result)
        normalized_result["image_url"] = f"/uploads/{thumbnail_path.name}"
        normalized_result["image_expires_at"] = _build_image_expiration()
        return JSONResponse(
            status_code=200,
            content={
                "code": 200,
                "data": normalized_result,
                "trace_id": trace_id,
            },
        )
    except UploadValidationError as exc:
        _delete_file(source_file_path)
        _delete_file(thumbnail_path)
        return _error_response(exc.message, status_code=exc.status_code, trace_id=trace_id)
    except VisionServiceError as exc:
        _delete_file(source_file_path)
        _delete_file(thumbnail_path)
        return _error_response(str(exc), status_code=502, trace_id=trace_id)
    except ValueError:
        logger.exception("Invalid analysis response format trace_id=%s", trace_id)
        _delete_file(source_file_path)
        _delete_file(thumbnail_path)
        return _error_response("图像分析结果格式异常，请稍后重试", 502, trace_id)
    except Exception:
        logger.exception("Unexpected error during image analysis trace_id=%s", trace_id)
        _delete_file(source_file_path)
        _delete_file(thumbnail_path)
        return _error_response("服务器内部错误，请稍后重试", 500, trace_id)


@app.post("/api/v1/vision/generate-alternatives")
async def generate_alternatives(request: AlternativeRequest):
    trace_id = str(uuid.uuid4())
    try:
        result = await generate_alternative_suggestions(
            request.analysis_result,
            request.user_context,
        )
        normalized_result = _normalize_alternatives_result(result)
        return JSONResponse(status_code=200, content={"code": 200, "data": normalized_result})
    except VisionServiceError as exc:
        return _error_response(str(exc), status_code=502, trace_id=trace_id)
    except ValueError:
        logger.exception("Invalid alternatives response format trace_id=%s", trace_id)
        return _error_response("爆改建议结果格式异常，请稍后重试", 502, trace_id)
    except Exception:
        logger.exception("Unexpected error during alternatives generation trace_id=%s", trace_id)
        return _error_response("服务器内部错误，请稍后重试", 500, trace_id)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)

