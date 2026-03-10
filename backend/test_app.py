import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))

import main


class LifeLensApiTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_uploads_dir = main.UPLOADS_DIR
        self.original_max_upload_bytes = main.MAX_UPLOAD_SIZE_BYTES
        self.original_max_upload_mb = main.MAX_UPLOAD_SIZE_MB

        main.UPLOADS_DIR = Path(self.temp_dir.name)
        for route in main.app.routes:
            if getattr(route, 'name', None) == 'uploads':
                route.app.directory = str(main.UPLOADS_DIR)

        self.client_context = TestClient(main.app)
        self.client = self.client_context.__enter__()

    def tearDown(self):
        self.client_context.__exit__(None, None, None)
        main.UPLOADS_DIR = self.original_uploads_dir
        main.MAX_UPLOAD_SIZE_BYTES = self.original_max_upload_bytes
        main.MAX_UPLOAD_SIZE_MB = self.original_max_upload_mb
        for route in main.app.routes:
            if getattr(route, 'name', None) == 'uploads':
                route.app.directory = str(main.UPLOADS_DIR)
        self.temp_dir.cleanup()

    def _make_image_bytes(self, image_format='PNG'):
        image = Image.new('RGB', (12, 12), color=(255, 120, 0))
        buffer = io.BytesIO()
        image.save(buffer, format=image_format)
        return buffer.getvalue()

    def _default_user_context(self):
        return {
            'age': 25,
            'goal': 'muscle_gain',
            'health_conditions': ['Nut Allergy']
        }

    def _valid_analysis_result(self):
        return {
            'main_name': '鸡胸肉沙拉',
            'total_calories': 320,
            'total_traffic_light': 'green',
            'warning_message': '',
            'thought_process': '识别为一份鸡胸肉沙拉。',
            'items': [
                {
                    'name': '鸡胸肉沙拉',
                    'calories': 320,
                    'unit': 'kcal',
                    'nutrition_tags': ['高蛋白', '低脂'],
                    'traffic_light': 'green'
                }
            ],
            'total_analysis': {
                'summary': '高蛋白低脂。',
                'suggestion': '适合控脂期食用。',
                'confidence': 0.91
            }
        }

    def test_health_endpoint(self):
        response = self.client.get('/api/v1/health')

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['status'], 'ok')
        self.assertEqual(payload['service'], 'lifelens-api')

    def test_rejects_invalid_file_type(self):
        response = self.client.post(
            '/api/v1/vision/analyze',
            files={
                'file': ('bad.svg', io.BytesIO(b'<svg></svg>'), 'image/svg+xml')
            },
            data={'user_context': json.dumps(self._default_user_context())}
        )

        self.assertEqual(response.status_code, 415)
        payload = response.json()
        self.assertIn('trace_id', payload)
        self.assertEqual(list(main.UPLOADS_DIR.iterdir()), [])

    def test_rejects_oversized_upload(self):
        main.MAX_UPLOAD_SIZE_BYTES = 8
        main.MAX_UPLOAD_SIZE_MB = 1

        response = self.client.post(
            '/api/v1/vision/analyze',
            files={
                'file': ('large.jpg', io.BytesIO(b'123456789'), 'image/jpeg')
            },
            data={'user_context': json.dumps(self._default_user_context())}
        )

        self.assertEqual(response.status_code, 413)
        self.assertIn('上传图片不能超过', response.json()['message'])
        self.assertEqual(list(main.UPLOADS_DIR.iterdir()), [])

    @patch.object(main, 'analyze_food_image', new_callable=AsyncMock)
    def test_analyze_success_returns_accessible_image_url(self, analyze_mock):
        analyze_mock.return_value = self._valid_analysis_result()

        response = self.client.post(
            '/api/v1/vision/analyze',
            files={
                'file': ('meal.png', io.BytesIO(self._make_image_bytes('PNG')), 'image/png')
            },
            data={'user_context': json.dumps(self._default_user_context())}
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        image_url = payload['data']['image_url']
        saved_path = main.UPLOADS_DIR / Path(image_url).name
        self.assertTrue(saved_path.exists())

        image_response = self.client.get(image_url)
        self.assertEqual(image_response.status_code, 200)
        self.assertTrue(image_response.content)

    @patch.object(main, 'analyze_food_image', new_callable=AsyncMock)
    def test_analyze_upstream_error_is_sanitized_and_cleans_upload(self, analyze_mock):
        analyze_mock.side_effect = main.VisionServiceError('图像分析服务暂时不可用，请稍后重试')

        response = self.client.post(
            '/api/v1/vision/analyze',
            files={
                'file': ('meal.png', io.BytesIO(self._make_image_bytes('PNG')), 'image/png')
            },
            data={'user_context': json.dumps(self._default_user_context())}
        )

        self.assertEqual(response.status_code, 502)
        payload = response.json()
        self.assertEqual(payload['message'], '图像分析服务暂时不可用，请稍后重试')
        self.assertIn('trace_id', payload)
        self.assertEqual(list(main.UPLOADS_DIR.iterdir()), [])

    @patch.object(main, 'generate_alternative_suggestions', new_callable=AsyncMock)
    def test_generate_alternatives_success(self, alternatives_mock):
        alternatives_mock.return_value = {
            'ordering_hint': '换成凉拌鸡胸肉。',
            'cooking_hint': '少油少盐。'
        }

        response = self.client.post(
            '/api/v1/vision/generate-alternatives',
            json={
                'analysis_result': {'main_name': '炸鸡', 'total_traffic_light': 'red'},
                'user_context': self._default_user_context()
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['ordering_hint'], '换成凉拌鸡胸肉。')

    @patch.object(main, 'generate_alternative_suggestions', new_callable=AsyncMock)
    def test_generate_alternatives_error_branch(self, alternatives_mock):
        alternatives_mock.side_effect = main.VisionServiceError('爆改建议服务暂时不可用，请稍后重试')

        response = self.client.post(
            '/api/v1/vision/generate-alternatives',
            json={
                'analysis_result': {'main_name': '炸鸡', 'total_traffic_light': 'red'},
                'user_context': self._default_user_context()
            }
        )

        self.assertEqual(response.status_code, 502)
        payload = response.json()
        self.assertEqual(payload['message'], '爆改建议服务暂时不可用，请稍后重试')
        self.assertIn('trace_id', payload)


if __name__ == '__main__':
    unittest.main()
