"""Chatscript match."""
import socket
from flow.chatbot_engine import Extension, FlowError

class ChatscriptMatch(Extension):
    """ChatscriptMatch plugin - defined .flow function ChatscriptMatch to match with
    patterns based on ChatScript patterns"""


    def __init__(self, flow):
        super().__init__(flow)
        class_name = self.__class__.__module__ + '.' + self.__class__.__name__
        flow.register_dot_flow_function('chatscript', {
            'class': class_name, 'method': 'match'})

    
    def match(self, args) -> bool:
        """
        Matches the 'pattern' with the user input

        :param pattern: pattern rule
        :param input_text: input text
        """

        pattern = args[0]
        input_text = args[1]

        if len(input_text) > 0:            
            cs_req = f":testpattern ({pattern}) {input_text}"
            cs_res = self.send(cs_req)
            result = cs_res.split("\n")[1].find("Matched") != -1
            return result

        return False

        # raise FlowError(f'Bad ChatScript pattern {pattern}')


    def send(self, input_text: str) -> dict:
        """
        Return a response based on the input data.

        :param request: A dictionary with input data.
        :return: A response to the input data.
        """        
           
        if not input_text:
            input_text = " " # at least one space, as per the required protocol
        msg_to_send = str.encode(u'%s\u0000%s\u0000%s\u0000' %
                                 ("bbot", self.flow.chatscript_flowext_bot_id, input_text))
        response = {} # type: dict
        try:
            # Connect, send, receive and close socket. Connections are not
            # persistent
            connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            connection.settimeout(10)  # in secs
            connection.connect((self.flow.chatscript_flowext_host, self.flow.chatscript_flowext_port))
            connection.sendall(msg_to_send)
            msg = ''
            while True:
                chunk = connection.recv(1024)
                if chunk == b'':
                    break
                msg = msg + chunk.decode("utf-8")
            connection.close()
            response = msg

        except socket.error:
            pass
            # msg = dict("":"") # something went wrong
        return response
