import logging
import html
import traceback
import json
import os
import cgi

from bbot.core import BBotCore, ChatbotEngine, BBotException, BBotLoggerAdapter
from bbot.config import load_configuration

class Restful:
    """"""
    def __init__(self, config: dict, dotbot: dict=None) -> None:
        """

        """
        self.config = config
        self.dotbot = dotbot
        self.dotdb = None  #
        self.tts = None
        self.actr = None
        self.logger_level = ''
        
        self.params = {}        

    def init(self, core):
        self.core = core
        self.logger = BBotLoggerAdapter(logging.getLogger('channel_restful'), self, self.core, 'ChannelRestful')        

    def endpoint(self, request=dict):
        try:            
            print('--------------------------------------------------------------------------------------------------------------------------------')
            self.params = request.get_json(force=True)
            self.logger.debug("Received request " + str(self.params))
            
            user_id = self.params.get('userId')
            bot_id = self.params.get('botId')
            org_id = self.params.get('orgId')
            pub_token = self.params.get('pubToken')        
            channel_id = self.params.get('channelId')
            input_params = self.params['input']

            input_params['channelPlatform'] = 'bbot_restful_channel'
            
            # get publisher user id from token
            pub_bot = self.dotdb.find_publisherbot_by_publisher_token(pub_token)
            if not pub_bot:
                raise Exception('Publisher not found')
            self.logger.debug('Found subscription id: ' + str(pub_bot.id) + ' - publisher name: ' + pub_bot.publisher_name + ' - for bot name: ' + pub_bot.bot_name + ' - bot id:' + pub_bot.bot_id)
            
            pub_id = pub_bot.publisher_name

            print("1")
            
            # if 'runBot' in params:
            #    run_bot = self.params['runBot']
        
            dotbot = self.dotdb.find_dotbot_by_bot_id(pub_bot.bot_id)                    
            print("2")
            if not dotbot:
                raise Exception('Bot not found')
            bot_id = dotbot.bot_id
            # build extended dotbot 
            dotbot.services = pub_bot.services
            dotbot.channels = pub_bot.channels
            dotbot.botsubscription = pub_bot
            print("3")
            self.dotbot = dotbot # needed for methods below
            config = load_configuration(os.path.abspath(os.path.dirname(__file__) + "../../../instance"), "BBOT_ENV")            
            print("4")

            bot = BBotCore.create_bot(config['bbot_core'], dotbot)
            self.core = bot
            input_text = ""
            #for input_type, input_value in input_params.items():
                # bot.get_response(input_type, input_value)
            #    _ = input_type
            #    input_text = input_text + input_value
            req = bot.create_request(
                input_params, user_id, bot_id, org_id, pub_id, channel_id)
            bbot_response = {}
            http_code = 500     
            bbot_response = bot.get_response(req)
            
            #response = defaultdict(lambda: defaultdict(dict))    # create a response dict with autodict property
            #for br in bot_response.keys():
            #   response[br] = bot_response[br]
            
            #response['output'] = self.escape_html_from_text(response['output'])
            #logger.debug('Escaped response text: ' + str(response['output']))
            
            if self.params.get('ttsEnabled'):          
                bbot_response['tts'] = {}
                if not self.tts:
                    bbot_response['errors'].append({'message': 'No TTS engine configured for this bot.'})                      
                else:
                    #retrieve TTS audio generated from all texts from bbot output                    
                    self.tts.voice_locale = self.get_tts_locale()
                    self.tts.voice_id = self.get_tts_voice_id()
                    all_texts = BBotCore.get_all_texts_from_output(bbot_response['output'])                
                    bbot_response['tts']['url'] = self.tts.get_speech_audio_url(all_texts, self.get_tts_timescale())           

            if self.params.get('actrEnabled', None): 
                bbot_response['actr'] = {}
                if not self.tts:
                    response['errors'].append({'message': 'No ACTR engine configured for this bot.'})                      
                else:
                    all_texts = BBotCore.get_all_texts_from_output(bbot_response['output'])                                    
                    bbot_response['actr'] = self.actr.get_actr(
                        all_texts,                         
                        self.get_tts_locale(),
                        self.get_tts_voice_id(), 
                        self.get_tts_timescale())


            if self.params.get('debugEnabled') is None:                
                if 'debug' in bbot_response:                     
                    del bbot_response['debug']
            
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
        return {'response': json.dumps(bbot_response), 'status': http_code, 'mimetype': 'application/json'}

    def get_endpoint_path(self) -> str:
        return self.config['endpoint_path']

    def get_tts_locale(self) -> str:
        """Returns locale for tts service"""
        if self.dotbot.tts.get('locale') is not None:
            return self.dotbot.tts['locale']
        # from request 
        if self.params.get('ttsLocale') is not None:
            return self.params['ttsLocale']
        # If there is no voice set, check fo default in DotBot
        if self.dotbot.tts.get('defaultLocale') is not None:
            return self.dotbot.tts['defaultLocale']
        # If there is not even defaultVoiceId, try with hardcoded default value
        return 'en_US'

    def get_tts_voice_id(self) -> str:
        """Returns bot voice id"""
        # DotBot VoiceId has higher priority. external configurations can't change this
        if self.dotbot.tts.get('voiceId') is not None:
            return self.dotbot.tts['voiceId']
        # from request 
        if self.params.get('ttsVoiceId') is not None:
            return self.params['ttsVoiceId']
        # If there is no voice set, check fo default in DotBot
        if self.dotbot.tts.get('defaultVoiceId') is not None:
            return self.dotbot.tts['defaultVoiceId']
        # If there is not even defaultVoiceId, try with hardcoded default value
        return 0

    def get_tts_timescale(self) -> str: #@TODO we might need a method to get values like this
        """Returns bot tts time scale"""
        # DotBot timeScale has higher priority. external configurations can't change this
        if self.dotbot.tts.get('timeScale') is not None:
            return self.dotbot.tts['timeScale']
        # from request 
        if self.params.get('ttsTimeScale') is not None:
            return self.params['ttsTimeScale']
        # If there is no time scale set, check fo default in DotBot
        if self.dotbot.tts.get('defaultTimeScale') is not None:
            return self.dotbot.tts['defaultTimeScale']
        # If there is not even default set, try with hardcoded default value
        return 100

    def get_http_locale(self) -> str:
        """ @TODO """
        return None

    def escape_html_from_text(self, bbot_response: list) -> list:
        """Escape HTML chars from text objects"""
        response = []
        for br in bbot_response:
            response_type = list(br.keys())[0]
            if response_type == 'text':
                br['text'] = html.escape(br['text'])
            response.append(br)
        
        return response

