"""Sentiment match."""
import http.client, urllib.request, urllib.parse, urllib.error, base64
import requests
from flow.chatbot_engine import Extension, FlowError, extensions_cache

class SentimentMatch(Extension):
    """SentimentMatch plugin"""

    def __init__(self, flow):
        super().__init__(flow)
        class_name = self.__class__.__module__ + '.' + self.__class__.__name__
        flow.register_dot_flow_function('sentiment', {
            'class': class_name, 'method': 'match'})

        
    def match(self, args) -> bool:
        """
        Matches the sentiment with the user input
        """
        sentiment_score = args[0]
        input_text = args[1]
        
        score = self.get_sentiment_analysis(input_text)

        # azure returns values from 0 to 1 float and flow expects values from -5 to 5 integer
        flow_score = int(round(score * 10, 0)) - 5
            
        return int(sentiment_score) == flow_score
            
        
    @extensions_cache
    def get_sentiment_analysis(self, input_text: str) -> float:
        headers = {
            # Request headers
            'Content-Type': 'application/json',
            'Ocp-Apim-Subscription-Key': self.flow.azure_subscription_key,
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

        try:
            r = requests.post(f'https://{self.flow.azure_location}.api.cognitive.microsoft.com/text/analytics/v2.0/sentiment', json=payload, headers=headers)
            return r.json()['documents'][0]['score']

        except ConnectionError as e:
            print("[Errno {0}] {1}".format(e.errno, e.strerror))   

