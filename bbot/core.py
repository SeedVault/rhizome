"""Define a plugin architecture to create bots."""
import abc
import importlib
import logging
import logging.config
from typing import Any

class Plugin(metaclass=abc.ABCMeta):
    """Generic plugin."""

    def __init__(self, config: dict) -> None:
        """
        Initialize the plugin.

        :param config: Configuration values for the instance.
        """


    @staticmethod
    def load_plugin(plugin_settings: dict) -> Any:
        """
        Create a new instance of a plugin dynamically.

        This method creates a new instance of a plugin and set its
        internal attributes and dependencies recursively.

        :param plugin_settings: Dictionary with initialization data.
        :return: An instance of the class defined in plugin_settings
        """
        parts = plugin_settings["plugin_class"].strip().split(".")
        class_name = parts.pop()
        package_name = ".".join(parts)
        module = importlib.import_module(package_name)
        dynamic_class = getattr(module, class_name)
        plugin = dynamic_class(plugin_settings)
        for attr_name in vars(plugin):
            if attr_name in plugin_settings:
                attr_config = plugin_settings[attr_name]
                if not isinstance(attr_config, dict): # single value
                    plugin.__setattr__(attr_name, attr_config)
                elif  "plugin_class" in attr_config:  # single instance
                    plugin.__setattr__(attr_name,
                                       Plugin.load_plugin(attr_config))
                else: # many instances
                    instances = {}
                    for key, values in attr_config.items():
                        if "plugin_class" in values:
                            instances[key] = Plugin.load_plugin(values)
                    plugin.__setattr__(attr_name, instances)
        return plugin


@Plugin.register
class Engine(Plugin, metaclass=abc.ABCMeta):
    """Abstract base class for chatbot engines."""

    @abc.abstractmethod
    def __init__(self, config: dict) -> None:
        """
        Initialize the engine.

        :param config: Configuration values for the instance.
        """
        self.logger = logging.Logger('bbot')  # type: logging.Logger
        super(Engine, self).__init__(config)


    @abc.abstractmethod
    def get_response(self, request: dict) -> dict:
        """
        Return a response based on the input data.

        :param request: A dictionary with input data.
        :return: A response to the input data.
        """
        _ = request
        return {}


    @staticmethod
    def create_request(input_text: str, user_id: str, bot_id: str = "",
                       org_id: str = "") -> dict:
        """
        Create a base request.

        :param input_text: Input text
        :param user_id: User ID
        :param bot_id: Bot ID
        :param org_id: Organization ID
        :return: A dictionary with the given data
        """
        return {"user_id": user_id, "bot_id": bot_id, "org_id": org_id,
                "input": {"text": input_text}}


    @staticmethod
    def create_response(output_text: str) -> dict:
        """
        Create a base response.

        :param output_text: Output text
        :return: A dictionary with the given data
        """
        return {"output": {"text": output_text}}



class EngineNotFoundError(Exception):
    """Engine not found."""


@Plugin.register
class ConfigReader(Plugin, metaclass=abc.ABCMeta):
    """Abstract base class for configuration readers."""

    @abc.abstractmethod
    def __init__(self, config: dict) -> None:
        """
        Initialize the config reader.

        :param config: Configuration values for the instance.
        """
        super(ConfigReader, self).__init__(config)


    @abc.abstractmethod
    def read(self) ->dict:
        """
        Return a dictionary with configuration settings.

        :return: Configuration settings.
        """
        return {}

def create_bot(config: dict, engine_name: str = "") -> Engine:
    """
    Create a bot.

    :param config: Configuration settings.
    :param engine_name: Name of engine to create. If ommited, defaults to value
                        specified under the key "bbot.default_engine" in the
                        configuration file.
    :return: Instance of a subclass of Engine.
    """
    if not engine_name:
        engine_name = config["bbot"]["default_engine"]
    if not engine_name in config["bbot"]["engines"]:
        raise EngineNotFoundError()
    bot = Plugin.load_plugin(config["bbot"]["engines"][engine_name])
    logging.config.dictConfig(config['logging'])
    bot.logger = logging.getLogger(engine_name)
    return bot
