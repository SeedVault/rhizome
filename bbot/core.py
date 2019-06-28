"""Define a plugin architecture to create bots."""
from __future__ import annotations # see https://www.python.org/dev/peps/pep-0563/
import abc
import os
import importlib
import logging
import logging.config
import smokesignal
from logging.config import DictConfigurator
from bbot.config import load_configuration

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
        @TODO this might be replaced by a conditional pipeline

        :param bot:
        :param response:
        :return:
        """
        if not bot.is_fallback and (response.get('noMatch') or response.get('error')):
            self.logger_core.debug('Bot engine has a no match. Looking fallback bots')

            # try import bots
            fbbs = bot.dotbot.get('fallbackBots', [])
            for bot_name in fbbs:
                self.logger_core.debug(f'Trying with bot {bot_name}')
                bot_dotbot_container = bot.dotdb.find_dotbot_by_idname(bot_name)
                if not bot_dotbot_container:
                    raise Exception(f'Fallback bot not found {bot_name}')
                else:
                    bot_dotbot = bot_dotbot_container.dotbot

                config_path = os.path.abspath(os.path.dirname(__file__) + "/../instance")
                config = load_configuration(config_path, "BBOT_ENV")
                bbot = create_bot(config, bot_dotbot)
                bbot.is_fallback = True
                req = ChatbotEngine.create_request(bot.request['input'], bot.user_id, 1, 1)
                fallback_response = bbot.get_response(req)
                if fallback_response.get('error'):
                    self.logger_core.error('Fallback bot returned an invalid response. Discarding.')
                    continue
                if not fallback_response.get('noMatch'):
                    self.logger_core.debug('Fallback bot has a response. Returning this to channel.')
                    return fallback_response
            if fbbs:
                self.logger_core.debug('Fallback bot don\'t have a response either. Sending original main bot response if any')
            else:
                self.logger_core.debug('No fallback defined for this bot. Sending original main bot response if any')
        return response

    def get_all_texts_from_output(bbot_response: dict) -> str:
        """Returns all concatenated texts from a bbot response"""
        texts = ''

        for r in bbot_response:
            response_type = list(r.keys())[0]
            if response_type == 'text':
                texts += r['text'] + '.\n' # @TODO improve this
        return texts


class ChatbotEngineNotFoundError(Exception):
    """ChatbotEngine not found."""


class ChatbotEngineError(Exception):
    """ChatbotEngine error."""


class BBotException(Exception):
    """BBot plugin error."""

    def __init__(self, args):
        self.args = args
        super(BBotException, self).__init__('args: {}'.format(args))

    def __reduce__(self):
        return BBotException, self.args


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
    chatbot_engine = dotbot['chatbotEngine']
    
    if chatbot_engine not in config["bbot"]["chatbot_engines"]:
        raise ChatbotEngineNotFoundError()

    bot = Plugin.load_plugin(config["bbot"]["chatbot_engines"][chatbot_engine], dotbot)
    logging.config.dictConfig(config['logging'])
    bot.logging_config = config['logging']

    bot.logger_core = BBotLoggerAdapter(logging.getLogger('bbot'), bot, bot)
    if hasattr(bot, 'init_engine'):
        bot.init_engine()
    return bot


class BBotLoggerAdapter(logging.LoggerAdapter):
    """
    Custom Logger Adapter to add some context data and more control on DotFlow extensions logging behavior
    """

    def __init__(self, logger, module: object, bot: ChatbotEngine, mod_name=''):
        """

        :param logger:
        :param module:
        :param bot:
        :param mod_name:
        """
        super().__init__(logger, {})

        self.bot = bot
        self.mod_name = mod_name

        if module.logger_level:
            self.setLevel(logging.getLevelName(module.logger_level))

        """ custom handlers dont work
        if module.config.get('logger_handler'):
            df = DictConfigurator(bot.logging_config)
            handler_config = bot.logging_config['handlers'][module.config['logger_handler']]
            self.logger.addHandler(df.configure_handler(handler_config))
        """

    def process(self, msg, kwargs):
        """

        :param msg:
        :param kwargs:
        :return:
        """
        # We need to set extras here because we need bot object ref to get user_id when available (it's not available at extension's init)
        extra = {
            'bot_id': self.bot.dotbot['id'],
            'bot_name': self.bot.dotbot['name'],
            'user_id': getattr(self.bot, 'user_id', '<no user id>'),
            'user_ip': getattr(self.bot, 'user_ip', '<no IP>')
        }

        kwargs["extra"] = extra
        return msg, kwargs
