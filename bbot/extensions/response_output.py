""""""
import random
import logging
import box
from bbot.core import ChatbotEngine, BBotException, BBotCore, BBotLoggerAdapter

class BBotResponseOutput():
    """BBot response output objects"""

    def __init__(self, config: dict, dotbot: dict) -> None:
        """
        Initialize the plugin.
        """
        self.config = config
        self.dotbot = dotbot

        self.logger_level = ''

        self.core = None
        self.logger = None

        self.functions = ['text', 'outputHasText', 'imBack', 'openUrl', 'suggestedActions', 'imageCard', 'thumbnailCard', 'videoCard', 'audioCard', 'heroCard']

    def init(self, core: BBotCore):
        """
        Initializes extension

        :param bot:
        :return:
        """
        self.core = core
        self.logger = BBotLoggerAdapter(logging.getLogger('core.ext.response'), self, self.core.bot, 'bbotoutput')                

        for f in self.functions:
            core.register_function(f, {'object': self, 'method': f, 'cost': 0, 'register_enabled': False})
            
    def text(self, args, f_type):
        """
        Returns BBot text output object

        :param args:
        :return:
        """

        if len(args) == 0:
            raise BBotException({'code': 200, 'function': 'text', 'arg': 0, 'message': 'Text in arg 0 is missing.'})

        msg_count = len(args)
        if msg_count > 1:  # multiple output, choose a random one
            msg_idx = random.randint(0, msg_count - 1)
        else:
            msg_idx = 0

        msg = self.core.resolve_arg(args[msg_idx], f_type, True)  # no need to resolve arg before this
        bbot_response = {
            'type': 'message',
            'text': str(msg)
            }
        self.core.add_output(bbot_response)
        return bbot_response

    def outputHasText(self, args, f_type):
        """
        Returns True or False if the output has the specified text
        """
        for o in self.core.response['output']:            
            if o.get('text') and o['text'] == args[0]:
                return True
        return False

    def thumbnailCard(self, args, f_type):        
        card = self._mediaCard(args, f_type, "images")
        card['attachments'][0]['contentType'] = "application/vnd.microsoft.card.thumbnail"
        self.core.add_output(card)

    def imageCard(self, args, f_type):
        return self.thumbnailCard(args, f_type)

    def videoCard(self, args, f_type):
        card = self._mediaCard(args, f_type)
        card['attachments'][0]['contentType'] = "application/vnd.microsoft.card.video"
        self.core.add_output(card)

    def audioCard(self, args, f_type):
        card = self._mediaCard(args, f_type)
        card['attachments'][0]['contentType'] = "application/vnd.microsoft.card.audio"
        self.core.add_output(card)

    def _mediaCard(self, args, f_type, media_elm: str="media"):
        """
        Returns BBot video object

        :param args:
        :param f_type:
        :return:
        """
        try:
            media_url = self.core.resolve_arg(args[0], f_type, True)
        except IndexError:
            raise BBotException({'code': 210, 'function': 'mediaCard', 'arg': 0, 'message': 'Media URL is missing.'})        
        try:
            title = self.core.resolve_arg(args[1], f_type, True)
        except IndexError:
            title = ""
        try:
            subtitle = self.core.resolve_arg(args[2], f_type, True)
        except IndexError:
            subtitle = ""
        try:
            text = self.core.resolve_arg(args[3], f_type, True)
        except IndexError:
            text = ""            
        try:
            buttons = self.core.resolve_arg(args[4], f_type, True)
        except IndexError:
            buttons = []
        try:
            image_url = self.core.resolve_arg(args[5], f_type, True)
        except IndexError:
            image_url = ""
        
        bbot_response = {
            'type': 'message',
            'attachments': [
                {          
                    "contentType": "",
                    "content": {
                        "subtitle": subtitle,
                        "text": text,
                        "image": image_url,
                        "title": title,
                        media_elm: [
                            {
                                "url": media_url
                            }
                        ],
                        "buttons": buttons
                    }
                }
                
            ]
        }
        
        return bbot_response

    def suggestedActions(self, args, f_type):
        errors = []
        try:
            actions = self.core.resolve_arg(args[0], f_type)
        except IndexError:
            errors.append({'code': 240, 'function': 'suggestedAction', 'arg': 0, 'message': 'suggestedAction actions missing.'})
        if errors:
            raise BBotException(errors)

        if type(actions) is not list:
            actions = [actions]

        for i in range(len(actions)):                
            if type(actions[i]) is not box.Box: # if it's not an object (dict are box.Box class here)
                if type(actions[i]) is str: # and it's a string, apply it as imBack
                    actions[i] = self.imBack(actions[i])
                else:
                    raise BBotException("suggestedActions function accepts strings or imBack objects only")

        bbot_response = {
            'suggestedActions': {
                'actions': actions
            }
        }
        self.core.add_output(bbot_response, True)  # Adds suggestion to last output

    def imBack(self, args, f_type):
        """
        Returns BBot imBack object (must be used within suggestedAction)

        :param args:
        :return:
        """
        errors = []
        try:
            title = self.core.resolve_arg(args[0], f_type)
        except IndexError:
            errors.append({'code': 240, 'function': 'imBack', 'arg': 0, 'message': 'imBack title missing.'})
        try:
            value = self.core.resolve_arg(args[1], f_type)
        except IndexError:
            value = title

        if errors:
            raise BBotException(errors)

        response = {
            "type": "imBack",
            "title": title,
            "value": value            
        }                    
        return response

    def openUrl(self, args, f_type):
        """
        Returns BBot openUrl object (must be used within suggestedAction)

        :param args:
        :return:
        """
        errors = []
        try:
            title = self.core.resolve_arg(args[0], f_type)
        except IndexError:
            errors.append({'code': 240, 'function': 'openUrl', 'arg': 0, 'message': 'openUrl title missing.'})
        try:
            value = self.core.resolve_arg(args[1], f_type)
        except IndexError:
            value = title

        if errors:
            raise BBotException(errors)

        response = {
            "type": "openUrl",
            "title": title,
            "value": value            
        }                    
        return response

    def heroCard(self, args, f_type):
        """
        Returns BBot hero card 

        :param args:
        :return:
        """
        errors = []        
        try:
            image = self.core.resolve_arg(args[0], f_type)
        except IndexError:
            errors.append({'code': 240, 'function': 'heroCard', 'arg': 0, 'message': 'heroCard image missing.'})
        try:
            title = self.core.resolve_arg(args[1], f_type)
        except IndexError:
            title = None
        try:
            subtitle = self.core.resolve_arg(args[2], f_type, True)
        except IndexError:
            subtitle = None
        try:
            text = self.core.resolve_arg(args[3], f_type, True)
        except IndexError:
            text = None      
        try:
            buttons = self.core.resolve_arg(args[4], f_type)
        except IndexError:
            buttons = None
        if errors:
            raise BBotException(errors)

        content = {}
        content['images'] = [{'url': image}]        
        if title:
            content['title'] = title
        if subtitle:
            content['subtitle'] = subtitle
        if text:
            content['text'] = text
        if buttons:
            content['buttons'] = buttons

        bbot_response = {
            'type': 'message',
            'attachments': [
                {
                    "contentType": "application/vnd.microsoft.card.hero",
                    "content": content
                }        
            ]
        }
        self.core.add_output(bbot_response)
