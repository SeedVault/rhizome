"""BBot Web Application."""

import sys, traceback
import os
import json
import logging
import logging.config

from flask_cors import CORS, cross_origin
from flask import Flask, request, render_template
from collections import defaultdict
from bbot.core import BBotCore, ChatbotEngine, Plugin, BBotException
from bbot.config import load_configuration


"""Create and configure an instance of the application."""
app = Flask(__name__)
CORS(app, support_credentials=True)

config_path = os.path.abspath(os.path.dirname(__file__) + "../../../instance")
config = load_configuration(config_path, "BBOT_ENV")
app.config.from_mapping(config)
w_config = config["channel_restful"]
restful = Plugin.load_plugin(w_config)
logging.config.dictConfig(config['logging'])
logger = logging.getLogger("channel_restful")

@app.route('/restful_channel', methods=['POST'])
@cross_origin(supports_credentials=True)
def rest():                                       # pylint: disable=W0612
    try:
        print('--------------------------------------------------------------------------------------------------------------------------------')
        restful.params = request.get_json(force=True)
        logger.debug("Received request " + str(restful.params))
        
        user_id = restful.params.get('userId')
        bot_id = restful.params.get('botId')
        org_id = restful.params.get('orgId')
        pub_token = restful.params.get('pubToken')        
        input_params = restful.params['input']
        
        # get publisher user id from token
        pub_bot = restful.dotdb.find_publisherbot_by_publisher_token(pub_token)
        if not pub_bot:
            raise Exception('Publisher not found')
        logger.debug('Found subscription id: ' + str(pub_bot.id) + ' - publisher name: ' + pub_bot.publisher_name + ' - for bot name: ' + pub_bot.bot_name + ' - bot id:' + pub_bot.bot_id)
        pub_id = pub_bot.publisher_name
        
        # if 'runBot' in params:
        #    run_bot = restful.params['runBot']
       
        dotbot = restful.dotdb.find_dotbot_by_bot_id(pub_bot.bot_id)                    
        if not dotbot:
            raise Exception('Bot not found')
        bot_id = dotbot.bot_id
        # build extended dotbot 
        dotbot.services = pub_bot.services
        dotbot.channels = pub_bot.channels
        dotbot.botsubscription = pub_bot

        restful.dotbot = dotbot # needed for methods below
        bot = BBotCore.create_bot(config, dotbot)
        input_text = ""
        #for input_type, input_value in input_params.items():
            # bot.get_response(input_type, input_value)
        #    _ = input_type
        #    input_text = input_text + input_value
        req = bot.create_request(input_params, user_id, bot_id, org_id, pub_id)
        bbot_response = bot.get_response(req)
        
        #response = defaultdict(lambda: defaultdict(dict))    # create a response dict with autodict property
        #for br in bot_response.keys():
        #   response[br] = bot_response[br]
        
        #response['output'] = restful.escape_html_from_text(response['output'])
        #logger.debug('Escaped response text: ' + str(response['output']))
        
        if restful.params.get('ttsEnabled'):          
            bbot_response['tts'] = {}
            if not restful.tts:
                bbot_response['errors'].append({'message': 'No TTS engine configured for this bot.'})                      
            else:
                #retrieve TTS audio generated from all texts from bbot output                    
                restful.tts.voice_locale = get_locale()
                restful.tts.voice_id = get_tts_voice_id()
                all_texts = BBotCore.get_all_texts_from_output(bbot_response['output'])                
                bbot_response['tts']['url'] = restful.tts.get_speech_audio_url(all_texts, restful.params.get('ttsTimeScale', 100))           

        if restful.params.get('actrEnabled', None): 
            bbot_response['actr'] = {}
            if not restful.tts:
                response['errors'].append({'message': 'No ACTR engine configured for this bot.'})                      
            else:
                all_texts = BBotCore.get_all_texts_from_output(bbot_response['output'])                                    
                bbot_response['actr'] = restful.actr.get_actr(
                    all_texts,                         
                    get_locale(),
                    get_tts_voice_id(), 
                    get_timescale())


        if restful.params.get('debugEnabled') is None:                
            if 'debug' in bbot_response:                     
                del bbot_response['debug']

    except Exception as e:
        if not isinstance(e, BBotException): # If BBotException means the issue is in botland, not rhizome
            logger.critical(str(e) + "\n" + str(traceback.format_exc()))            
        else:
            pass # we should alert the botdev
        if config['environment'] == 'development':
            bbot_response = {
                'output': [{'text': str(e)}], #@TODO use bbot.text() 
                'error': {'traceback': str(traceback.format_exc())}
                }
        else:
            bbot_response = {'output': [{'text': 'An error happened. Please try again later.'}]}
            # @TODO this should be configured in dotbot
            # @TODO let bot engine decide what to do?
        
    logger.debug("Response from restful channel: " + str(bbot_response))
    return json.dumps(bbot_response)

def get_locale() -> str:
    """Returns locale for tts service. It first check on params if no value provided it fallsback to http header."""
    dotbot_lc = restful.dotbot.get('enabledLocales', [])
    
    # get current locale
    param_lc = restful.params.get('locale', None) 
    curr_lc = None
    if param_lc:
        if param_lc in dotbot_lc:
            curr_lc = param_lc  # we got locale based on client choice
    else:  
        # check http header locale to see if it's enabled by the bot
        # @TODO
        curr_lc = None

    if not curr_lc:
        #client locale is not enabled by the bot. check if there is any language available for it anyway
        #@TODO

        curr_lc = restful.dotbot.get('defaultLocale', 'en_US')

    return curr_lc

def get_tts_voice_id() -> str:
    """Returns bbot voice id. First check on params. Default value is 1"""
    return restful.dotbot.get('ttsVoiceId', None) or restful.params.get('ttsVoiceId', None) or 0

def get_timescale() -> str: #@TODO we might need a method to get values like this
    """Returns bbot voice id. First check on params. Default value is 1"""
    return restful.dotbot.get('ttsTimeScale', None) or restful.params.get('ttsTimeScale', None) or 100


def get_http_locale() -> str:
    """ @TODO """
    return None


@app.route('/TestWebChatBot')
def test():                                     # pylint: disable=W0612
    return render_template('test.html')



