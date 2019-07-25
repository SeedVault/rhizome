
import requests
import logging
from bbot.core import ChatbotEngine, BBotException, BBotCore, BBotExtensionException
from engines.dotflow2.chatbot_engine import DotFlow2LoggerAdapter


class DotFlow2MSCSSentimentAnalysis():
    """ChatScript DotFlow2 function"""

    def __init__(self, config: dict, dotbot: dict) -> None:
        """
        Initialize class
        """
        self.config = config
        self.dotbot = dotbot

        self.bot = None
        self.logger = None
        
        self.azure_location = ''
        self.azure_subscription_key = ''
        self.logger_level = ''

    def init(self, bot: ChatbotEngine):
        """
        Initialize extension

        :param bot:
        :return:
        """
        self.bot = bot
        self.logger = DotFlow2LoggerAdapter(logging.getLogger('df2_ext.ssent_an'), self, self.bot, '$simpleSentimentAnalysis')
        bot.register_dotflow2_function('simpleSentimentAnalysis', {'object': self, 'method': 'df2_simpleSentimentAnalysis', 'cost': 0.5, 'register_enabled': True})
        
    def df2_simpleSentimentAnalysis(self, args, f_type):
        """
        Detects sentiment analysis using Microsoft Cognitive Services

        :param args:
        :param f_type:
        :return:
        """
        try:
            input_text = self.bot.resolve_arg(args[0], f_type)
        except IndexError:
            input_text = self.bot.call_dotflow2_function('input', [], 'R')  # optional. default input()

        headers = {
            # Request headers
            'Content-Type': 'application/json',
            'Ocp-Apim-Subscription-Key': self.azure_subscription_key,
        }
        payload = {
            "documents": [
                {
                    "language": "en",
                    "id": "1",
                    "text": input_text
                }
            ]
        }

        self.logger.debug('Requesting sentiment analysis score to Microsoft Cognitive Services...')
    
        r = requests.post(
            f'https://{self.azure_location}.api.cognitive.microsoft.com/text/analytics/v2.0/sentiment',
            json=payload, headers=headers)
        response = r.json()
        self.logger.debug('Returned response: ' + str(response))
    
        if 'error' in response:
            self.logger.critical(response['error']['message'])
            raise BBotExtensionException(response['error']['message'], BBotCore.FNC_RESPONSE_ERROR)

        score = response['documents'][0]['score']            
        return score
