import os
import base64
import json
import mimetypes
from PIL import Image
import pillow_avif
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Configuration for Qwen-VL-Max (assuming OpenAI-compatible endpoint like DashScope)
# For DashScope:
# API_KEY: Your DashScope API Key
# BASE_URL: "https://dashscope.aliyuncs.com/compatible-mode/v1"
# MODEL: "qwen-vl-max"

client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
)

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

async def analyze_food_image(image_path, user_context_str):
    converted_path = None
    try:
        # Detect extension and handle format conversion if necessary
        ext = os.path.splitext(image_path)[1].lower()

        # Initial MIME type detection for format-specific logic
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type:
            mime_map = {
                '.webp': 'image/webp',
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.bmp': 'image/bmp',
                '.avif': 'image/avif'
            }
            mime_type = mime_map.get(ext, "image/jpeg")

        # DashScope/Qwen-VL might not support AVIF directly, convert to JPEG
        if ext == '.avif' or mime_type == 'image/avif':
            print(f"Converting AVIF to JPEG: {image_path}")
            try:
                img = Image.open(image_path)
                converted_path = image_path.rsplit('.', 1)[0] + "_converted.jpg"
                img.convert("RGB").save(converted_path, "JPEG", quality=95)
                image_path = converted_path
                mime_type = "image/jpeg"
                print(f"Successfully converted AVIF to JPEG: {converted_path}")
            except Exception as conv_err:
                print(f"AVIF conversion failed: {conv_err}")
                # Fallback to original and let the API decide

        base64_image = encode_image(image_path)
        user_context = json.loads(user_context_str)

        print(f"Analyzing image: {image_path}, Detected MIME: {mime_type}")

        # Construct the prompt with Chain of Thought instructions
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

        response = client.chat.completions.create(
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
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"Error in analyze_food_image: {e}")
        import traceback
        traceback.print_exc()

        # Return the specific error message to the frontend for debugging
        return {
            "error": str(e),
            "items": [],
            "total_analysis": {
                "summary": "Analysis failed. Error: " + str(e),
                "suggestion": "Please check the backend logs or try a different image.",
                "confidence": 0
            }
        }
    finally:
        # Clean up temporary converted file if it exists
        if converted_path and os.path.exists(converted_path):
            try:
                os.remove(converted_path)
                print(f"Cleaned up converted file: {converted_path}")
            except Exception as cleanup_err:
                print(f"Error cleaning up {converted_path}: {cleanup_err}")
