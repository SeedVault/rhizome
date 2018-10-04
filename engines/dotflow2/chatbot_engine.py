"""BBot engine based on DotFlow2."""
import logging
import smokesignal
from .dotflow2_core_functions import *
from .dotflow2_output import *
from bbot.core import ChatbotEngine


class DotFlow2(ChatbotEngine):
    """BBot engine based on DotFlow2."""

    DOTFLOW2_FUNCTION_PREFIX = '_'  # This should be $, but mongodb does not allow us to use it even using server 4.0

    def __init__(self, config: dict, dotbot: dict) -> None:
        """
        Initialize the plugin.

        :param config: Configuration values for the instance.
        """
        super().__init__(config, dict)

        # internal dotflow2 variables
        self.request = {}  # bbot request
        self.response = {}
        self.config = config
        self.dotbot = dotbot

        #
        self.dotdb = None
        self.plugins = []  # bbot plugins

        self.dotflow2_functions_map = {}
        self.template_functions_map = {}

        #
        self.logger_df2 = logging.getLogger("dotflow2")

        # All DotFlow2 functions can be called by self.df2.x() - where x is the name of the function
        # This is used when developing a bot directly in python as a runtime, or when using $python DotFlow2 function
        self.df2 = DotFlow2FunctionsProxy(self)

        # Registering DotFlow functions from their modules
        DotFlow2CoreFunctions(self)
        DotFlow2Output(self)

        #
        self.debug = {}                      # This holds debug data from the DotFlow2 VM
        self.bot_id = self.dotbot['id']

    def init_plugins(self):
        """
        Init all plugins configured in yml file
        They might try to register as DotFlow2 functions or subscribe to events
        This method should be called when all plugins are loaded into self.plugins

        :return:
        """
        for p in self.plugins:
            self.logger.debug('Initializing plugin ' + str(p))
            self.plugins[p].init(self)

    def register_dotflow2_function(self, function_name: str, callback: dict):
        """
        Register DotFlow2 $function mapped to its plugin method.

        :param function_name: .flow function name
        :param callback: callable array class/method of plugin method
        """
        self.logger_df2.debug('Registering dotflow2 function ' + function_name)
        self.dotflow2_functions_map[function_name] = callback

    def register_template_function(self, function_name: str, callback: dict):
        """
        Register template custom function mapped to its plugin method.

        :param function_name: .flow function name
        :param callback: callable array class/method of plugin method
        """
        self.logger_df2.debug('Registering template custom function ' + function_name)
        self.template_functions_map[function_name] = callback

    def get_response(self, request: dict) -> dict:
        """
        Return a response based on the input data.

        :param request: A dictionary with input data.
        :return: A response to the input data.
        """

        self.request = request
        self.response = {'output': []}
        self.debug = {'functionsResponses': []}

        # get current contexts
        n_curr_context = self.get_current_contexts()

        # looks for matching paths for the current contexts
        m_path = self.get_matching_paths(n_curr_context)

        # If path is false means there is no match, we return noMatch response
        # NOTE: This is a real no-match. This means the engine did not match any node at all.
        #       There are also "no match" nodes which will throw a message to the output but still sending noMatch
        #       response. This is part of the BBot response specification so BBot can call fallback bots if needed for
        #       a better response, but if there is no fallback bot or they don't have a response either, BBot will
        #       send to the channel the original response from the main bot
        if m_path:
            # executes responses on the path
            self.run_responses(m_path)
        else:
            self.response['noMatch'] = True

        # Add debug information
        self.response['debug'] = self.debug

        # returning response
        self.logger_df2.debug("DotFlow2 response: " + str(self.response))
        return self.response

    def get_nodes_by_context(self, context: str) -> list:
        """
        Returns all nodes tagged with specified context
        :return: Nodes list
        """
        return self.dotdb.find_dotflows_by_context(self.bot_id, context)

    def get_current_contexts(self) -> list:
        """
        Returns current contexts.
        It will have the current context of the volley/followups which will have highest priority and lasts until net volley (or X minutes?)
        It will have custom contexts set by nodes and lasts for X minutes
        It always includes 'globals' context at the lowest priority of the context list as a hardcoded fallback context

        :return:
        """
        return ['global']

    def get_matching_paths(self, contexts: list) -> dict:
        """
        Returns path that conditional criteria returns true.
        In the case of criterias that dont uses ML for intent detection it will return the first criterias's path which returns true
        In the case of criterias that do uses ML it will return the one with higher score between the ones that scores above the threshold

        :param node: Node with paths to be tested
        :return: Matched path
        """

        # @TODO for now it only process pattern intent checking

        # Try from highest context priority to lower
        self.logger_df2.debug('Looking for matching paths...')
        matching_path = None
        matching_node = None
        for c in contexts:
            self.logger_df2.debug('Looking for context "' + c + '"')
            nodes = self.get_nodes_by_context(c)
            for n in nodes:
                self.logger_df2.debug('Loading context node "' + n['id'] + '"')
                for p in n['paths']:
                    self.logger_df2.debug('Loading node path "' + p['id'] + '"')
                    if p.get('conditions') is not None:  # Checks if conditions exists
                        result = self.execute_dotflow2_obj(p['conditions'], 'C')
                    else:
                        self.logger_df2.debug('Conditions attr doesn\'t exists. Set default as True')
                        result = True  # Conditions attr doesn't exists so we return True as default

                    self.logger_df2.debug('CONDITIONS RESULT: ' + str(result))
                    if result == True:
                        self.logger_df2.debug('Found a matching path: ' + p['id'] + ' from node: ' + n['id'])
                        matching_node = n
                        matching_path = p
                        break

        return matching_path

    def run_responses(self, path):
        """
        Runs all responses from the path.

        :param path: Path
        """

        bbot_response = []

        responses = path.get('responses')
        if not responses:
            return bbot_response

        for r in responses:
            self.execute_dotflow2_obj(r, 'R')


    def execute_dotflow2_obj(self, dotflow2_obj, f_type: str):
        """
        This runs DotFlow2 instructions. It accepts objects with DotFlow2 functions or strings which will be executed as templates

        :param dotflow2_obj:
        :return:
        """
        self.logger_df2.debug('Trying to execute object: ' + str(dotflow2_obj))
        if self.is_dotflow2_function(dotflow2_obj):
            self.logger_df2.debug('The object is DotFlow2 function')
            func_name = self.get_func_name_from_dotflow2_obj(dotflow2_obj)
            args = self.get_args_from_dotflow2_obj(dotflow2_obj)
            if type(args) is not list:
                args = [args]
            self.logger_df2.debug('Will try to resolve args: ' + str(args))
            # if args are not values we execute them first to resolve them and get the
            # resulting value before call the function
            resolved_args = []
            for arg in args:
                resolved_args.append(self.execute_dotflow2_obj(arg, f_type))
            self.logger_df2.debug('Got resolved args: ' + str(resolved_args))
            response = self.call_dotflow2_function(func_name, resolved_args, f_type)

        elif self.is_template(dotflow2_obj):
            self.logger_df2.debug('The object is a template')
            response = self.plugins['template'].render(self, dotflow2_obj, {})

        else:  # it's a value so return it as response
            self.logger_df2.debug('The object is a value')
            response = dotflow2_obj

        self.logger_df2.debug('DotFlow2 object response: ' + str(response))
        return response

    def is_dotflow2_function(self, value) -> bool:
        """
        Returns true if the value is a DotFlow2 function
        :param value:
        :return:
        """
        try:
            if type(value) is dict:  # function should be defined in a dict
                obj_keys = list(value.keys())
                if len(obj_keys) == 1:  # function should be the only attr of the object
                    if len(obj_keys[0]) >= 2:  # function should have at least one more char plus sign $
                        if obj_keys[0][:1] == self.DOTFLOW2_FUNCTION_PREFIX:  # function should start with a sign $
                            return True
            return False
        except Exception as e:
            return False
        return False

    def is_template(self, value) -> bool:
        """
        Returns true if the value is a template
        :param value:
        :return:
        """
        return type(value) is str and (('{%' in value and '%}' in value) or ('{{' in value and '}}' in value))

    def get_func_name_from_dotflow2_obj(self, bbot_obj: dict) -> str:
        """
        Returns DotFlow2 function name form the condition or response object

        :param dict: Condition or Reesponse DotFlow2 object
        :return: DotFlow2 function name
        """

        return list(bbot_obj.keys())[0][1:]

    def get_args_from_dotflow2_obj(self, bbot_obj: dict):
        """
        Returns DotFlow2 function's arguments from the condition or response object
        :param bbot_obj:
        :return:
        """
        return bbot_obj[self.DOTFLOW2_FUNCTION_PREFIX + self.get_func_name_from_dotflow2_obj(bbot_obj)]

    def call_dotflow2_function(self, func_name: str, args: list, f_type: str):
        """
        Executes a DotFlow2 function

        :param func_name:
        :param args:
        :return:
        """
        self.logger_df2.debug('Calling dotflow2 function "' + func_name + '" with args ' + str(args))
        if func_name in self.dotflow2_functions_map:
            response = getattr(self.dotflow2_functions_map[func_name]['object'],
                               self.dotflow2_functions_map[func_name]['method'])(args, f_type)
        else:
            # @TODO for now we just send a warning to the log. We will make it an Exception later
            self.logger_df2.warning(
                'The bot tried to run DotFlow2 function "' + func_name + '" but it\'s not registered')
            response = None

        self.logger_df2.debug('Response: ' + str(response))

        self.debug['functionsResponses'].append({
            'function': func_name,
            'args': args,
            'return': response,
            'responseTime': 0
        })

        return response



class DotFlow2FunctionsProxy:
    """
    This class is a proxy to call DotFlow2 functions
    """
    def __init__(self, bot: ChatbotEngine):
        self.bot = bot

    def __getattr__(self, name):
        def wrapper(*args, **kwargs):
            if name in self.bot.dotflow2_functions_map:
                return self.bot.call_dotflow2_function(name, args, 'R')
        return wrapper
