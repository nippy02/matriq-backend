import os
from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

os.environ['USE_SQLITE_FOR_TESTS'] = '1'
os.environ['ENABLE_REAL_MODEL'] = '0'
os.environ['DATABASE_URL'] = 'sqlite:////tmp/matriq_test_ai.db'

from app.main import app


def _login(client, email, password):
    res = client.post('/api/auth/login', json={'email': email, 'password': password})
    assert res.status_code == 200, res.text
    return res.json()['access_token']


def _image(color, size=(320, 320)):
    bio = BytesIO()
    Image.new('RGB', size, color).save(bio, format='PNG')
    bio.seek(0)
    return bio


def test_classify_and_validate_flow():
    with TestClient(app) as client:
        tech_token = _login(client, 'jon@matriq.com', 'tech123')
        senior_token = _login(client, 'senior@matriq.com', 'senior123')

        res = client.post(
            '/api/classify',
            headers={'Authorization': f'Bearer {tech_token}'},
            files={'image': ('black.png', _image((0, 0, 0)), 'image/png')},
            data={'client_name': 'Client B', 'project_id': 'P-101', 'branch_id': '1'},
        )
        assert res.status_code == 200, res.text
        payload = res.json()['classification']
        assert payload['decision'] in {'AUTO_ACCEPTED', 'MANUAL_REVIEW_QUEUE', 'MANDATORY_OVERRIDE'}

        if payload['manual_review_queue'] is None:
            res = client.post(
                '/api/classify',
                headers={'Authorization': f'Bearer {tech_token}'},
                files={'image': ('gray.png', _image((20, 20, 20)), 'image/png')},
                data={'client_name': 'Client C', 'project_id': 'P-102', 'branch_id': '1'},
            )
            assert res.status_code == 200, res.text
            payload = res.json()['classification']

        review_case = payload['manual_review_queue']
        assert review_case is not None

        reviews = client.get('/api/reviews', headers={'Authorization': f'Bearer {senior_token}'})
        assert reviews.status_code == 200, reviews.text
        assert any(item['review_case_id'] == review_case['review_case_id'] for item in reviews.json())

        val = client.post(
            '/api/validate',
            headers={'Authorization': f'Bearer {senior_token}'},
            json={
                'review_case_id': review_case['review_case_id'],
                'final_label': 'concrete',
                'justification': 'Manual override test',
            },
        )
        assert val.status_code == 200, val.text
        dashboard = client.get('/api/dashboard', headers={'Authorization': f'Bearer {senior_token}'})
        assert dashboard.status_code == 200, dashboard.text
