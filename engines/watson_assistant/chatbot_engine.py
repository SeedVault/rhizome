import logging
from bbot.core import BBotCore, ChatbotEngine, ChatbotEngineError, BBotLoggerAdapter
import ibm_watson
import ibm_cloud_sdk_core
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

class WatsonAssistant(ChatbotEngine):
    """
    BBot engine that calls external program.
    """

    def __init__(self, config: dict, dotbot: dict) -> None:
        """
        Initialize the plugin.

        :param config: Configuration values for the instance.
        """
        super().__init__(config, dotbot)

        self.dotdb = None

    def init(self, core: BBotCore):
        """
        Initializebot engine 
        """
        super().init(core)

        self.logger = BBotLoggerAdapter(logging.getLogger('watson_cbe'), self, self.core)

        # Set up Assistant service.
        authenticator = IAMAuthenticator(self.dotbot.chatbot_engine['iamApikey'])        
        self.service = ibm_watson.AssistantV2(authenticator=authenticator, version = '2019-02-28')
        self.service.set_service_url(self.dotbot.chatbot_engine['url'])
        
        self.logger.debug("Connection: " + str(self.service))
        
    def get_response(self, request: dict) -> dict:
        """
        Return a response based on the input data.

        :param request: A dictionary with input data.
        :return: A response to the input data.
        """
        
        self.request = request

        input_text = request['input']['text']
        user_id = request['user_id']
        bot_id = request['bot_id']

        session = self.get_bot_session(user_id, bot_id)
        session_id = session['session_id']

        response = {}
        try:
            response = self.get_assistant_response(session_id, request['input'])
        except ibm_cloud_sdk_core.api_exception.ApiException as e:  # This means we are trying to use an expired session 
                                                                    # @TODO I don't know how to test this before. try to improve it.
            # create a new session (but dont delete context!) and try again  
            self.logger.debug('Session has timed out. Try to create a new one')
            session = self.get_bot_session(user_id, True)
            session_id = session['session_id']    
            response = self.get_assistant_response(session_id, request['input'])

        self.logger.debug("Response: " + str(response))

        output = ""
        if response['output']['generic']:
            if response['output']['generic'][0]['response_type'] == 'text':
             output = response['output']['generic'][0]['text']

        self.core.bbot.text(output)

    def get_assistant_response(self, session_id: str, rinput: dict):
        """
        Returns response from bot engine

        :param session_id: The session id
        :param rinput: The request dict
        :return: A dict 
        """
        return self.service.message(
            self.dotbot.chatbot_engine['assistantId'],
            session_id,
            input={'text': rinput['text']}
        ).get_result()

    def get_bot_session(self, user_id: str, bot_id: str, renew: bool=False):
        """
        Returns session data both session id and context
        If there is no session on db we create one

        :param user_id: A string with the user id
        :param renew: A bool to indicate if we need to renew the session id (watson asisstant has a timeout and we have to get a new one when that happens)
        :return: A dict 
        """
        session = self.dotdb.get_watson_assistant_session(user_id, bot_id)

        if session:
            self.logger.debug("Found old session: " + str(session))
        else:
            session = {'session_id': None, 'context': {}}
            self.logger.debug("No session found. Generating a new one.")
        
        if renew:               
            session['session_id'] = None

        if not session.get('session_id'):                        
            session_id = self.service.create_session(assistant_id = self.dotbot.chatbot_engine['assistantId']).get_result()['session_id']                            
            session['session_id'] = session_id
            self.logger.debug("Created new session: " + session_id)               
            self.dotdb.set_watson_assistant_session(user_id, bot_id, session_id, session['context']) # context might have data if we are renewing session
                    
        return session

