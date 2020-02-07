"""BBot engine based on DirectLine API."""
import logging
import copy
import requests
import json
from bbot.core import BBotCore, ChatbotEngine, ChatbotEngineError, BBotLoggerAdapter, BBotException


class DirectLine(ChatbotEngine):
    
    def __init__(self, config: dict, dotbot: dict) -> None:
        """
        Initialize the plugin.

        :param config: Configuration values for the instance.
        """
        super().__init__(config, dotbot)

        self.dotdb = None

        self.conversation_id = None
        self.watermark = None
        self.direct_line_secret = self.dotbot.chatbot_engine['secret']
        self.base_url = self.dotbot.chatbot_engine.get('url') or 'https://directline.botframework.com/v3/directline'

    def init(self, core: BBotCore):
        """
        Initializebot engine 
        """
        super().init(core)
        
        self.logger = BBotLoggerAdapter(logging.getLogger('directline_cbe'), self, self.core)

    def get_response(self, request: dict) -> dict:
        """
        Return a response based on the input data.

        :param request: A dictionary with input data.
        :return: A response to the input data.
        """
        super().get_response(request)

        self.init_session()
        self.directline_send_message(request['input']['text'])
        response = self.directline_get_message()
        self.to_bbot_response(response)

    def to_bbot_response(self, response: list) -> dict:        
        bbot_response = []
        resp = copy.deepcopy(response)

        for r in resp['activities']:            
            # filter not needed data
            elms = ['id', 'conversation', 'conversationId', 'timestamp', 'channelId', 'inputHint', 'from', 'recipient', 'replyToId', 'serviceUrl']
            for i in elms:
                if i in r:
                    del r[i]

            self.core.add_output(r)
                                
    def init_session(self):
        if not self.conversation_id or not self.watermark:
            # look on database first            
            self.logger.debug('Looking for conversation id and watermark in database')
            session = self.dotdb.get_directline_session(self.user_id, self.bot_id)                        
            if not session:                
                self.logger.debug('Not in database, ask for a new one and store it')
                self.conversation_id = self.directline_get_new_conversation_id()
                self.watermark = "" # it will not filter by watermark so we can get initial welcome message from the bot
                self.dotdb.set_directline_session(self.user_id, self.bot_id, self.conversation_id, self.watermark)
            else:
                self.conversation_id, self.watermark = session
                self.logger.debug('Got conversation ID: ' + self.conversation_id + ' - watermark: ' + str(self.watermark))

    def directline_get_headers(self):
        return {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + self.direct_line_secret,
        }        

    def directline_get_new_conversation_id(self):        
        url = self.base_url + '/conversations'
        self.logger.debug('DirectLine requesting new conversation id')
        response = requests.post(url, headers=self.directline_get_headers())        
        self.logger.debug('DirectLine response: ' + response.text)
        if response.status_code == 201 or response.status_code == 200:
            jsonresponse = response.json()
            return jsonresponse['conversationId']

        raise BBotException('Response error code: ' + str(response.status_code))
        
    def directline_send_message(self, text):        
        url = self.base_url + '/conversations/' + self.conversation_id + '/activities'
        payload = {
            'conversationId': self.conversation_id,
            'type': 'message',
            'from': {'id': self.request["user_id"]},
            'text': text
        }        
        self.logger.debug('DirectLine sending message with payload: ' +  str(payload))
        self.logger.debug('url: ' + url)
        response = requests.post(url, headers=self.directline_get_headers(), data=json.dumps(payload))
        self.logger.debug('DirectLine response: ' + response.text)
        if response.status_code == 200:            
            return response.json()

        raise BBotException('Response error code: ' + str(response.status_code) + ' - Message: ' + response.text)
        

    def directline_get_message(self):        
        url = self.base_url + '/conversations/' + self.conversation_id + '/activities?watermark=' + self.watermark
        payload = {'conversationId': self.conversation_id}
        self.logger.debug('DirectLine getting message with payload: ' + str(payload))
        self.logger.debug('url: ' + url)
        response = requests.get(url, headers=self.directline_get_headers(), json=payload)
        self.logger.debug('DirectLine response: ' + response.text)
        if response.status_code == 200:
            # store watermark
            json_response = response.json()
            self.watermark = json_response['watermark']
            self.dotdb.set_directline_session(self.user_id, self.bot_id, self.conversation_id, json_response['watermark'])            
            return json_response
      
        raise BBotException('Response error code: ' + str(response.status_code))
