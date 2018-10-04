"""
Text fixtures for module dot_repository.api.

Run a single test by using the flag -v:

FLASK_ENV=testing python -m pytest -s -v ./tests/dot_repository/test_api.py::test_manage_dotflows

"""
import json


def test_authentication_ok(client):
    """GET /api/system/login."""
    response = client.get('/api/system/login?username=test&password=test')
    data = json.loads(response.data)
    assert response.status_code == 200
    assert data['status'] == 'success'
    assert data['token'] != ''


def test_authentication_with_wrong_credentials(client):
    """GET /api/system/login."""
    response = client.get('/api/system/login?username=wrong&password=wrong')
    data = json.loads(response.data)
    assert response.status_code == 401
    assert data['status'] == 'fail'


def test_authentication_with_validation_errors(client):
    """GET /api/system/login."""
    response = client.get('/api/system/login')
    data = json.loads(response.data)
    assert response.status_code == 400
    assert len(data['validation_errors']) == 2


def test_logout(client):
    """DELETE /api/system/login."""
    response = client.delete('/api/system/login?username=test')
    data = json.loads(response.data)
    assert response.status_code == 200
    assert data['status'] == 'success'


def test_restrict_access_to_protected_resources(client):
    """GET /api/dotbot."""
    response = client.get('/api/dotbot')
    assert response.status_code == 401


def test_allow_access_with_authentication_token(client, test_token):
    """GET /api/dotbot."""
    response = client.get('/api/dotbot?token=' + test_token)
    assert response.status_code == 200


def test_manage_dotbots(client, test_token):
    """Test dotbots."""
    # No dotbots
    response = client.get('/api/dotbot?token=' + test_token)
    data = json.loads(response.data)
    assert response.status_code == 200
    assert b'[]' in response.data

    # Create dotbots
    dotbot_names = ['one', 'two', 'three']
    for dotbot_name in dotbot_names:
        # insert dotbots
        json_body = {
            "id": 0,
            "name": dotbot_name,
            "status": "enabled",
            "modes": [],
            "channels": []
        }
        response = client.post('/api/dotbot/0?token=' + test_token, json=json_body)
        data = json.loads(response.data)
        assert response.status_code == 200
        assert data['name'] == dotbot_name
        assert data['id']
        # Update dotbots
        json_body['id'] = data['id']
        json_body['name'] = data['name'] + ' updated'
        response = client.post('/api/dotbot/' + data['id'] +
                               '?token=' + test_token, json=json_body)
        data = json.loads(response.data)
        assert response.status_code == 200
        assert data['name'] == dotbot_name + ' updated'
        # Delete dotbot named "one updated"
        if data['name'] == 'one updated':
            response = client.delete('/api/dotbot/' + data['id'] +
                                     '?token=' + test_token)
        assert response.status_code == 200

    # List active dotbots
    response = client.get('/api/dotbot?token=' + test_token)
    data = json.loads(response.data)
    assert response.status_code == 200
    assert len(data) == 2

    # Get a single dotbot
    dotbot_name = data[0]['name']
    dotbot_id = data[0]['id']
    response = client.get('/api/dotbot/' + dotbot_id +
                          '?token=' + test_token)
    data = json.loads(response.data)
    assert response.status_code == 200
    assert data['name'] == dotbot_name

    # Try to get a dotbot that doesn't exist.
    response = client.get('/api/dotbot/' + ("ab" * 12) +
                          '?token=' + test_token)
    assert response.status_code == 200
    assert b'{}' in response.data


def test_manage_dotflows(client, test_token):
    """Test dotflows."""
    # Try to list dotflows from a dotbot that doesn't exist.
    response = client.get('/api/dotbot/' + ("ab" * 12) + '/dotflow' +
                          '?token=' + test_token)
    assert response.status_code == 404
    assert b'DotBot not found' in response.data

    # Create a dotbot
    dot_bot = {
        "id": 0,
        "name": "test dotbot",
        "dotbot": {
            "status": "enabled",
            "modes": [],
            "channels": []
        }
    }
    response = client.post('/api/dotbot/0?token=' + test_token, json=dot_bot)
    data = json.loads(response.data)
    assert response.status_code == 200
    dotbot_id = data['id']

    # Try to add a dotflow to an inexistent dotbot
    dot_flow = {
        "dotbot_id": ("ab" * 12),
        "name": "test dotflow",
        "dotflow_id": 0,
        "dotflow": {}
    }
    response = client.post('/api/dotflow/0?token=' + test_token, json=dot_flow)
    data = json.loads(response.data)
    assert response.status_code == 404
    assert b'DotBot not found' in response.data

    # Add a dotflow to the dotbot
    dot_bot = {
        "dotbot_id": dotbot_id,
        "name": "test dotflow",
        "dotflow_id": 0,
        "dotflow": {}
    }
    response = client.post('/api/dotflow/0?token=' + test_token, json=dot_bot)
    data = json.loads(response.data)
    assert response.status_code == 200
    assert data['name'] == "test dotflow"
    assert data['id']

    # Update the dotflow
    dotflow_id = data['id']
    dot_bot['name'] = data['name'] + ' updated'
    response = client.post('/api/dotflow/' + dotflow_id +
                           '?token=' + test_token, json=dot_bot)
    data = json.loads(response.data)
    assert response.status_code == 200
    assert data['name'] == "test dotflow updated"

    # List dotflows in dotbot
    response = client.get('/api/dotbot/' + dotbot_id + '/dotflow' +
                          '?token=' + test_token)
    data = json.loads(response.data)
    assert response.status_code == 200
    assert len(data) == 1

    # Get dotflow by ID
    response = client.get('/api/dotflow/' + dotflow_id +
                          '?token=' + test_token, json=dot_bot)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['name'] == "test dotflow updated"

    # Delete dotflow
    response = client.delete('/api/dotflow/' + dotflow_id +
                             '?token=' + test_token, json=dot_bot)
    data = json.loads(response.data)
    assert response.status_code == 200
    assert b'{}' in response.data
    response = client.get('/api/dotflow/' + dotflow_id +
                          '?token=' + test_token, json=dot_bot)
    assert response.status_code == 200
    assert b'{}' in response.data
