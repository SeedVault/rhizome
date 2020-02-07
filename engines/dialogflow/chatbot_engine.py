"""BBot engine that calls dialogflow."""
import logging
import json
from bbot.core import BBotCore, ChatbotEngine, ChatbotEngineError, BBotLoggerAdapter

import dialogflow
from google.oauth2.service_account import Credentials
from google.protobuf.json_format import MessageToDict

class DialogFlow(ChatbotEngine):
    """
    BBot engine that calls external program.
    """

    def __init__(self, config: dict, dotbot: dict) -> None:
        """
        Initialize the plugin.

        :param config: Configuration values for the instance.
        """
        super().__init__(config, dotbot)

    def init(self, core: BBotCore):
        """
        Initializebot engine 
        """
        super().init(core)

        self.logger = BBotLoggerAdapter(logging.getLogger('dialogfl_cbe'), self, self.core)
        
        self.service_account = json.loads(self.dotbot.chatbot_engine['serviceAccount'])
        self.platform = None

        self.available_platforms = {
            'google_assistant': 'ACTIONS_ON_GOOGLE',
            'facebook': 'FACEBOOK',
            'slack': 'SLACK',
            'telegram': 'TELEGRAM',
            'skype': 'SKYPE'
        }
        
        credentials = Credentials.from_service_account_info(self.service_account)
        self.session_client = dialogflow.SessionsClient(credentials=credentials)
        
    def get_response(self, request: dict) -> dict:
        """
        Return a response based on the input data.

        :param request: A dictionary with input data.
        :return: A response to the input data.
        """
        
        super().get_response(request)

        self.platform = self.get_platform()

        input_text = request['input']['text']
        input_text.replace("\n", " ")
        
        session_id = request['user_id']
        language_code = 'en-US'
        
        """
        Returns the result of detect intent with texts as inputs.

        Using the same `session_id` between requests allows continuation
        of the conversaion.
        """
                
        session = self.session_client.session_path(self.service_account['project_id'], session_id)
        
        text_input = dialogflow.types.TextInput(
            text=input_text, language_code=language_code)

        query_input = dialogflow.types.QueryInput(text=text_input)

        response_class = self.session_client.detect_intent(
            session=session, query_input=query_input)

        response = MessageToDict(response_class)

        self.logger.debug('Response: ' + json.dumps(response, indent=4, sort_keys=True))
                
        self.logger.debug('Detected intent: {} (confidence: {})'.format(
            response['queryResult']['intent']['displayName'],
            response['queryResult']['intentDetectionConfidence']))
                    
        self.logger.debug('Looking for media cards for platform: ' + str(self.platform))
        found_text = False
        for fm in response['queryResult']['fulfillmentMessages']:
            # get text response
            text = None
            if fm.get('platform') == self.platform: # using get() because dialogflow is sending some objects without platform property...?(or is MessageToDict()?)
                if fm.get('text'):                    
                    text = fm['text']['text'][0]                    
                elif fm.get('simpleResponses'): # text for google assistant
                    text = fm['simpleResponses']['simpleResponses'][0]['textToSpeech']
                
                if text:
                    found_text = True
                    self.core.bbot.text(text)
                
                # get card/media and convert it to heroCard() arguments                            
                if fm.get('card'): # telegram, facebook
                    title = fm['card'].get('title')
                    image_url = fm['card'].get('imageUri')
                    subtitle = fm['card'].get('subtitle')
                    text = fm['card'].get('text')
                    buttons = []
                    if fm['card'].get('buttons'):                        
                        for b in fm['card']['buttons']:
                            buttons.append(self.core.bbot.imBack(b['text'], b.get('postback')))

                    self.core.bbot.heroCard(image_url, title, subtitle, text, buttons)
                                
                if fm.get('basicCard'): # google assistant
                    bcard = fm['basicCard']
                    title = bcard.get('title')
                    subtitle = bcard.get('subtitle')
                    text = bcard.get('formattedText')
                    image_url = bcard.get('image', {}).get('imageUri')
                    buttons = []
                    if bcard.get('buttons'):
                        for b in bcard['buttons']:
                            if 'openUriAction' in b:
                                buttons.append(self.core.bbot.openUrl(b['title'], b['openUriAction']['uri']))

                    self.core.bbot.heroCard(image_url, title, subtitle, text, buttons)
                    
                if fm.get('image'): #slackware
                    self.core.bbot.imageCard(fm['image']['imageUri'])
      
                # get suggestions (chips for google assistat)
                if fm.get('suggestions'):
                    suggested_actions = []
                    for sa in fm['suggestions']['suggestions']:
                        suggested_actions.append(self.core.bbot.imBack(sa['title']))
                    
                    self.core.bbot.suggestedActions(suggested_actions)

                # get quick replies (skype) -- it allows just one quick reply from gui??
                if fm.get('quickReplies'):
                    self.core.bbot.suggestedActions(self.core.bbot.imBack(fm['quickReplies']['title'], fm['quickReplies']['quickReplies'][0]))
                        
        if not found_text: # if specific platform text was not defined, show default 
            self.core.bbot.text(response['queryResult'].get('fulfillmentText', ''))

    def get_platform(self):
        # first check if there is a forcePlatform set. if not, take channelId from channel
        current_platform = self.get_dialogflow_platform_from_channel_id(self.channel_id)        
        force_platform = self.dotbot.chatbot_engine.get('forcePlatform')
        if force_platform:
            self.logger.debug('Platform should be "' + str(current_platform) + '" based in current channelId "' + self.channel_id + '" but...')
            self.logger.debug('Setting forced by config platform to: ' + str(force_platform))
            platform = force_platform
        else:            
            platform = current_platform
            self.logger.debug('Setting platform to "' + str(platform) + '" based on current channelId "' + str(self.channel_id) + '"')
                
        # if selected channelId is not supported (might be some channel from restful like hadron or webchat) will set platform with defaultPlatform value from dotbot chatbot_engine object 
        if platform not in self.available_platforms.values():                                        
            self.logger.debug('Platform "' + str(platform) + '" is invalid. Setting platform to default value: ' +str(self.dotbot.chatbot_engine.get('defaultPlatform')))
            platform = self.dotbot.chatbot_engine.get('defaultPlatform') 
        
        #if platform not in self.available_platforms.values():                                        
        #    raise Exception("Dialoflowg platform not supported: " + str(platform))

        return platform

    def get_dialogflow_platform_from_channel_id(self, channel_id: str):                
        return self.available_platforms.get(channel_id)
    