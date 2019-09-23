"""Bot engine based on Wolfram Alpha Short Answers API."""
import logging
import requests
from bbot.core import ChatbotEngine, ChatbotEngineError, BBotLoggerAdapter, Plugin, BBotCore


class WolframAlphaShortAnswers(ChatbotEngine):
    """
    """

    def __init__(self, config: dict, dotbot: dict) -> None:
        """
        Initialize the plugin.

        :param config: Configuration values for the instance.
        """
        super().__init__(config, dotbot)

    def init(self, core: BBotCore):
        """
        Initializes bot
        """
        super().init(core)
        self.logger = BBotLoggerAdapter(logging.getLogger('wolframsa_cbe'), self, self.core)
                
    def get_response(self, request: dict) -> dict:
        """
        Return a response based on the input data.

        :param request: A dictionary with input data.
        :return: A response to the input data.
        """        
        super().get_response(request)
                               
        appid = self.dotbot['wolfram_alpha_short_answers']['appId']
        query = self.request['input']['text']
        self.logger.debug('Querying to Wolfram Alpha Short Answers API with query: ' + query)
        r = requests.get(f'http://api.wolframalpha.com/v1/result?appid={appid}&i={query}')
        self.logger.debug('Wolfram Alpha Short Answers API response code: ' + str(r.status_code) + ' - message: ' + str(r.text)[0:300])
        if r.status_code == 200:
            aw = r.text
        if r.status_code == 501:
            aw = r.text # Because this bot is designed to return a single result, this message may appear if no sufficiently short result can be found. You may occasionally receive this answer when requesting information on topics that are restricted or not covered.
        
        self.core.bbot.text(aw)
        return self.response
        


