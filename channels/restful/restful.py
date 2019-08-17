import logging
import html

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
        
        self.params = {}

        self.logger = logging.getLogger("channel_restful")


    def escape_html_from_text(self, bbot_response: list) -> list:
        """Escape HTML chars from text objects"""
        response = []
        for br in bbot_response:
            response_type = list(br.keys())[0]
            if response_type == 'text':
                br['text'] = html.escape(br['text'])
            response.append(br)
        
        return response

