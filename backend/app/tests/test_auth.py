import os
from fastapi.testclient import TestClient

os.environ['USE_SQLITE_FOR_TESTS'] = '1'
os.environ['ENABLE_REAL_MODEL'] = '0'
os.environ['DATABASE_URL'] = 'sqlite:////tmp/matriq_test_auth.db'

from app.main import app


def test_login():
    with TestClient(app) as client:
        res = client.post('/api/auth/login', json={'email': 'jon@matriq.com', 'password': 'tech123'})
        assert res.status_code == 200, res.text
        payload = res.json()
        assert payload['role'] == 'Lab Technician'
        assert payload['access_token']
