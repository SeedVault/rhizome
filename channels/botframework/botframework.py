"""BotFramework Channel."""
import logging
import json
import os
import cgi
import traceback
import datetime
import requests
from urllib.parse import urlparse

from bbot.core import BBotCore, ChatbotEngine, BBotException, BBotLoggerAdapter
from bbot.config import load_configuration

class BotFramework:
    
    def __init__(self, config: dict, dotbot: dict) -> None:
        """        
        """
        self.config = config
        self.dotbot = dotbot
        self.dotdb = None #        
        self.logger_level = ''

    def init(self, core):
        self.core = core
        self.logger = BBotLoggerAdapter(logging.getLogger('channel_botframerwork'), self, self.core, 'ChannelBotFramework')        

        self.logger.debug("Listening BotFramework from path: " + self.get_webhook_path())

    def endpoint(self, request=dict, publisherbot_token=str):
        print('------------------------------------------------------------------------------------------------------------------------')
        self.logger.debug('Received request: ' + str(request.data))
        self.logger.debug(f'Received a BotFramework webhook request for publisher token {publisherbot_token}')        

        try:
            params = request.get_json(force=True)
            org_id = 1

            # get publisher user id from token
            pub_bot = self.dotdb.find_publisherbot_by_publisher_token(publisherbot_token)
            if not pub_bot:
                raise Exception('Publisher not found')
            self.logger.debug('Found publisher: ' + pub_bot.publisher_name + ' - for bot id: ' + pub_bot.bot_id)
            pub_id = pub_bot.publisher_name
                    
            dotbot = self.dotdb.find_dotbot_by_bot_id(pub_bot.bot_id)                    
            if not dotbot:
                raise Exception('Bot not found')
            bot_id = dotbot.bot_id
            # build extended dotbot 
            dotbot.services = pub_bot.services
            dotbot.channels = pub_bot.channels
            dotbot.botsubscription = pub_bot
            
            user_id = params['from']['id']

            bbot_request = {'text': ''}
            if params['type'] == 'message':
                bbot_request = {'text': params['text']}

            #@TODO we might better be using msft botbuilder pkg to handle this
            self.response_payload = {
                'channelId': params['channelId'],
                'conversation': {'id': params['conversation']['id']},
                'from': params['recipient'],
                'id': params['id'],
                'inputHint': 'acceptingInput',
                'localTimestamp': params['localTimestamp'],
                'locale': params['locale'],
                'replyToId': params['id'],
                'serviceUrl': params['serviceUrl'],
                'timestamp': datetime.datetime.now().isoformat(),
                'type': 'message'
            }

            config = load_configuration(os.path.abspath(os.path.dirname(__file__) + "../../../instance"), "BBOT_ENV")
            bbot = BBotCore.create_bot(config['bbot_core'], dotbot)
            self.logger.debug('User id: ' + user_id)
            req = bbot.create_request(bbot_request, user_id, bot_id, org_id, pub_id)                           
            bbot_response = bbot.get_response(req)
            http_code = 200
            
        except Exception as e:          
            if isinstance(e, BBotException): # BBotException means the issue is in bot userland, not rhizome
                http_code = 200                                                
            else:
                self.logger.critical(str(e) + "\n" + str(traceback.format_exc()))            
                http_code = 500            
                
            if os.environ['BBOT_ENV'] == 'development':                
                bbot_response = {
                    'output': [{'text': cgi.escape(str(e))}], #@TODO use bbot.text() 
                    'error': {'traceback': str(traceback.format_exc())}
                    }
            else:
                bbot_response = {'output': [{'text': 'An error happened. Please try again later.'}]}
                # @TODO this should be configured in dotbot
                # @TODO let bot engine decide what to do?
            
        self.logger.debug("Response from restful channel: " + str(bbot_response))
        self.to_botframework(bbot_response)

    def get_webhook_url(self) -> str:
        return self.config['webhook_uri']

    def get_webhook_path(self) -> str:
        parsed_url = urlparse(self.config['webhook_uri'])
        return parsed_url.path 

    def to_botframework(self, bbot_response):
        for br in bbot_response['output']:
            if 'text' in br.keys():
                if not self.response_payload.get('text'):
                    self.response_payload['text'] = ''
                self.response_payload['text'] += br['text']
            if br.get('contentType', '').startswith('application/vnd.microsoft.card'):
                if not self.response_payload.get('attachments'):
                    self.response_payload['attachments'] = []
                self.response_payload['attachments'].append(br)

        self.logger.debug("Response sent back to BotFramework: " + str(self.response_payload))
        
        response = requests.post(self.response_payload['serviceUrl'] + '/v3/conversations', headers=self.directline_get_headers(), json=self.response_payload)
        self.logger.debug("Response from BotFramework: " + str(response.text))

    def directline_get_headers(self):
        return {
            'Content-Type': 'application/json',
        }       