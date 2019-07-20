
import socket
import re
import logging
from bbot.core import ChatbotEngine, BBotException
from engines.dotflow2.chatbot_engine import DotFlow2LoggerAdapter

class DotFlow2ChatScriptMatch():
    """ChatScript DotFlow2 function"""

    def __init__(self, config: dict, dotbot: dict) -> None:
        """
        Initialize class
        """
        self.config = config
        self.dotbot = dotbot

        self.bot = None
        self.logger = None

        self.server_host = ''
        self.server_port = 0
        self.server_bot_id = ''
        self.logger_level = ''

    def init(self, bot: ChatbotEngine):
        """
        Initialize chatbot engine

        :param bot:
        :return:
        """
        self.bot = bot
        self.logger = DotFlow2LoggerAdapter(logging.getLogger('df2_ext.csMatch'), self, self.bot, '$chatscriptMatch')
        bot.register_dotflow2_function('chatscriptMatch', {'object': self, 'method': 'chatscriptMatch'})
        
    def chatscriptMatch(self, args, f_type):
        """
        Evaluates ChatScript pattern
        @TODO add caching

        :param args:
        :param f_type:
        :return:
        """

        try:
            pattern = self.bot.resolve_arg(args[0], f_type)
        except IndexError:
            raise BBotException({'code': 190, 'function': 'chatscriptMatch', 'arg': 0, 'message': 'Pattern in arg 0 is missing.'})

        try:
            input_text = self.bot.resolve_arg(args[1], f_type)
        except IndexError:
            raise BBotException({'code': 191, 'function': 'chatscriptMatch', 'arg': 1, 'message': 'Text in arg 1 is missing.'})

        try:
            entities_var_names = self.bot.resolve_arg(args[2], f_type)
        except IndexError:
            entities_var_names = []  # entities are optional

        result = False
        if len(input_text) > 0:
            # clear match variables first (ChatScript does not reset them when running testpattern)
            self.send(':do ^clearmatch()')
            # test the pattern
            cs_req = f":testpattern ({pattern}) {input_text}"  #@TODO try sending direct text and running ^match later (it's faster. sends input text once)
            self.logger.debug("ChatScript request: " + cs_req)
            cs_res = self.send(cs_req)
            self.logger.debug('ChatScript response: \n' + str(cs_res))

            if not self.has_error(cs_res):
                result = self.is_match(cs_res)
                if result:
                    self.logger.info('It\'s a match!')
                else:
                    self.logger.info('No match')
                # check if there are match variables set
                if self.has_match_variables(cs_res):
                    self.store_variables_from_matched_variables(entities_var_names)
            else:
                self.logger.warning('Response returned with error')

        return result

    def has_error(self, response):
        """
        Returns True if success response, False if not
        Successful response means ChatScript didn't answer with an error. It can be with Match or Failure responses.

        :param response:
        :return:
        """
        return response.find(' Matched') == -1 and response.find(' Failed') == -1

    def is_match(self, response):
        """
        Returns True if there is a match, False if not

        :param response:
        :return:
        """
        return response.find(' Matched') != -1

    def has_match_variables(self, response):
        """
        Returns True if there are match variables set

        :param response:
        :return:
        """
        return response.find(' wildcards: (') != -1

    def store_variables_from_matched_variables(self, entities_var_names: list):
        """
        Stores all matched variables with names defined by the 3rd argument on DotFlow2 function $chatscriptMatch

        :return:
        """
        # get matched variables
        vm_res = self.send(':variables match')
        vm_res_list = vm_res.split('\n')
        # This parses ':variable match' ChatScript response: _2 (5-5) =  black (black)
        # This will result in capture groups: 2, 5, 5, black, black
        for vmrl in vm_res_list:
            r = re.match('_(\d+) \((\d+)-(\d+)\) =  ([^\(]+) \((.+)\)', vmrl)
            if r:
                match_variable_n = int(r.group(1))
                var_value = r.group(4)
                try:
                    var_name = entities_var_names[match_variable_n]
                    self.bot.session.set_var(self.bot.user_id, var_name, var_value)
                    self.bot.detected_entities[
                        var_name] = var_value  # @TODO this value should be sent to response only if the conditional returns True
                    self.logger.info('Storing match variable "_' + str(match_variable_n) +
                                     '" in DotFlow2 variable "' + var_name + '" with value "' + var_value + '"')
                except IndexError:
                    self.logger.warning('ChatScript detected a match variable but there is no entity variable name provided')

    def send(self, input_text):
        """

        :param user_id:
        :param input_text:
        :return:
        """

        if not input_text:
            input_text = " " # at least one space, as per the required protocol
        msg_to_send = str.encode(u'%s\u0000%s\u0000%s\u0000' % (self.bot.user_id, self.server_bot_id, input_text))
        self.logger.debug(f"Trying to connect to ChatScript server on host '{self.server_host}' port '{self.server_port}' botid '{self.server_bot_id}'")
        response = ''
        try:
            # Connect, send, receive and close socket. Connections are not
            # persistent
            connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            connection.settimeout(10)  # in secs
            connection.connect((self.server_host, int(self.server_port)))
            connection.sendall(msg_to_send)

            while True:
                chunk = connection.recv(1024)
                if chunk == b'':
                    break
                response = response + chunk.decode("utf-8")
            connection.close()

        except ConnectionRefusedError as e:
            self.logger.critical("ChatScript server is not answering: " + str(e))
        except Exception as e:
            raise e

        return response
