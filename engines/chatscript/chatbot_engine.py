"""BBot engine based on ChatScript."""
import socket
import logging
import traceback
import re
import json
from bbot.core import BBotCore, ChatbotEngine, ChatbotEngineError, BBotLoggerAdapter


class ChatScript(ChatbotEngine):
    """BBot engine based on ChatScript."""

    def __init__(self, config: dict, dotbot: dict) -> None:
        """
        Initialize the plugin.

        :param config: Configuration values for the instance.
        """
        super().__init__(config, dotbot)

    def init(self, core: BBotCore):
        """
        Initializebot engine 
        """
        super().init(core)

        self.logger = BBotLoggerAdapter(logging.getLogger('chatscript_cbe'), self, self.core)

    def get_response(self, request: dict) -> dict:
        """
        Return a response based on the input data.

        :param request: A dictionary with input data.
        :return: A response to the input data.
        """
        super().get_response(request)

        self.request = request

        input_text = request['input']['text']
        chatbot_engine = self.dotbot.chatbot_engine

        cs_bot_id = chatbot_engine['botId']
        self.logger.debug('Request received for bot id "' + cs_bot_id + '" with text: "' + str(input_text) + '"')

        if not input_text:
            input_text = " " # at least one space, as per the required protocol
        msg_to_send = str.encode(u'%s\u0000%s\u0000%s\u0000' %
                                 (request["user_id"], chatbot_engine['botId'], input_text))
        response = {} # type: dict
        self.logger.debug("Connecting to chatscript server host: " + chatbot_engine['host'] + " - port: " + str(chatbot_engine['port']) + " - botid: " + chatbot_engine['botId'])
        try:
            # Connect, send, receive and close socket. Connections are not
            # persistent
            connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            connection.settimeout(10)  # in secs
            connection.connect((chatbot_engine['host'], int(chatbot_engine['port'])))            
            connection.sendall(msg_to_send)
            msg = ''
            while True:
                chunk = connection.recv(1024)
                if chunk == b'':
                    break
                msg = msg + chunk.decode("utf-8")
            connection.close()
            response = BBotCore.create_response(msg)

        except Exception as e:            
            raise BBotException(e)

        self.logger.debug("Chatscript response: " + str(response))

        # check if chatscript is an error, it should add obb flagging it
        if not len(response):
            msg = "Empty response from ChatScript server"            
            raise BBotException(msg)
        if response == "No such bot.\r\n":
            msg = "There is no such bot on this ChatScript server"            
            raise BbotException(msg)

        # convert chatscript response to bbot response specification
        self.to_bbot_response(response)

       
    def to_bbot_response(self, response: str) -> dict:
        """
        Converts Chatscript response to BBOT response speciication
        :param response:  Chatscript response
        :return: BBOT response specification dict
        """
        # split response and oob
        #response, oob = ChatScript.split_response(response)
    
        response_split = response.split('\\n')
        for rs in response_split:
            #rs = {**bbot_response, **oob} @TODO check oob support
            self.core.bbot.text(rs)


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
