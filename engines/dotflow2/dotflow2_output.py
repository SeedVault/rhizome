""""""
import random
from bbot.core import ChatbotEngine, BBotException


class DotFlow2Output():
    """."""

    def __init__(self, bot: ChatbotEngine) -> None:
        """
        Initialize the plugin.
        """

        self.bot = bot

        self.functions = ['text', 'image', 'video', 'audio', 'button']

        for f in self.functions:
            bot.register_dotflow2_function(f, {'object': self, 'method': f})
            bot.register_template_function(f, {'object': self, 'method': f})

    def text(self, args, f_type):
        """
        Sends BBot text output object to the output stream

        :param args:
        :return:
        """

        msg_count = len(args)
        if msg_count > 1:  # multiple output, choose a random one
            msg_idx = random.randint(0, msg_count - 1)
        else:
            msg_idx = 0
        msg = args[msg_idx]

        self.bot.add_output({'text': msg})

    def image(self, args, f_type):
        """
        Sends BBot image output object to the output strea

        :param args:
        :param f_type:
        :return:
        """
        image_link = args[0]
        self.bot.add_output(
            {
                'image': {
                    'url': image_link
                }
            })

    def video(self, args, f_type):
        """
        Sends BBot video object to the output stream

        :param args:
        :param f_type:
        :return:
        """
        video_link = args[0]
        self.bot.add_output(
            {
                'video': {
                    'url': video_link
                }
            })

    def audio(self, args, f_type):
        """
        Sends BBot audio object to the output stream

        :param args:
        :param f_type:
        :return:
        """
        audio_link = args[0]
        self.bot.add_output(
            {
                'audio': {
                    'url': audio_link
                }
            })

    def button(self, args, f_type):
        """
        Sends BBot button output object to the output stream

        :param args:
        :return:
        """
        errors = []
        try:
            button_id = args[0]
        except:
            errors.append({'code': 0, 'function': 'button', 'arg': 0, 'message': 'Button ID missing.'})

        try:
            text = args[1]
        except:
            errors.append({'code': 0, 'function': 'button', 'arg': 1, 'message': 'Button text missing.'})

        try:
            postback = args[2]
        except:
            postback = None  # postback is optional

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

        self.bot.add_output(response)


