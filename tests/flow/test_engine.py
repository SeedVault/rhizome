"""Unit tests for module flow.engine"""
from tests.bbot.conftest import create_test_bot
from bbot.core import Engine

def test_commands():
    """Create bot."""
    bot = create_test_bot(None, "flow")
    request = Engine.create_request(":unknown_command", "joe", '7', '1')
    response = bot.get_response(request)
    assert response["output"]["text"].startswith('Unknown command.')
    request = Engine.create_request(":help", "joe", '7', '1')
    response = bot.get_response(request)
    assert response["output"]["text"].startswith('Commands:')
    request = Engine.create_request(":reset all", "joe", '7', '1')
    response = bot.get_response(request)
    assert response["output"]["text"].startswith('User data')
