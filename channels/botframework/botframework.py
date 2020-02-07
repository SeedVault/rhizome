"""BotFramework Channel."""
import copy
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
        self.access_token = None
        self.dotbot = None

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
            self.dotbot = dotbot
            if not dotbot:
                raise Exception('Bot not found')
            bot_id = dotbot.bot_id
            # build extended dotbot 
            dotbot.services = pub_bot.services
            dotbot.channels = pub_bot.channels
            dotbot.botsubscription = pub_bot

            if 'botframework' not in dotbot.channels.keys():
                raise BBotException("Botframework chanel in not enabled")

            self.app_id = pub_bot.channels['botframework']['app_id']
            self.app_password = pub_bot.channels['botframework']['app_password']

            self.service_url = params['serviceUrl']
            user_id = params['from']['id']
           
            bbot_request = params
            if not bbot_request.get('text'):
                bbot_request['text'] = 'hello'

            self.response_payload = {
                'channelId': params['channelId'],
                'conversation': params['conversation'],
                'from': params['recipient'],
                'id': params['id'],                
                'replyToId': params['id'],                            
                #'inputHint': 'acceptingInput',
                #'localTimestamp': params['localTimestamp'],
                #'locale': params['locale'],
                #'serviceUrl': params['serviceUrl'],
                #'timestamp': datetime.datetime.now().isoformat(),
            }

            channel_id = params['channelId']
            
            config = load_configuration(os.path.abspath(os.path.dirname(__file__) + "../../../instance"), "BBOT_ENV")
            bbot = BBotCore.create_bot(config['bbot_core'], dotbot)
            self.logger.debug('User id: ' + user_id)

            # authenticate
            self.authenticate()

            req = bbot.create_request(bbot_request, user_id, bot_id, org_id, pub_id, channel_id)                           
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
                    'output': [{'type': 'message', 'text': cgi.escape(str(e))}], #@TODO use bbot.text() 
                    'error': {'traceback': str(traceback.format_exc())}
                    }
            else:
                bbot_response = {'output': [{'type': 'message', 'text': 'An error happened. Please try again later.'}]}
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
        
        response_payload = copy.deepcopy(self.response_payload)

        for br in bbot_response['output']:
            
            r = {**response_payload, **br}

            self.logger.debug("Response sent back to BotFramework: " + str(r))        
            url = self.service_url + 'v3/conversations/' + r['conversation']['id'] + '/activities/' + r['id']
            self.logger.debug("To url: " + url)
            response = requests.post(url, headers=self.directline_get_headers(), json=r)
            msg = "BotFramework response: http code: " + str(response.status_code) + " message: " + str(response.text)
            if response.status_code != 200:
                raise BBotException(msg)
            self.logger.debug(msg)

    def directline_get_headers(self):
        headers = {
            'Content-Type': 'application/json',            
        }       
        if self.access_token:
            headers['Authorization'] = 'Bearer ' + self.access_token
        return headers

    def authenticate(self):
        # first check if we have access_token in database
        self.logger.debug("Looking for Azure AD access token in database...")
        stored_token = self.dotdb.get_azure_ad_access_token(self.dotbot.bot_id)        
        if stored_token:
            expire_date = stored_token['expire_date']
            if  expire_date >= datetime.datetime.utcnow():
                # got valid token
                self.access_token = stored_token['access_token']                
                self.logger.debug('Got valid token from db. Will expire in ' + str(stored_token['expire_date']))
                return
            else:
                self.logger.debug('Got expired token. Will request new one')
        else:
            self.logger.debug('There is no token in database. Will request one')

        url = "https://login.microsoftonline.com/botframework.com/oauth2/v2.0/token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.app_id,
            "client_secret": self.app_password,
            "scope": "https://api.botframework.com/.default"
        }
        self.logger.debug("Sending request to Microsoft OAuth with payload: " + str(payload))
        response = requests.post(url, data=payload)    
        msg = "Response from Microsoft OAuth: http code: " + str(response.status_code) + " message: " + str(response.text)
        if response.status_code != 200:
            raise BBotException(msg)
        self.logger.debug(msg)
        json_response = response.json()
        self.access_token = json_response['access_token']
        expire_date = datetime.datetime.utcnow() + datetime.timedelta(0, json_response['expires_in']) # now plus x seconds to get expire date 

        self.dotdb.set_azure_ad_access_token(self.dotbot.bot_id, self.access_token, expire_date)
        
