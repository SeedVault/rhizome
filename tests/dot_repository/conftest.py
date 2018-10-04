"""Text fixtures for module dot_repository."""
import pytest
from dot_repository.api import app, dotdb

@pytest.fixture
def client():
    """A test client for the app."""
    dotdb.restart_from_scratch()
    username = 'test'
    plaintext_password = 'test'
    organization = dotdb.create_organization('test')
    is_admin = 1
    _ = dotdb.create_user(username, plaintext_password, organization, is_admin)
    ctx = app.app_context()
    ctx.push()
    yield app.test_client()
    ctx.pop()


@pytest.fixture
def test_token():
    """Retrieve a token used for testing."""
    _ = dotdb.find_one_organization('it_doesnt_exist')
    result = dotdb.login('test', 'test')
    return result.token
