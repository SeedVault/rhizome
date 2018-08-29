"""Unit tests for module bbot.core"""
import pytest
from tests.bbot.conftest import create_test_bot
from bbot.core import Plugin, ChatbotEngine, ChatbotEngineNotFoundError

class DummyEngine(ChatbotEngine):
    """Dummy engine."""
    def __init__(self, settings: dict) -> None:
        self.name = ''
        self.loader = None
        self.extensions = {} # type: dict
        super().__init__(settings)

    def get_response(self, request: dict) ->dict:
        """
        Return a response based on the input data.

        :param request: A dictionary with input data.
        :return: A response to the input data.
        """
        return ChatbotEngine.create_response("dummy")



class DummyPlugin(Plugin): # pylint: disable=too-few-public-methods
    """Dummy plugin."""
    def __init__(self, settings: dict) -> None:
        self.name = ''
        super().__init__(settings)


def test_create_plugin_dynamically():
    """Create plugin dynamically."""
    settings = {"plugin_class": "tests.bbot.test_core.DummyPlugin",
                "name": "dummy plugin"}
    instance = Plugin.load_plugin(settings)
    assert instance.name == settings["name"]


def test_engine_not_found_error():
    """Engine not found error."""
    with pytest.raises(ChatbotEngineNotFoundError):
        _ = create_test_bot({}, "IT_DOESNT_EXIST")


def test_create_bot():
    """Create bot."""
    config_settings = \
    {
        "bbot": {
            "default_chatbot_engine": "dummy",
            "chatbot_engines": {
                "dummy": {
                    "plugin_class": "tests.bbot.test_core.DummyEngine",
                    "name": "engine",
                    "loader": {
                        "plugin_class": "tests.bbot.test_core.DummyPlugin",
                        "name": "loader"
                    },
                    "extensions": {
                        "dummy_plugin_1": {
                            "plugin_class": "tests.bbot.test_core.DummyPlugin",
                            "name": "extension 1"
                        },
                        "dummy_plugin_2": {
                            "plugin_class": "tests.bbot.test_core.DummyPlugin",
                            "name": "extension 2"
                        }
                    }
                }
            }
        },
        "logging": {
            "version": 1
        }
    }
    bot = create_test_bot(config_settings)
    info = config_settings["bbot"]["chatbot_engines"]["dummy"]
    assert bot.name == info["name"]
    assert bot.loader.name == info["loader"]["name"]
    assert bot.extensions["dummy_plugin_2"].name == \
           info["extensions"]["dummy_plugin_2"]["name"]
    request = ChatbotEngine.create_request("dummy", "Joe")
    response = bot.get_response(request)
    assert response['output']['text'] == "dummy"
