"""BBot engine based on Python."""
import logging
from bbot.core import ChatbotEngine, ChatbotEngineError, Plugin


class Python(ChatbotEngine):
    """
    BBot engine based on Python. This is a proxy class which calls to the real bot class defined in dotbot
    """

    def __init__(self, config: dict, dotbot: dict) -> None:
        """
        Initialize the plugin.

        :param config: Configuration values for the instance.
        """
        super().__init__(config)

    def get_response(self, request: dict) -> dict:
        """
        Return a response based on the input data.

        :param request: A dictionary with input data.
        :return: A response to the input data.
        """
        bot = Plugin.get_class_from_fullyqualified(
            'engines.python.bots.' + self.dotbot['python']['bot_class'] + '.PythonBot')
        bot = bot(self.config)
        bot.logger = logging.getLogger("python")
        response =  bot.get_response(request)

        bot.logger.debug("PythonBot response BBOT format: " + str(response))
        return response




"""
This is an example of a python bot which should be located in /engines/python/bots/test1 
and defined in dotbot as 'python_class': 'test1'  (@TODO maybe set botid as class by convention?)

 
from bbot.core import ChatbotEngine, ChatbotEngineError

class PythonBot(ChatbotEngine):

    def __init__(self, config: dict) -> None:
        super().__init__(config)

    def get_response(self, request: dict) -> dict:
        self.request = request

        bbot_response = {'text': ['DONT ASK ME. IM JUST A PYTHON BOT']}
        return bbot_response

"""
