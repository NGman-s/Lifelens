import base64
import json
import logging
import mimetypes
import os
import time

from PIL import Image
import pillow_avif
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

logger = logging.getLogger(__name__)

# Configuration for Qwen-VL-Max (assuming OpenAI-compatible endpoint like DashScope)
# For DashScope:
# API_KEY: Your DashScope API Key
# BASE_URL: "https://dashscope.aliyuncs.com/compatible-mode/v1"
# MODEL: "qwen-vl-max"

async_client = AsyncOpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
)


class VisionServiceError(Exception):
    """Safe error surfaced to API clients."""


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def _ensure_api_key_configured():
    if os.getenv("DASHSCOPE_API_KEY"):
        return
    logger.error("DASHSCOPE_API_KEY is not configured")
    raise VisionServiceError("图像分析服务暂时不可用，请稍后重试")


async def analyze_food_image(image_path, user_context):
    converted_path = None
    try:
        _ensure_api_key_configured()

        ext = os.path.splitext(image_path)[1].lower()
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type:
            mime_map = {
                ".webp": "image/webp",
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".gif": "image/gif",
                ".bmp": "image/bmp",
                ".avif": "image/avif",
            }
            mime_type = mime_map.get(ext, "image/jpeg")

        if ext == ".avif" or mime_type == "image/avif":
            logger.info("Converting AVIF to JPEG: %s", image_path)
            try:
                img = Image.open(image_path)
                converted_path = image_path.rsplit(".", 1)[0] + "_converted.jpg"
                img.convert("RGB").save(converted_path, "JPEG", quality=95)
                image_path = converted_path
                mime_type = "image/jpeg"
                logger.info("Successfully converted AVIF to JPEG: %s", converted_path)
            except Exception:
                logger.exception("AVIF conversion failed for %s", image_path)

        base64_image = encode_image(image_path)
        logger.info("Analyzing image: %s, detected MIME: %s", image_path, mime_type)

        prompt = f"""
        Role: Professional Nutritionist and AI Vision Expert.
        Task: Analyze the provided food image and provide nutritional information based on the user's profile.

        IMPORTANT: All text content in the output (values for name, summary, suggestion, thought_process, tags, etc.) MUST be in Simplified Chinese (简体中文). Keep the JSON keys in English.

        User Profile:
        - Age: {user_context.get('age')}
        - Gender: {user_context.get('gender', 'Not specified')}
        - Height: {user_context.get('height', 'Not specified')} cm
        - Weight: {user_context.get('weight', 'Not specified')} kg
        - Activity Level: {user_context.get('activity_level', 'Not specified')}
        - Goal: {user_context.get('goal')}
        - Health Conditions: {', '.join(user_context.get('health_conditions', []))}

        Instructions:
        1. First, identify all food items in the image and estimate their portions accurately.
        2. Reason about the nutritional content (macros/micros) based on ingredients.
        3. MANDATORY SAFETY CHECK: Cross-reference the identified ingredients with the user's health conditions.
           - Start your thought process by explicitly listing the health conditions considered: "考虑到用户的[健康状况1, 健康状况2]...".
           - IF USER HAS ALLERGIES: You MUST flag ANY potential presence or risk of cross-contamination of the allergen.
           - If user has "Diabetes": Be extremely sensitive to added sugars, white flour, and high-GI fruits.
           - If user has "Hypertension": Be extremely sensitive to high sodium (salt), processed meats, and salty sauces.
           - If user has "High Cholesterol": Flag high saturated fats and trans fats.
        4. Traffic Light Logic (Rating Standards):
           - RED: Mandatory for any direct ALLERGY exposure. Also for direct, high-risk conflicts with health conditions (e.g., sugary drink for Diabetic, high-sodium meal for Hypertension).
           - YELLOW: Borderline/Caution. High in calories, fat, sugar, or sodium relative to goals, or requiring strict portion control.
           - GREEN: Safe and recommended. No health conflicts; aligns with nutrition goals.
        5. Global Calculation:
           - Calculate 'total_calories' by summing up the calories of all identified items.
           - Generate a 'main_name' that describes the entire meal (e.g., "Avocado Salmon Salad").
           - Determine a 'total_traffic_light' based on the overall health impact.
           - Provide a 'warning_message' ONLY IF 'total_traffic_light' is 'red' or 'yellow', explaining the specific health risk or allergy concern clearly in Chinese.

        Output Format (STRICT JSON):
        {{
            "main_name": "Overall Dish Name (Chinese)",
            "total_calories": 0,
            "total_traffic_light": "green/yellow/red",
            "warning_message": "Clear warning in Chinese (if red/yellow, otherwise empty string)",
            "thought_process": "Detailed step-by-step reasoning in Chinese",
            "items": [
                {{
                    "name": "Dish Name (Chinese)",
                    "calories": 0,
                    "unit": "kcal",
                    "nutrition_tags": ["Tag1", "Tag2"],
                    "traffic_light": "green/yellow/red"
                }}
            ],
            "total_analysis": {{
                "summary": "Short summary of the meal in Chinese",
                "suggestion": "Practical advice for the user in Chinese",
                "confidence": 0.95
            }}
        }}
        """

        response = await async_client.chat.completions.create(
            model="qwen3-vl-flash",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"},
            timeout=45.0
        )

        content = response.choices[0].message.content
        return json.loads(content)
    except VisionServiceError:
        raise
    except Exception:
        logger.exception("Error in analyze_food_image")
        raise VisionServiceError("图像分析服务暂时不可用，请稍后重试")
    finally:
        if converted_path and os.path.exists(converted_path):
            try:
                os.remove(converted_path)
                logger.info("Cleaned up converted file: %s", converted_path)
            except Exception:
                logger.exception("Error cleaning up %s", converted_path)


