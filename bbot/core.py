"""Define a plugin architecture to create bots."""
from __future__ import annotations # see https://www.python.org/dev/peps/pep-0563/
import abc
import os
import importlib
import logging
import logging.config
import datetime
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
    def load_plugin(plugin_settings: dict, dotbot: dict=None, parent: object=None) -> Any:
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
                    plugin.__setattr__(attr_name, Plugin.load_plugin(attr_config, dotbot, plugin))
                else: # many instances
                    instances = {}
                    for key, values in attr_config.items():
                        if "plugin_class" in values:
                            instances[key] = Plugin.load_plugin(values, dotbot, plugin)

                    plugin.__setattr__(attr_name, instances)
        #@TODO we might change this to run directly on _init_ with a callback
        if hasattr(plugin, 'init'):            
            plugin.init(parent)
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
class BBotCore(Plugin, metaclass=abc.ABCMeta):
    """Abstract base class for chatbot engines."""

    SIGNAL_GET_RESPONSE_AFTER = 'get_response_after'
    SIGNAL_CALL_BBOT_FUNCTION_AFTER = 'call_function_after'
    SIGNAL_TEMPLATE_RENDER = 'template_render'

    def __init__(self, config: dict, dotbot: dict) -> None:
        """
        Initialize the chatbot engine.

        :param config: Configuration values for the instance.
        """
        #super(ChatbotEngine, self).__init__(config)

        self.config = config
        self.dotbot = dotbot

        self.dotdb = None
        self.logger = None
        self.cache = None
        self.extensions = []
        self.pipeline = []

        self.is_fallback = False
        self.user_id = ''
        self.bot_id = ''
        self.org_id = ''
        self.logger_level = ''
        self.request = {}
        self.executed_functions = []
        self.bot = None

        self.bbot_functions_map = {}    # Registered template functions

        self.bbot = BBotFunctionsProxy(self)

        smokesignal.clear_all() # this shouldnt be needed. @TODO build the whole obj hierarchy, store it in a static var and decouple request session data

    def init(self, none):
        """
        Initilize BBot core. Load and init chatbot engine
        """

        # Init core
        #self.extensions[0].init(self)      
       
        # Instatiate chatbot engine and initialize
        config_path = os.path.abspath(os.path.dirname(__file__) + "/../instance")
        config = load_configuration(config_path, "BBOT_ENV")
        
        self.bot = Plugin.load_plugin(config["chatbot_engines"][self.dotbot['chatbotEngine']], self.dotbot, self)               
        self.logger = BBotLoggerAdapter(logging.getLogger('core'), self, self.bot, 'core')        
        self.bot.core = self

        #self.bot.init()

    def register_function(self, function_name: str, callback: dict):
        """
        Register template custom function mapped to its plugin method.

        :param function_name: .flow function name
        :param callback: callable array class/method of plugin method
        """
        
        self.bbot_functions_map[function_name] = callback

    def resolve_arg(self, arg, f_type):
        """
        """
        return arg

    def get_response(self, request: dict) -> dict:
        """
        Return a response based on the input data.

        :param request: A dictionary with input data.
        :return: A response to the input data.
        """

        self.response = self.bot.get_response(request)
        self.process_pipeline()
        smokesignal.emit(BBotCore.SIGNAL_GET_RESPONSE_AFTER, bbot_response = self.response)        
        self.logger.debug('Response from bbot metaengine: ' + str(self.response))
        return self.response

    def process_pipeline(self):
        """
        Executes all processes listed in the pipeline configuration
        """
        for p in self.pipeline:
            self.pipeline[p].process()
        
    @staticmethod
    def create_bot(config: dict, dotbot: dict={}):
        """
        Create a bot.

        :param config: Configuration settings.
        :param chatbot_engine_name: Name of engine to create. If ommited,
                            defaults to value specified under the key
                            "bbot.default_chatbot_engine" in configuration file.
        :return: Instance of BBotCore class.
        """
        chatbot_engine = dotbot['chatbotEngine']
        
        if chatbot_engine not in config["chatbot_engines"]:
            raise ChatbotEngineNotFoundError()

        bot = Plugin.load_plugin(config["bbot_core"], dotbot)           
        return bot

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

    def get_all_texts_from_output(bbot_response: dict) -> str:
        """Returns all concatenated texts from a bbot response"""
        texts = ''

        for r in bbot_response:
            response_type = list(r.keys())[0]
            if response_type == 'text':
                texts += r['text'] + '.\n' # @TODO improve this
        return texts


    def extensions_cache(func):
        """
        Decorator to apply cache to extensions
        @TODO add ttl 5min
        """
        def function_wrapper(self, args, f_type):
            # key = botid_methodname_arg0_arg1_arg2
            # adds args only if they are string, integer or boolean (avoiding nonhashagle values [even in nested values])
            key = self.core.bot_id + "_" + func.__name__
            for arg in args:
                if isinstance(arg, (str, int, bool)):
                    key += "_" + str(arg)
            cached = self.core.cache.get(key)
            if cached is None:
                value = func(self, args, f_type)
                self.core.cache.set(key, value)
                return value
            else:
                self.logger.debug('Found cached value!')
                return cached

        return function_wrapper


