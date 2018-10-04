"""Define a plugin architecture to create bots."""
from __future__ import annotations # see https://www.python.org/dev/peps/pep-0563/
import abc
import importlib
import logging
import logging.config
import smokesignal

from typing import Any


class Plugin(metaclass=abc.ABCMeta):
    """Generic plugin."""

    def __init__(self, config: dict) -> None:
        """
        Initialize the plugin.

        :param config: Configuration values for the instance.
        """


    @staticmethod
    def load_plugin(plugin_settings: dict, dotbot: dict=None) -> Any:
        """
        Create a new instance of a plugin dynamically.

        This method creates a new instance of a plugin and set its
        internal attributes and dependencies recursively.

        :param plugin_settings: Dictionary with initialization data.
        :return: An instance of the class defined in plugin_settings
        """
        plugin = Plugin.get_class_from_fullyqualified(plugin_settings['plugin_class'])(plugin_settings, dotbot)
        for attr_name in vars(plugin):
            if attr_name in plugin_settings:
                attr_config = plugin_settings[attr_name]
                if not isinstance(attr_config, dict): # single value
                    plugin.__setattr__(attr_name, attr_config)
                elif  "plugin_class" in attr_config:  # single instance
                    plugin.__setattr__(attr_name, Plugin.load_plugin(attr_config))
                else: # many instances
                    instances = {}
                    for key, values in attr_config.items():
                        if "plugin_class" in values:
                            instances[key] = Plugin.load_plugin(values)

                    plugin.__setattr__(attr_name, instances)
        return plugin

    @staticmethod
    def get_class_from_fullyqualified(setting_class):
        """
        Parses plugin_class entry from config settings, imports and returns the class
        :param setting_class: Fully qualified classname
        :return: imported class
        """
        parts = setting_class.strip().split(".")
        class_name = parts.pop()
        package_name = ".".join(parts)
        module = importlib.import_module(package_name)
        dynamic_class = getattr(module, class_name)
        return dynamic_class



@Plugin.register
class ChatbotEngine(Plugin, metaclass=abc.ABCMeta):
    """Abstract base class for chatbot engines."""

    @abc.abstractmethod
    def __init__(self, config: dict, dotbot: dict) -> None:
        """
        Initialize the chatbot engine.

        :param config: Configuration values for the instance.
        """
        super(ChatbotEngine, self).__init__(config)

        self.dotdb = None
        self.config = {}
        self.dotbot = None
        self.logger = None
        self.is_fallback = False

        self.user_id = ''
        self.bot_id = ''
        self.org_id = ''
        self.request = {}

    @abc.abstractmethod
    def get_response(self, request: dict) -> dict:
        """
        Return a response based on the input data.

        :param request: A dictionary with input data.
        :return: A response to the input data.
        """
        return request


    @staticmethod
    def create_request(chan_input: dict, user_id: str, bot_id: str = "",
                       org_id: str = "") -> dict:
        """
        Create a base request.

        :param chan_input: Input from channel
        :param user_id: User ID
        :param bot_id: Bot ID
        :param org_id: Organization ID
        :return: A dictionary with the given data
        """
        return {"user_id": user_id, "bot_id": bot_id, "org_id": org_id, "input": chan_input}


    @staticmethod
    def create_response(output: dict) -> dict:
        """
        Create a base response.

        :param output: Output from bot engine
        :return: A dictionary with the given data
        """
        return output

    def fallback_bot(self, bot: ChatbotEngine, response: dict) -> dict:
        """
        @TODO this will be called from a pubsub event, so args might change
        Call to fallback bots defined in dotbot when the main bot has a no match o
        or when it doesnt answer or has an invalid response

        :param bot:
        :param response:
        :return:
        """
        if not bot.is_fallback and (response.get('noMatch') or response.get('error')):
            self.logger.debug('Bot engine has a no match. Looking fallback bots')

            # try import bots
            for bot_name in bot.dotbot.get('fallbackBots'):
                self.logger.debug(f'Trying with bot {bot_name}')
                bot_dotbot_container = bot.dotdb.find_dotbot_by_name(bot_name)
                if not bot_dotbot_container:
                    raise Exception(f'Fallback bot not found {bot_name}')
                else:
                    bot_dotbot = bot_dotbot_container.dotbot

                bbot = create_bot(bot.config, bot_dotbot)
                bbot.is_fallback = True
                req = ChatbotEngine.create_request(bot.request['input'], bot.user_id, 1, 1)
                fallback_response = bbot.get_response(req)
                if fallback_response.get('error'):
                    self.logger.error('Fallback bot returned an invalid response. Discarding.')
                    continue
                if not fallback_response.get('noMatch'):
                    self.logger.debug('Fallback bot has a response. Returning this to channel.')
                    return fallback_response

            self.logger.debug('Fallback bot don\'t have a response either. Sending original main bot response if any')
        return response

class ChatbotEngineNotFoundError(Exception):
    """ChatbotEngine not found."""

class ChatbotEngineError(Exception):
    """ChatbotEngine error."""

class ChatbotEngineExtension():
    """Base class for extensions."""
    def __init__(self, config: dict, dotbot: dict) -> None:
        pass

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

@Plugin.register
class TemplateEngine(Plugin, metaclass=abc.ABCMeta):
    """Abstract base class for template engines."""

    @abc.abstractmethod
    def __init__(self, config: dict) -> None:
        """
        Initialize the template engine.

        :param config: Configuration values for the instance.
        """
        super(TemplateEngine, self).__init__(config)


    @abc.abstractmethod
    def render(self) ->str:
        """
        Return a template rendered string.
        """
        return ""


@Plugin.register
class Cache(Plugin, metaclass=abc.ABCMeta):
    """Abstract base class for cache."""

    @abc.abstractmethod
    def __init__(self, config: dict) -> None:
        """
        Initialize the cache.

        :param config: Configuration values for the instance.
        """
        super(Cache, self).__init__(config)


    @abc.abstractmethod
    def set(self) -> None:
        """
        Set cache value
        """
        return ""

    @abc.abstractmethod
    def get(self) ->str:
        """
        Get cached value
        """
        return ""



def create_bot(config: dict, dotbot: dict={}) -> ChatbotEngine:
    """
    Create a bot.

    :param config: Configuration settings.
    :param chatbot_engine_name: Name of engine to create. If ommited,
                        defaults to value specified under the key
                        "bbot.default_chatbot_engine" in configuration file.
    :return: Instance of a subclass of ChatbotEngine.
    """
    chatbot_engine = dotbot['chatbot_engine']
    if not chatbot_engine in config["bbot"]["chatbot_engines"]:
        raise ChatbotEngineNotFoundError()

    bot = Plugin.load_plugin(config["bbot"]["chatbot_engines"][chatbot_engine], dotbot)
    logging.config.dictConfig(config['logging'])
    bot.logger = logging.getLogger('bbot')
    if hasattr(bot, 'init_plugins'):
        bot.init_plugins()
    return bot
