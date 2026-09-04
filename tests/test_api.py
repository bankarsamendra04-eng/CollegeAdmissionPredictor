import pytest
import json
from app import create_app

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
    })
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

def test_api_stats(client):
    response = client.get('/api/stats')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'colleges_count' in data
    assert 'branches_count' in data
    assert 'historical_records' in data
    assert 'prediction_accuracy_note' in data

def test_api_colleges(client):
    response = client.get('/api/colleges')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'colleges' in data
    assert isinstance(data['colleges'], list)

def test_api_colleges_search(client):
    response = client.get('/api/colleges?search=engineering')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'colleges' in data
    assert isinstance(data['colleges'], list)

def test_api_college_details(client):
    # Mocking id 1 assumes it exists in DB (or mock DB returns something).
    # If DB is empty, this might 404. Let's test standard behaviour.
    # We will just verify it returns either 200 or 404 (if not found in mock/db).
    response = client.get('/api/college/1')
    assert response.status_code in (200, 404)
    if response.status_code == 200:
        data = json.loads(response.data)
        assert 'name' in data
        assert 'city' in data

def test_api_college_details_not_found(client):
    response = client.get('/api/college/99999')
    assert response.status_code == 404

def test_api_branches(client):
    response = client.get('/api/branches')
    assert response.status_code == 200

def test_api_categories(client):
    response = client.get('/api/categories')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'categories' in data
    codes = [c['code'] for c in data['categories']]
    assert 'OPEN' in codes
    assert 'OBC' in codes

def test_api_cutoffs(client):
    response = client.get('/api/cutoffs?college_id=1')
    assert response.status_code == 200

def test_api_analytics(client):
    response = client.get('/api/analytics')
    assert response.status_code == 200

def test_api_predict_valid(client):
    payload = {
        "merit_rank": 1500,
        "percentile": 95.5,
        "category": "OPEN",
        "preferred_branches": ["Computer Science"]
    }
    response = client.post('/api/predict', json=payload)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'recommendations' in data

def test_api_predict_missing_rank(client):
    payload = {
        "percentile": 95.5,
        "category": "OPEN",
        "preferred_branches": ["Computer Science"]
    }
    response = client.post('/api/predict', json=payload)
    assert response.status_code == 400

def test_api_predict_invalid_percentile(client):
    payload = {
        "merit_rank": 1500,
        "percentile": 150.0,  # Invalid
        "category": "OPEN",
        "preferred_branches": ["Computer Science"]
    }
    response = client.post('/api/predict', json=payload)
    assert response.status_code == 400

def test_api_compare(client):
    payload = {
        "college_ids": [1, 2],
        "category": "OPEN"
    }
    response = client.post('/api/compare', json=payload)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'colleges' in data

def test_page_routes(client):
    pages = ['/', '/predictor', '/colleges', '/analytics', '/compare', '/about', '/disclaimer']
    for page in pages:
        res = client.get(page)
        assert res.status_code == 200, f"Page {page} returned {res.status_code}"

def test_api_export(client):
    # First create a prediction
    payload = {
        "merit_rank": 2500,
        "category": "OBC",
        "preferred_branches": ["CSE", "IT"]
    }
    res = client.post('/api/predict', json=payload)
    assert res.status_code == 200
    pred_data = json.loads(res.data)
    pred_id = pred_data.get('prediction_id')
    assert pred_id is not None

    export_res = client.get(f'/api/export/{pred_id}')
    assert export_res.status_code == 200
    assert 'Admission Prediction Report' in export_res.data.decode('utf-8')