@Plugin.register
class ChatbotEngine(Plugin, metaclass=abc.ABCMeta):
    """Abstract base class for chatbot engines."""

    @abc.abstractmethod
    def __init__(self, config: dict, dotbot: dict) -> None:
        """
        Initialize the instance.

        :param config: Configuration values for the instance.
        """
        self.core = None        

        self.dotbot = dotbot
        self.config = config
        self.bot_id = ''
        self.user_id = ''
        self.logger_level = ''
        self.is_fallback = False
        
    @abc.abstractmethod
    def get_response(self, request: dict) -> dict:
        """
        Get response based on the request
        """

    @abc.abstractmethod
    def init(self) -> None:
        """
        Initializes chatbot engine with config and dotbot loaded
        """

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
class Extension(Plugin, metaclass=abc.ABCMeta):
    """Abstract base class for extensions."""

    @abc.abstractmethod
    def __init__(self, config: dict) -> None:
        """
        Initialize the extension.

        :param config: Configuration values for the instance.
        """

    @abc.abstractmethod
    def init(self):
        """        
        """
        
    @abc.abstractmethod
    def register_activity(self, function_name, response):
        """        
        """        


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



class BBotLoggerAdapter(logging.LoggerAdapter):
    """
    Custom Logger Adapter to add some context data and more control on DotFlow extensions logging behavior
    """

    def __init__(self, logger, module: object, bot, mod_name=''):
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
            self.setLevel(module.logger_level)

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

        bot_id = ''
        try:
            bot_id = self.bot.dotbot['id']
        except AttributeError:
            pass

        bot_name = ''
        try:
            bot_name = self.bot.dotbot['name']
        except AttributeError:
            pass

        user_id = ''
        try:
            user_id = self.bot.user_id
        except AttributeError:
            pass

        user_ip = ''
        try:
            user_ip = self.bot.user_ip
        except AttributeError:
            pass

        extra = {
            'bot_id': bot_id,
            'bot_name': bot_name,
            'user_id': user_id,
            'user_ip': user_ip
        }

        kwargs["extra"] = extra
        return msg, kwargs


class BBotFunctionsProxy:
    """
    This class is a proxy to call BBot functions in a easy way
    Ex:
    bbot = BBotFunctionsProxy()
    bbot.fname()
    """

    RESPONSE_OK = 1
    RESPONSE_ERROR = 2

    def __init__(self, core: BBotCore):
        self.core = core

    def __getattr__(self, name):
        def wrapper(*args, **kwargs):
            if name in self.core.bbot_functions_map:
                return self.call_bbot_function(name, args, '')
        return wrapper

    def call_bbot_function(self, func_name: str, args: list, f_type: str):
        """
        Executes a BBot function

        :param func_name: Name of the function
        :param args: List with arguments
        :param f_type: Function Type
        :return:
        """
        self.core.logger.debug('Calling bbot function "' + func_name + '" with args ' + str(args))
        start = datetime.datetime.now()
        if func_name in self.core.bbot_functions_map:
            response = getattr(self.core.bbot_functions_map[func_name]['object'],
                               self.core.bbot_functions_map[func_name]['method'])(args, f_type)
        else:
            # @TODO for now we just send a warning to the log. We will make it an Exception later
            self.core.logger.warning(func_name + '" it\'s not registered')
            response = None
        end = datetime.datetime.now()
        self.core.logger.debug('Response: ' + str(response))

        # Adds debug information about the executed function
        self.core.executed_functions.append({
            'function': func_name,
            'args': args,
            'return': response,
            'responseTime': int((end - start).total_seconds() * 1000)
        })

        smokesignal.emit(BBotCore.SIGNAL_CALL_BBOT_FUNCTION_AFTER, name=func_name, response_code=BBotFunctionsProxy.RESPONSE_OK)

        return response