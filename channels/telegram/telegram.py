"""."""
import telepot
import logging
import logging.config


class Telegram:
    """Translates telegram request/response to flow"""

    def __init__(self, config: dict, dotbot: dict) -> None:
        """
        
        """
        self.config = config
        self.dotbot = dotbot
        self.dotdb = None #
        self.api = None

        self.logger = logging.getLogger("channel_telegram")

        self.response_type_fnc = {
            'text': self.send_text,
            'image': self.send_image,
            'video': self.send_video,
            'audio': self.send_audio
        }

    def set_api_token(self, token: str):
        self.api = telepot.Bot(token)


    def to_bbot_request(self, request: str) -> str:
        return {'text': request}

    ### Responses

    def send_response(self, bbot_response: dict):
        """
        """
        # @TODO check if we can avoid sending separate api request for each text if there are more than one
        for br in bbot_response['output']:
            # Buttons needs special treatment because telegram ask for mandatory text output with it
            # So we need to find and send text output at the same time
            if 'buttons' in br.keys():
                self.send_buttons(br['buttons'], br['text'])
                br.pop('text', None)
                br.pop('buttons', None)

            for response_type in br.keys():
                res = br[response_type]

                if response_type == 'card':
                    response_type = res[0]['type']

                if callable(self.response_type_fnc.get(response_type)):
                    self.response_type_fnc[response_type](res)

    def send_text(self, texts: list):
        """
        """                
        for text in texts:
            if text:
                self.api.sendMessage(self.user_id, text, parse_mode='Markdown')
            else:
                self.logger.error("Trying to send empty message to Telegram")

    def send_image(self, image: dict):
        """
        """
        image = image[0]
        caption = f"*{image['title']}*"
        if image['subtitle']: caption += f"\n{image['subtitle']}"
        self.api.sendPhoto(self.user_id, image['info']['media_uri'], caption=caption, parse_mode='Markdown',
                           disable_notification=None, reply_to_message_id=None, reply_markup=None)
        
    def send_video(self, video: dict):
        """
        """
        video = video[0]
        caption = f"*{video['title']}*"
        if video['subtitle']: caption += f"\n{video['subtitle']}"
        self.api.sendVideo(self.user_id, video['info']['media_uri'], duration=None, width=None, height=None,
                           caption=caption, parse_mode='Markdown', supports_streaming=None, disable_notification=None, reply_to_message_id=None, reply_markup=None)

    def send_audio(self, audio: dict):
        """
        """
        audio = audio[0]
        caption = f"*{audio['title']}*"
        if audio['subtitle']: caption += f"\n{audio['subtitle']}"
        #self.telegram.sendAudio(self.user_id, audio['info']['media_uri'], caption=caption, parse_mode='Markdown', duration=None, performer=None, 
        #   title="Title?", disable_notification=None, reply_to_message_id=None, reply_markup=None)
        self.api.sendVoice(self.user_id, audio['info']['media_uri'], caption=caption, parse_mode='Markdown', duration=None,
                           disable_notification=None, reply_to_message_id=None, reply_markup=None)
        
        
    def send_buttons(self, buttons: dict, text: list):
        """
        """        
        from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
        telegram_buttons = []
        for button in buttons:
            telegram_buttons.append([InlineKeyboardButton(text=button['label'], callback_data=button['input'])])                
        keyboard = InlineKeyboardMarkup(inline_keyboard=telegram_buttons)        
        self.api.sendMessage(self.user_id, text[0], reply_markup=keyboard)


    ### Request

    def get_user_id(self, request: dict):
        if request.get('message'): #regular text
            self.user_id = request['message']['from']['id']
            return self.user_id

        if request.get('callback_query'): # callback from a button click
            return request['callback_query']['from']['id']

    def get_message(self, request: dict):
        if request.get('message'): #regular text
            return request['message']['text']

        if request.get('callback_query'): # callback from a button click
            return request['callback_query']['data']


    ### Misc

    def webhooks_check(self):
        """
        This will check and start all webhooks for telegram enabled bots
        """

        # get al telegram enabled bots
        telegram_dotbots = self.dotdb.find_dotbots_by_channel('telegram')

        # cert file only used on local machines with self-signed certificate
        cert_file = open(self.config['cert_filename'], 'rb') if self.config['cert_filename'] else None

        for td in telegram_dotbots:
            self.logger.debug('Checking Telegram webhook for botid ' + td.id + '...')

            self.set_api_token(td.dotbot['channels']['telegram']['token'])

            # build webhook url
            url = self.config['webhook_uri'].replace('{dotbotid}', td.id)

            # check webhook current status (faster than overriding webhook)
            webhook_info = self.api.getWebhookInfo()
            webhook_notset = webhook_info['url'] == ''
            if webhook_info['url'] != url and not webhook_notset: # webhook url is set and wrong
                self.logger.warning('Telegram webhook set is invalid (' + webhook_info['url'] + '). Deleting webhook...')
                delete_ret = self.api.deleteWebhook()
                if delete_ret:
                    self.logger.warning("Successfully deleted.")
                else:
                    error = "Couldn't delete the invalid webhook"
                    self.logger.error(error)
                    raise Exception(error)
                webhook_notset = True
            if webhook_notset: # webhook is not set
                self.logger.info(f'Setting webhook for bot id {td.id} with webhook url {url}')
                set_ret = self.api.setWebhook(url=url, certificate=cert_file)
                if set_ret:
                    self.logger.info("Successfully set.")
                else:
                    error = "Couldn't set the webhook"
                    self.logger.error(error)
                    raise Exception(error)
            else:
                self.logger.debug("Webhook is correct")

