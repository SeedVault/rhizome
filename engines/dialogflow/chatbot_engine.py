"""BBot engine that calls dialogflow."""
import logging
from bbot.core import BBotCore, ChatbotEngine, ChatbotEngineError, BBotLoggerAdapter

import dialogflow
from google.oauth2.service_account import Credentials

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

        credentials = Credentials.from_service_account_info(self.dotbot['dialogflow']['serviceAccount'])
        self.session_client = dialogflow.SessionsClient(credentials=credentials)
        
    def get_response(self, request: dict) -> dict:
        """
        Return a response based on the input data.

        :param request: A dictionary with input data.
        :return: A response to the input data.
        """
        
        self.request = request

        input_text = request['input']['text']
        input_text.replace("\n", " ")
        
        session_id = request['user_id']
        language_code = 'en-US'
        
        """
        Returns the result of detect intent with texts as inputs.

        Using the same `session_id` between requests allows continuation
        of the conversaion.
        """
                
        session = self.session_client.session_path(self.dotbot['dialogflow']['serviceAccount']['project_id'], session_id)
        
        text_input = dialogflow.types.TextInput(
            text=input_text, language_code=language_code)

        query_input = dialogflow.types.QueryInput(text=text_input)

        response = self.session_client.detect_intent(
            session=session, query_input=query_input)
                
        self.logger.debug('Detected intent: {} (confidence: {})'.format(
            response.query_result.intent.display_name,
            response.query_result.intent_detection_confidence))
            
        self.core.bbot.text(response.query_result.fulfillment_text)