async def generate_alternative_suggestions(analysis_result, user_context):
    start_time = time.time()
    try:
        _ensure_api_key_configured()
        food_name = analysis_result.get("main_name", "未知食物")

        logger.info("Generating suggestions for: %s", food_name)

        prompt = f"""
        Role: Professional Nutritionist and AI Diet Expert.
        Task: Based on a previous food analysis which resulted in a YELLOW or RED alert, provide two types of "AI Hack" (AI 爆改) suggestions to make the meal healthier.

        Context:
        - Food Name: {food_name}
        - Calories: {analysis_result.get('total_calories')} kcal
        - Warning Message: {analysis_result.get('warning_message')}
        - Current Rating: {analysis_result.get('total_traffic_light')}
        - User Goal: {user_context.get('goal')}
        - User Health Conditions: {', '.join(user_context.get('health_conditions', []))}

        Instructions:
        1. Provide an 'ordering_hint': A better choice if the user is ordering from a restaurant (e.g., "将日式拉面换成荞麦凉面"). For RED alerts, suggesting a completely different dish is often necessary.
        2. Provide a 'cooking_hint': A way to modify the dish if the user is cooking at home (e.g., "将 50% 的面条替换为魔芋丝"). For RED alerts, highlight ways to drastically reduce the problematic component.
        3. Keep suggestions concise, practical, and highly relevant to the warning message and user context.
        4. Both suggestions MUST be in Simplified Chinese (简体中文).

        Output Format (STRICT JSON):
        {{
            "ordering_hint": "Ordering suggestion here",
            "cooking_hint": "Cooking suggestion here"
        }}
        """

        response = await async_client.chat.completions.create(
            model="qwen-flash",
            messages=[
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}]
                }
            ],
            response_format={"type": "json_object"},
            timeout=30.0
        )

        content = response.choices[0].message.content
        duration = time.time() - start_time
        logger.info("Suggestions for %s generated in %.2fs", food_name, duration)
        return json.loads(content)
    except VisionServiceError:
        raise
    except Exception:
        duration = time.time() - start_time
        logger.exception("Error in generate_alternative_suggestions after %.2fs", duration)
        raise VisionServiceError("爆改建议服务暂时不可用，请稍后重试")
