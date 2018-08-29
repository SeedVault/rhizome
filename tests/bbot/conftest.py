"""Text fixtures for module bbot."""
import os
import pytest
from bbot.config import load_configuration
from bbot.core import create_bot, ChatbotEngine

@pytest.fixture
def get_configuration_path() -> str:
    """Return the path of configuration files."""
    return os.path.abspath(os.path.dirname(__file__) + "/../../instance")


@pytest.fixture
def create_test_bot(config_settings: dict,
                    chatbot_engine_name: str = "") -> ChatbotEngine:
    """Create a bot for testing."""
    if not config_settings:
        config_settings = load_configuration(get_configuration_path(),
                                             "BBOT_ENV", "testing")
    return create_bot(config_settings, chatbot_engine_name)
