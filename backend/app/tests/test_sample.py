import os
from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

os.environ['USE_SQLITE_FOR_TESTS'] = '1'
os.environ['ENABLE_REAL_MODEL'] = '0'
os.environ['DATABASE_URL'] = 'sqlite:////tmp/matriq_test_sample.db'

from app.main import app


def _login(client, email, password):
    res = client.post('/api/auth/login', json={'email': email, 'password': password})
    assert res.status_code == 200
    return res.json()['access_token']


def _img_bytes(color=(180, 180, 180)):
    bio = BytesIO()
    Image.new('RGB', (300, 300), color).save(bio, format='PNG')
    bio.seek(0)
    return bio


def test_sample_listing_after_classification():
    with TestClient(app) as client:
        token = _login(client, 'jon@matriq.com', 'tech123')
        image = _img_bytes((190, 190, 190))
        res = client.post(
            '/api/classify',
            headers={'Authorization': f'Bearer {token}'},
            files={'image': ('sample.png', image, 'image/png')},
            data={'client_name': 'Client A', 'project_id': 'P-100', 'branch_id': '1'},
        )
        assert res.status_code == 200, res.text
        samples = client.get('/api/samples', headers={'Authorization': f'Bearer {token}'})
        assert samples.status_code == 200, samples.text
        assert len(samples.json()) >= 1
