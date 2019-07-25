""""""
import random
import logging
from bbot.core import ChatbotEngine, BBotException, BBotCore, BBotLoggerAdapter

class BBotResponseOutput():
    """BBot response output objects"""

    def __init__(self, config: dict, dotbot: dict) -> None:
        """
        Initialize the plugin.
        """
        self.config = config
        self.dotbot = dotbot

        self.logger_level = ''

        self.core = None
        self.logger = None

        self.functions = ['text', 'image', 'video', 'audio', 'button']

    def init(self, core: BBotCore):
        """
        Initializes extension

        :param bot:
        :return:
        """
        self.core = core
        self.logger = BBotLoggerAdapter(logging.getLogger('core.ext.response'), self, self.core.bot, 'bbotoutput')                

        for f in self.functions:
            core.register_function(f, {'object': self, 'method': f, 'cost': 0, 'register_enabled': False})
            
    def text(self, args, f_type):
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

        msg = self.core.resolve_arg(args[msg_idx], f_type, True)  # no need to resolve arg before this
        bbot_response = {'text': str(msg)}
        self.core.add_output(bbot_response)
        return bbot_response

    def image(self, args, f_type):
        """
        Returns BBot image output object

        :param args:
        :param f_type:
        :return:
        """
        try:
            image_url = self.core.resolve_arg(args[0], f_type, True)
        except IndexError:
            raise BBotException({'code': 210, 'function': 'image', 'arg': 0, 'message': 'Image URL in arg 0 is missing.'})

        bbot_response = {'image': {'url': image_url}}
        self.core.add_output(bbot_response)
        return bbot_response

    def video(self, args, f_type):
        """
        Returns BBot video object

        :param args:
        :param f_type:
        :return:
        """
        try:
            video_url = self.core.resolve_arg(args[0], f_type, True)
        except IndexError:
            raise BBotException({'code': 220, 'function': 'video', 'arg': 0, 'message': 'Video URL in arg 0 is missing.'})

        bbot_response = {'video': {'url': video_url}}
        self.core.add_output(bbot_response)
        return bbot_response

    def audio(self, args, f_type):
        """
        Returns BBot audio object

        :param args:
        :param f_type:
        :return:
        """
        try:
            audio_url = self.core.resolve_arg(args[0], f_type, True)
        except IndexError:
            raise BBotException({'code': 230, 'function': 'audio', 'arg': 0, 'message': 'Audio URL in arg 0 is missing.'})

        bbot_response = {'audio': {'url': audio_url}}
        self.core.add_output(bbot_response)
        return bbot_response

    def button(self, args, f_type):
        """
        Returns BBot button output object

        :param args:
        :return:
        """
        errors = []
        try:
            button_id = self.core.resolve_arg(args[0], f_type)
        except IndexError:
            errors.append({'code': 240, 'function': 'button', 'arg': 0, 'message': 'Button ID missing.'})

        try:
            text = self.core.resolve_arg(args[1], f_type)
        except IndexError:
            errors.append({'code': 241, 'function': 'button', 'arg': 1, 'message': 'Button text missing.'})

        try:
            postback = self.core.resolve_arg(args[2], f_type)
        except IndexError:
            postback = None  # postback is optional #@TODO revisit this. buttonId is not a good idea after all

        if errors:
            raise BBotException(errors)

        bbot_response = {
                'button': {
                    'id': button_id,
                    'text': text
                }
            }
        if postback:
            bbot_response['button']['postback'] = postback

        self.core.add_output(bbot_response)
        return bbot_response
