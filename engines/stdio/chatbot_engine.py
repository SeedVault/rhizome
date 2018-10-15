"""BBot engine that calls external program."""
import logging
from bbot.core import ChatbotEngine, ChatbotEngineError, Plugin

import subprocess


class Stdio(ChatbotEngine):
    """
    BBot engine that calls external program.
    """

    def __init__(self, config: dict, dotbot: dict) -> None:
        """
        Initialize the plugin.

        :param config: Configuration values for the instance.
        """
        super().__init__(config)

        self.cmd = config.cmd
        self.p = subprocess.Popen(self.cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    def get_response(self, request: dict) -> dict:
        """
        Return a response based on the input data.

        :param request: A dictionary with input data.
        :return: A response to the input data.
        """

        input_text = request['input']['text']
        input_text.replace("\n", " ") 
        self.p.stdin.write(input_text + "\n")

        output_text = self.p.stdout.readline()

        response =  {"text": [output_text]}

        return response


