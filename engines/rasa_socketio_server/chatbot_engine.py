"""Bot engine based on Rasa Core with Rasa SocketIO Channel"""
import logging
import requests
import json
import socketio
from bbot.core import ChatbotEngine, ChatbotEngineError, BBotLoggerAdapter, Plugin, BBotCore


class RasaSocketIOServer(ChatbotEngine):
    """
    """

    def __init__(self, config: dict, dotbot: dict) -> None:
        """
        Initialize the plugin.

        :param config: Configuration values for the instance.
        """
        super().__init__(config, dotbot)

        self.recv = None

    def init(self, core: BBotCore):
        """
        Initializes bot
        """
        super().init(core)

        self.logger = BBotLoggerAdapter(logging.getLogger('rasawsserver_cbe'), self, self.core)
                
    def get_response(self, request: dict) -> dict:
        """
        Return a response based on the input data.

        :param request: A dictionary with input data.
        :return: A response to the input data.
        """        
        super().get_response(request)
                               
        server_url = self.dotbot.chatbot_engine['serverUrl']
        user_message_evt = self.dotbot.chatbot_engine.get('userMessageEvt', 'user_uttered')
        bot_message_evt = self.dotbot.chatbot_engine.get('botMessageEvt', 'bot_uttered')
        msg = self.request['input']['text']
        
        self.logger.debug('Querying to Rasa Server ' + server_url)
        
        sio = socketio.Client()
        
        @sio.on(bot_message_evt)
        def on_message(data):
            self.logger.debug("Received '%s'" % data)
            self.recv = data                
        
        @sio.on('session_confirm')
        def on_message(data):
            self.logger.debug("Session confirmed '%s'" % data)
            
        sio.connect(server_url)
        sio.call('session_request', {"session_id": [self.user_id]})
        sio.call(user_message_evt, data={"message": msg,"customData":{"language":"en"},"session_id": self.user_id})              
        sio.disconnect()
                    
        self.core.bbot.text(self.recv['text'])
        return self.response
        

       