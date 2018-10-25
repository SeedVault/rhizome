""""""
import random
import logging
from bbot.core import ChatbotEngine, BBotException
from engines.dotflow2.chatbot_engine import DotFlow2LoggerAdapter


class DotFlow2ResponseOutput():
    """BBot response output objects"""

    def __init__(self, config: dict, dotbot: dict) -> None:
        """
        Initialize the plugin.
        """
        self.config = config
        self.dotbot = dotbot

        self.logger_level = ''

        self.bot = None
        self.logger = None

        self.functions = ['text', 'image', 'video', 'audio', 'button']

    def init(self, bot: ChatbotEngine):
        """
        Initializes extension

        :param bot:
        :return:
        """
        self.bot = bot
        self.logger = DotFlow2LoggerAdapter(logging.getLogger('df2_ext.r_output'), self, self.bot, 'Output Response Ext')

        for f in self.functions:
            bot.register_dotflow2_function(f, {'object': self, 'method': 'df2_' + f})
            bot.register_template_function(f, {'object': self, 'method': 'df2_' + f})

    def df2_text(self, args, f_type):
        """
        Returns BBot text output object

        :param args:
        :return:
        """

        if len(args) == 0:
            raise BBotException({'code': 200, 'function': 'text', 'arg': 0, 'message': 'Text in arg 0 is missing.'})

        msg_count = len(args)
        if msg_count > 1:  # multiple output, choose a random one
            msg_idx = random.randint(0, msg_count - 1)
        else:
            msg_idx = 0

        msg = self.bot.resolve_arg(args[msg_idx], f_type)  # no need to resolve arg before this

        return {'text': msg}

    def df2_image(self, args, f_type):
        """
        Returns BBot image output object

        :param args:
        :param f_type:
        :return:
        """
        try:
            image_url = self.bot.resolve_arg(args[0], f_type)
        except IndexError:
            raise BBotException({'code': 210, 'function': 'image', 'arg': 0, 'message': 'Image URL in arg 0 is missing.'})

        return {
                'image': {
                    'url': image_url
                }
            }

    def df2_video(self, args, f_type):
        """
        Returns BBot video object

        :param args:
        :param f_type:
        :return:
        """
        try:
            video_url = self.bot.resolve_arg(args[0], f_type)
        except IndexError:
            raise BBotException({'code': 220, 'function': 'video', 'arg': 0, 'message': 'Video URL in arg 0 is missing.'})

        return {
                'video': {
                    'url': video_url
                }
            }

    def df2_audio(self, args, f_type):
        """
        Returns BBot audio object

        :param args:
        :param f_type:
        :return:
        """
        try:
            audio_url = self.bot.resolve_arg(args[0], f_type)
        except IndexError:
            raise BBotException({'code': 230, 'function': 'audio', 'arg': 0, 'message': 'Audio URL in arg 0 is missing.'})

        return {
                'audio': {
                    'url': audio_url
                }
            }

    def df2_button(self, args, f_type):
        """
        Returns BBot button output object

        :param args:
        :return:
        """
        errors = []
        try:
            button_id = self.bot.resolve_arg(args[0], f_type)
        except IndexError:
            errors.append({'code': 240, 'function': 'button', 'arg': 0, 'message': 'Button ID missing.'})

        try:
            text = self.bot.resolve_arg(args[1], f_type)
        except IndexError:
            errors.append({'code': 241, 'function': 'button', 'arg': 1, 'message': 'Button text missing.'})

        try:
            postback = self.bot.resolve_arg(args[2], f_type)
        except IndexError:
            postback = None  # postback is optional #@TODO revisit this. buttonId is not a good idea after all

        if errors:
            raise BBotException(errors)

        response = {
                'button': {
                    'id': button_id,
                    'text': text
                }
            }
        if postback:
            response['button']['postback'] = postback

        return response


