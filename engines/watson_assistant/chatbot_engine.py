import logging
from bbot.core import BBotCore, ChatbotEngine, ChatbotEngineError, BBotLoggerAdapter
import ibm_watson

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
        self.service = ibm_watson.AssistantV2(
            iam_apikey = self.dotbot['watsonassistant']['iamApikey'],
            url = self.dotbot['watsonassistant']['url'],
            version = '2019-02-28'
        )
        self.logger.debug("Conexion: " + str(self.service))
        
    def get_response(self, request: dict) -> dict:
        """
        Return a response based on the input data.

        :param request: A dictionary with input data.
        :return: A response to the input data.
        """
        
        self.request = request

        input_text = request['input']['text']
        user_id = request['user_id']

        session = self.get_bot_session(user_id)
        session_id = session['session_id']

        response = self.service.message(
            self.dotbot['watsonassistant']['assistantId'],
            session_id,
            input={'text': input_text}
        ).get_result()

        self.logger.debug("Response: " + str(response))

        output = ""
        if response['output']['generic']:
            if response['output']['generic'][0]['response_type'] == 'text':
             output = response['output']['generic'][0]['text']

        self.core.bbot.text(output)

    def get_bot_session(self, user_id):

        session = self.dotdb.get_watson_assistant_session(user_id)        
        if not session:                        
            session_id = self.service.create_session(assistant_id = self.dotbot['watsonassistant']['assistantId']).get_result()['session_id']
            session = {}
            session['session_id'] = session_id
            self.logger.debug("Created new session: " + session_id)
            self.dotdb.set_watson_assistant_session(user_id, session_id, {})
        else:
            self.logger.debug("Found old session: " + str(session))
        return session
