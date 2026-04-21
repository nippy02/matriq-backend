import os
from fastapi.testclient import TestClient

os.environ['USE_SQLITE_FOR_TESTS'] = '1'
os.environ['ENABLE_REAL_MODEL'] = '0'
os.environ['DATABASE_URL'] = 'sqlite:////tmp/matriq_test_samples_post.db'

from app.main import app


def _login(client, email, password):
    res = client.post('/api/auth/login', json={'email': email, 'password': password})
    assert res.status_code == 200, res.text
    return res.json()['access_token']


def test_samples_post_route():
    with TestClient(app) as client:
        token = _login(client, 'jon@matriq.com', 'tech123')
        res = client.post(
            '/api/samples',
            headers={'Authorization': f'Bearer {token}'},
            json={
                'client_name': 'Posted Sample',
                'project_id': 'POST-200',
                'branch_id': 1,
                'material_type': 'concrete',
                'image_path': 'uploads/posted.png',
                'ai_predicted_label': 'Concrete',
                'ai_confidence_score': 0.91,
                'decision': 'AUTO_ACCEPTED',
                'device_metadata': {'source': 'unit-test'},
            },
        )
        assert res.status_code == 200, res.text
        payload = res.json()
        assert payload['client_name'] == 'Posted Sample'
        assert payload['decision'] == 'Auto-Accepted'
