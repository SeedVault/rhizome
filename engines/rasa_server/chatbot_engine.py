"""Bot engine based on Rasa Core with Rasa Server"""
import logging
import requests
import json
import socketio
from bbot.core import ChatbotEngine, ChatbotEngineError, BBotLoggerAdapter, Plugin, BBotCore, BBotException


class RasaServer(ChatbotEngine):
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
        self.logger = BBotLoggerAdapter(logging.getLogger('rasaserver_cbe'), self, self.core)
                
    def get_response(self, request: dict) -> dict:
        """
        Return a response based on the input data.

        :param request: A dictionary with input data.
        :return: A response to the input data.
        """        
        super().get_response(request)
                                            
        msg = self.request['input']['text']
        
        server_type = self.get_server_type()
        if  server_type == 'socketio':
            response = self.socketio_server(msg)
        if  server_type == 'rest':
            response = self.rest_server(msg)
        
        for r in response:            
            if 'text' in r.keys():
                self.core.bbot.text(r['text'])
            if 'image' in r.keys():
                self.core.bbot.image(r['image'])
            
        return self.response
        
    def get_server_type(self):
        if self.dotbot.chatbot_engine['serverUrl'].startswith('http'):
            return 'rest'
        elif self.dotbot.chatbot_engine['serverUrl'].startswith('ws'):
            return 'socketio'
        else:
            raise BBotException('Wrong Rasa Server url')

    def rest_server(self, msg):
        server_url = self.dotbot.chatbot_engine['serverUrl']
        self.logger.debug('Querying to Rasa Server ' + server_url)
        params = {"sender": self.user_id, "message": msg}
        r = requests.post(server_url + '/webhooks/rest/webhook', json=params)
        self.logger.debug('Rasa Server response code: ' + str(r.status_code) + ' - message: ' + str(r.text)[0:300])
        if r.status_code == 200:
            aw = r.json()            
        else:
            raise BBotException(r.text)
        return aw
        
    def socketio_server(self, msg):
        server_url = self.dotbot.chatbot_engine['serverUrl']
        user_message_evt = self.dotbot.chatbot_engine.get('userMessageEvt', 'user_uttered')
        bot_message_evt = self.dotbot.chatbot_engine.get('botMessageEvt', 'bot_uttered')
        
        sio = socketio.Client()
        
        @sio.on(bot_message_evt)
        def on_message(data):
            self.logger.debug("Received '%s'" % data)
            self.recv = data                
        
        @sio.on('session_confirm')
        def on_message(data):
            self.logger.debug("Session confirmed '%s'" % data)
            
        self.logger.debug('Querying to Rasa Server ' + server_url)
        sio.connect(server_url)
        sio.call('session_request', {"session_id": [self.user_id]})
        sio.call(user_message_evt, data={"message": msg,"customData":{"language":"en"},"session_id": self.user_id})              
        sio.disconnect()
        return [self.recv] #@TODO check multiple outputs
        

