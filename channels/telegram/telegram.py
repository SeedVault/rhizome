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
            'none': self.none,
            'text': self.send_text,
            'image': self.send_image,
            'video': self.send_video,
            'audio': self.send_audio,
            'buttons': self.send_buttons
        }

    def set_api_token(self, token: str):
        self.api = telepot.Bot(token)


    def to_bbot_request(self, request: str) -> str:
        return {'text': request}

    ### Responses

    def send_response(self, bbot_response: dict):
        """
        Parses BBot output response and sends content to telegram
        """
        # @TODO check if we can avoid sending separate api request for each text if there are more than one

        bbot_output = bbot_response['output']

        t_output = self.buttons_process(bbot_output)

        # Iterate through bbot responses
        for br in t_output:
            response_type = list(br.keys())[0]
            if callable(self.response_type_fnc.get(response_type)):
                self.response_type_fnc[response_type](br)
            else:
                self.logger.warning('Unrecognized BBot output response "' + response_type)

    def none(self, arg):
        """

        :return:
        """
        pass

    def send_text(self, text: list):
        """
        Sends text to telegram
        """
        text = text['text']
        if type(text) is str and text:
            self.api.sendMessage(self.user_id, text, parse_mode='Markdown')
        else:
            self.logger.error("Trying to send empty message to Telegram")

    def send_image(self, image: dict):
        """
        Sends image to telegram
        """
        image = image['image']
        caption = None
        if image.get('title'):
            caption = f"*{image['title']}*"
            if image.get('subtitle'):
                caption += f"\n{image['subtitle']}"

        self.api.sendPhoto(self.user_id, image['url'], caption=caption, parse_mode='Markdown',
                           disable_notification=None, reply_to_message_id=None, reply_markup=None)
        
    def send_video(self, video: dict):
        """
        Sends video to telegram
        """
        video = video['video']
        caption = None
        if video.get('title'):
            caption = f"*{video['title']}*"
            if video.get('subtitle'):
                caption += f"\n{video['subtitle']}"

        self.api.sendVideo(self.user_id, video['url'], duration=None, width=None, height=None,
                           caption=caption, parse_mode='Markdown', supports_streaming=None, disable_notification=None, reply_to_message_id=None, reply_markup=None)

    def send_audio(self, audio: dict):
        """
        Sends audio to telegram
        """
        audio = audio['audio']
        caption = None
        if audio.get('title'):
            caption = f"*{audio['title']}*"
            if audio.get('subtitle'):
                caption += f"\n{audio['subtitle']}"

        #self.telegram.sendAudio(self.user_id, audio['uri'], caption=caption, parse_mode='Markdown', duration=None, performer=None,
        #   title="Title?", disable_notification=None, reply_to_message_id=None, reply_markup=None)
        self.api.sendVoice(self.user_id, audio['url'], caption=caption, parse_mode='Markdown', duration=None,
                           disable_notification=None, reply_to_message_id=None, reply_markup=None)

    def send_buttons(self, buttons: dict):
        """
        Sends buttons to telegram
        """
        buttons = buttons['buttons']
        from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
        telegram_buttons = []
        for button in buttons['buttons']:
            telegram_buttons.append([InlineKeyboardButton(text=button['text'], callback_data=button['postback'])])
        keyboard = InlineKeyboardMarkup(inline_keyboard=telegram_buttons)        
        self.api.sendMessage(self.user_id, buttons['text'], reply_markup=keyboard)


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
        telegram_dotbots_c = self.dotdb.find_dotbots_by_channel('telegram')
        if not telegram_dotbots_c:
            self.logger.debug('No telegram enabled bots')

        # cert file only used on local machines with self-signed certificate
        cert_file = open(self.config['cert_filename'], 'rb') if self.config.get('cert_filename') else None

        for tdc in telegram_dotbots_c:
            td = tdc.dotbot

            self.logger.debug('Checking Telegram webhook for botid ' + td['id'] + '...')

            self.logger.debug('Setting token ' + td['channels']['telegram']['token'])
            self.set_api_token(td['channels']['telegram']['token'])

            # build webhook url
            url = self.config['webhook_uri'].replace('{dotbotid}', td['id'])

            # check webhook current status (faster than overriding webhook)
            webhook_info = self.api.getWebhookInfo()
            self.logger.debug('WebHookInfo: ' + str(webhook_info))
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
                self.logger.info(f'Setting webhook for bot id ' + td['id'] + f' with webhook url {url}')
                set_ret = self.api.setWebhook(url=url, certificate=cert_file)
                self.logger.debug(set_ret)
                if set_ret:
                    self.logger.info("Successfully set.")
                else:
                    error = "Couldn't set the webhook"
                    self.logger.error(error)
                    raise Exception(error)
            else:
                self.logger.debug("Webhook is correct")

    def buttons_process(self, bbot_output: dict) -> dict:
        """
        Groups text and buttons for Telegram API.
        BBot response specification do not groups buttons and texts, so his is a process to do it for Telegram.

        Buttons needs special treatment because Telegram ask for mandatory text output with it
        so we need to find and send text output at the same time

        :param bbot_output: BBot response output
        :return: Telegram buttons object
        """
        for idx, br in enumerate(bbot_output):
            response_type = list(br.keys())[0]

            if response_type == 'button':
                # look for previous text
                if bbot_output[idx - 1].get('text'):
                    buttons_text = bbot_output[idx - 1]['text']
                    bbot_output[idx - 1] = {'none': []}  # will be send with buttons
                else:
                    buttons_text = ''
                # look for next buttons
                buttons = [br['button']]
                for idx2, next_btn in enumerate(bbot_output[idx + 1:len(bbot_output)]):
                    if next_btn.get('button'):
                        buttons.append(next_btn['button'])
                        bbot_output[idx2 + idx + 1] = {'none': []}  # will be added with the grouped buttons
                    elif next_btn.get('text'):  # when it founds a text, stops looking for more buttons
                        break

                bbot_output[idx] = {  # modifying button object for telegram.send_button()
                    'buttons': {
                        'text': buttons_text,
                        'buttons': buttons
                    }
                }
        return bbot_output
