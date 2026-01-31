import os
import shutil
import uuid
import asyncio
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import json
from services.vision_service import analyze_food_image, generate_alternative_suggestions
from utils.cleanup import periodic_cleanup

app = FastAPI(title="LifeLens API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
if not os.path.exists(UPLOADS_DIR):
    os.makedirs(UPLOADS_DIR)

# Mount uploads directory for static access
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

@app.on_event("startup")
async def startup_event():
    # Start periodic cleanup task in background (every 24h, delete files > 8 days old)
    asyncio.create_task(periodic_cleanup(UPLOADS_DIR, days=8, interval_hours=24))

@app.get("/")
async def root():
    return {"message": "LifeLens API is running"}

@app.post("/api/v1/vision/analyze")
async def analyze_vision(
    file: UploadFile = File(...),
    user_context: str = Form(...)
):
    # Save uploaded file
    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1]
    if not ext:
        ext = ".jpg" # Default to jpg if no extension

    filename = f"{file_id}{ext}"
    file_path = os.path.join(UPLOADS_DIR, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # Call Qwen-VL analysis
        analysis_result = await analyze_food_image(file_path, user_context)

        # Check if analysis failed (vision_service returns error dict instead of raising)
        if "error" in analysis_result:
            return {
                "code": 500,
                "message": analysis_result.get("error", "Analysis failed"),
                "trace_id": file_id
            }

        # Add image_url to the result
        # The frontend will prepend the BASE_URL
        analysis_result["image_url"] = f"/uploads/{filename}"

        return {
            "code": 200,
            "data": analysis_result,
            "trace_id": file_id
        }
    except Exception as e:
        # If analysis fails, we might still want to keep the image for debugging,
        # or delete it. For now, let's keep it consistent with the success case
        # (or maybe delete to save space if it's useless? Let's keep it simple).
        return {
            "code": 500,
            "message": str(e),
            "trace_id": file_id
        }

class AlternativeRequest(BaseModel):
    analysis_result: dict
    user_context: dict

@app.post("/api/v1/vision/generate-alternatives")
async def generate_alternatives(request: AlternativeRequest):
    try:
        # Convert dicts back to JSON strings for the service function if needed,
        # but the service can just take dicts too if updated.
        # Let's keep it consistent with the service's current signature.
        result = await generate_alternative_suggestions(
            json.dumps(request.analysis_result),
            json.dumps(request.user_context)
        )
        return {
            "code": 200,
            "data": result
        }
    except Exception as e:
        return {
            "code": 500,
            "message": str(e)
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
