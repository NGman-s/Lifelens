import requests
import json
import os

# Configuration
API_URL = "http://localhost:8080/api/v1/vision/analyze"
TEST_IMAGE_PATH = "sample_food.jpg" # Make sure to put a sample image here
USER_CONTEXT = {
    "age": 25,
    "goal": "muscle_gain",
    "health_conditions": ["Nut Allergy"]
}

def test_analyze():
    if not os.path.exists(TEST_IMAGE_PATH):
        print(f"Error: {TEST_IMAGE_PATH} not found. Please provide a sample image for testing.")
        return

    print(f"Sending request to {API_URL}...")

    files = {
        'file': (os.path.basename(TEST_IMAGE_PATH), open(TEST_IMAGE_PATH, 'rb'), 'image/jpeg')
    }
    data = {
        'user_context': json.dumps(USER_CONTEXT)
    }

    try:
        response = requests.post(API_URL, files=files, data=data)
        if response.status_code == 200:
            print("Success! Analysis Result:")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        else:
            print(f"Failed with status code: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    test_analyze()
