""""""
import random

from bbot.core import ChatbotEngine, ChatbotEngineExtension


class DotFlow2Output():
    """."""

    def __init__(self, bot) -> None:
        """
        Initialize the plugin.
        """

        self.bot = bot

        self.functions = ['text']

        for f in self.functions:
            bot.register_dotflow2_function(f, {'object': self, 'method': f})
            bot.register_template_function(f, {'object': self, 'method': f})

    def text(self, args, f_type):
        """
        Sends text to the output

        :param args:
        :return:
        """

        msg_count = len(args)
        if msg_count > 1:  # multiple output, choose a random one
            msg_idx = random.randint(0, msg_count - 1)
        else:
            msg_idx = 0
        msg = args[msg_idx]

        self.bot.response['output'].append({'text': [msg]})
