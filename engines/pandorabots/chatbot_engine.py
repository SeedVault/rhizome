import logging
import requests
from bbot.core import BBotCore, ChatbotEngine, ChatbotEngineError, BBotLoggerAdapter, BBotException

class PandoraBots(ChatbotEngine):
    """
    BBot engine that calls external program.
    """

    def __init__(self, config: dict, dotbot: dict) -> None:
        """
        Initialize the plugin.

        :param config: Configuration values for the instance.
        """
        super().__init__(config, dotbot)

        self.botkey = dotbot.chatbot_engine['botkey']
        self.dotdb = None

    def init(self, core: BBotCore):
        """
        Initializebot engine 
        """
        super().init(core)

        self.url = 'https://api.pandorabots.com'        
        self.logger = BBotLoggerAdapter(logging.getLogger('pandora_cbe'), self, self.core)
        
    def get_response(self, request: dict) -> dict:
        """
        Return a response based on the input data.

        :param request: A dictionary with input data.
        :return: A response to the input data.
        """
        
        super().get_response(request)

        session = self.get_session()
        response = {}
               
        if not session:
            self.logger.debug('There is no session for this user. Ask Pandorabots for a new one.')
            response = self.atalk(self.request['input']['text'])
            self.logger.debug('Storing sessionid and client_name')            
            self.set_session(response['sessionid'], response['client_name'])
        else:
            sessionid = session['sessionid']
            client_name = session['client_name']        
            self.logger.debug('Requesting bot response with sessionid "' + str(sessionid) + '" and client_name "' + str(client_name) + '"')
            response = self.talk(self.request['input']['text'], sessionid, client_name)
        
        self.logger.debug("Response content: " + str(response))            
        
        if response['status'] == 'ok':
            for msg in response['responses']:
                self.core.bbot.text(msg)
        else:
            raise BBotException(str(response))

    def atalk(self, input_txt: str):
        params = {
            'botkey': self.botkey,
            'input': input_txt,    
        }    
        response = requests.post(self.url + '/atalk', params)
        self.logger.debug("Response status code: " + str(response.status_code))    
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            raise BBotException(response.text)    
        else:
            raise Exception(response.text)

    def talk(self, input_txt: str, sessionid: str, client_name: str):       
        params = {
            'botkey': self.botkey,
            'input': input_txt,    
            'extra': True,            
            'sessionid': sessionid,
            'client_name': client_name        
        }    
        response = requests.post(self.url + '/talk', params)
        self.logger.debug("Response status code: " + str(response.status_code))    
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            raise BBotException(response.text)    
        else:
            raise Exception(response.text)

    def get_session(self):
        return self.dotdb.get_pandorabots_session(self.bot_id, self.user_id)    

    def set_session(self, sessionid, client_name):
        self.dotdb.set_pandorabots_session(self.bot_id, self.user_id, sessionid, client_name)    
        
    