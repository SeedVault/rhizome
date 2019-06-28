"""BBot engine based on ChatScript."""
import socket
import logging
import traceback
import re
import json
from bbot.core import ChatbotEngine, ChatbotEngineError


class ChatScript(ChatbotEngine):
    """BBot engine based on ChatScript."""

    def __init__(self, config: dict, dotbot: dict) -> None:
        """
        Initialize the plugin.

        :param config: Configuration values for the instance.
        """
        super().__init__(config, dotbot)

        self.config = config
        self.dotbot = dotbot

        self.logger_level = ''          # Logging level for the module
        self.logger_cs = logging.getLogger("chatscript")

    def get_response(self, request: dict) -> dict:
        """
        Return a response based on the input data.

        :param request: A dictionary with input data.
        :return: A response to the input data.
        """

        self.request = request

        input_text = request['input']['text']

        cs_bot_id = self.dotbot['chatscript']['botId']
        self.logger_cs.debug('Request received for bot id "' + cs_bot_id + '" with text: "' + str(input_text) + '"')

        if not input_text:
            input_text = " " # at least one space, as per the required protocol
        msg_to_send = str.encode(u'%s\u0000%s\u0000%s\u0000' %
                                 (request["user_id"], self.dotbot['chatscript']['botId'], input_text))
        response = {} # type: dict
        self.logger_cs.debug("Connecting to chatscript server host: " + self.dotbot['chatscript']['host'] + " - port: " + str(self.dotbot['chatscript']['port']) + " - botid: " + self.dotbot['chatscript']['botId'])
        try:
            # Connect, send, receive and close socket. Connections are not
            # persistent
            connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            connection.settimeout(10)  # in secs
            connection.connect((self.dotbot['chatscript']['host'], self.dotbot['chatscript']['port']))            
            connection.sendall(msg_to_send)
            msg = ''
            while True:
                chunk = connection.recv(1024)
                if chunk == b'':
                    break
                msg = msg + chunk.decode("utf-8")
            connection.close()
            response = self.create_response(msg)

        except Exception as e:
            self.logger_cs.critical(str(e) + "\n" + str(traceback.format_exc()))
            raise Exception(e)

        self.logger_cs.debug("Chatscript response: " + str(response))

        # check if chatscript is an error, it should add obb flagging it
        if not len(response):
            msg = "Empty response from ChatScript server"
            self.logger_cs.critical(msg)
            raise Exception(msg)
        if response == "No such bot.\r\n":
            msg = "There is no such bot on this ChatScript server"
            self.logger_cs.critical(msg)
            raise Exception(msg)

        # convert chatscript response to bbot response specification
        bbot_response = ChatScript.to_bbot_response(response)

        self.logger_cs.debug("Chatscript response BBOT format: " + str(bbot_response))

        bbot_response = self.fallback_bot(self, bbot_response) # @TODO this might be called from a different place
        return {'output': [bbot_response]}

    @staticmethod
    def to_bbot_response(response: str) -> dict:
        """
        Converts Chatscript response to BBOT response speciication
        :param response:  Chatscript response
        :return: BBOT response specification dict
        """
        # split response and oob
        response, oob = ChatScript.split_response(response)

        bbot_response = {'text': response}
        bbot_response = {**bbot_response, **oob}
        return bbot_response

    @staticmethod
    def split_response(response: str) -> tuple:
        """
        Returns a splitted text response and OOB in a tuple
        :param response: Chatscript response
        :return: Tuple with text response and OOB
        """
        oob_json_re = re.search('^\[{.*\}\ ]', response)
        oob = {}
        if oob_json_re:
            oob = json.loads(oob_json_re.group(0).strip('[]'))
            response = response.replace(oob_json_re.group(0), '')
        return response, oob
