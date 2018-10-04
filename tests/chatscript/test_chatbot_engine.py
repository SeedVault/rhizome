"""Unit tests for module chatscript.chat_engine"""
from tests.bbot.conftest import create_test_bot
from bbot.core import ChatbotEngine

def test_create_bot():
    """Create bot."""
    bot = create_test_bot(None, "chatscript")
    assert bot.host
    assert bot.port
    request = ChatbotEngine.create_request("Hello", "Joe")
    response = bot.get_response(request)
    assert response["output"]["text"]


def test_socket_error():
    """Test socket error."""
    bot = create_test_bot(None, "chatscript")
    bot.port = 0
    request = ChatbotEngine.create_request("", "Joe")
    response = bot.get_response(request)
    assert not response
