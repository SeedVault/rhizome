"""Bot engine based on Rasa Core with Rasa Server"""
import logging
import requests
from bbot.core import ChatbotEngine, ChatbotEngineError, BBotLoggerAdapter, Plugin, BBotCore, BBotException


class RasaRestServer(ChatbotEngine):
    """
    """

    def __init__(self, config: dict, dotbot: dict) -> None:
        """
        Initialize the plugin.

        :param config: Configuration values for the instance.
        """
        super().__init__(config, dotbot)

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
                               
        server_url = self.dotbot.chatbot_engine['serverUrl']
        msg = self.request['input']['text']

        self.logger.debug('Querying to Rasa Server ' + server_url)
        params = {"sender": self.user_id, "message": msg}
        r = requests.post(server_url + '/webhooks/rest/webhook', json=params)
        self.logger.debug('Rasa Server response code: ' + str(r.status_code) + ' - message: ' + str(r.text)[0:300])
        if r.status_code == 200:
            aw = r.json()[0]
        else:
            raise BBotException(r.text)
        
        if 'text' in aw.keys():
            self.core.bbot.text(aw['text'])
        #@TODO add media like image
        return self.response
        


