"""Telegram Channel. LOAD channels.restful.app TO ANSWER TELEGRAM WEBHOOK"""
import telepot
import logging
from urllib.parse import urlparse
import time
import html
import traceback
import json
import os
import cgi
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton

from bbot.core import BBotCore, ChatbotEngine, BBotException, BBotLoggerAdapter
from bbot.config import load_configuration

class Telegram:
    """Translates telegram request/response to flow"""

    def __init__(self, config: dict, dotbot: dict) -> None:
        """        
        """
        self.config = config
        self.dotbot = dotbot
        self.dotdb = None #
        self.api = None
        self.logger_level = ''
        
        self.default_text_encoding = 'HTML' #@TODO move this to dotbot

        self.emOpen = "<b>"
        self.emClose = "</b>"
        if self.default_text_encoding == 'markdown':
            self.emOpen = "*"
            self.emClose = "*"


    def init(self, core):
        self.core = core
        self.logger = BBotLoggerAdapter(logging.getLogger('channel_telegram'), self, self.core, 'ChannelTelegram')        

        self.logger.debug("Listening Telegram from path: " + self.get_webhook_path())

    def endpoint(self, request=dict, publisherbot_token=str):
        print('------------------------------------------------------------------------------------------------------------------------')
        self.logger.debug(f'Received a Telegram webhook request for publisher token {publisherbot_token}')

        enabled = self.webhook_check(publisherbot_token)
        if enabled:
            try:
                params = request.get_json(force=True)
                org_id = 1

                # checks if bot is telegram enabled
                # if not, it delete the webhook and throw an exception
                
                # get publisher user id from token
                pub_bot = self.dotdb.find_publisherbot_by_publisher_token(publisherbot_token)
                if not pub_bot:
                    raise Exception('Publisher not found')
                self.logger.debug('Found publisher: ' + pub_bot.publisher_name + ' - for bot id: ' + pub_bot.bot_id)
                pub_id = pub_bot.publisher_name
                
                # if 'runBot' in params:
                #    run_bot = self.params['runBot']
            
                dotbot = self.dotdb.find_dotbot_by_bot_id(pub_bot.bot_id)                    
                if not dotbot:
                    raise Exception('Bot not found')
                bot_id = dotbot.bot_id
                # build extended dotbot 
                dotbot.services = pub_bot.services
                dotbot.channels = pub_bot.channels
                dotbot.botsubscription = pub_bot
                
                token = pub_bot.channels['telegram']['token']
                self.set_api_token(token)

                user_id = self.get_user_id(params)
                telegram_recv = self.get_message(params)
                self.logger.debug('POST data from Telegram: ' + str(params))
                bbot_request = self.to_bbot_request(telegram_recv)

                channel_id = 'telegram'
                                
                config = load_configuration(os.path.abspath(os.path.dirname(__file__) + "../../../instance"), "BBOT_ENV")
                bbot = BBotCore.create_bot(config['bbot_core'], dotbot)
                self.logger.debug('User id: ' + user_id)
                req = bbot.create_request(bbot_request, user_id, bot_id, org_id, pub_id, channel_id)                    
                bbot_response = bbot.get_response(req)
                                
                self.send_response(bbot_response)
                self.logger.debug("Response from telegram channel: " + str(bbot_response))

            except Exception as e:           
                self.logger.critical(str(e) + "\n" + str(traceback.format_exc()))            
                if os.environ['BBOT_ENV'] == 'development':
                    bbot_response = {                        
                        'output': [{'type': 'message', 'text': cgi.escape(str(e))}],
                        'error': {'traceback': str(traceback.format_exc())}
                        }
                else:
                    bbot_response = {'output': [{'type': 'message', 'text': 'An error happened. Please try again later.'}]}
                    # @TODO this should be configured in dotbot
                    # @TODO let bot engine decide what to do?
                
                self.logger.debug("Response from telegram channel: " + str(bbot_response))
                self.send_response(bbot_response)

            
    def webhook_check(self, publisherbot_token):

        pb = self.dotdb.find_publisherbot_by_publisher_token(publisherbot_token)

        if pb.channels.get('telegram'):
            return True

        self.logger.warning(f'Deleting invalid Telegram webhook for publisher bot token: {publisherbot_token} - publisher id: ' + pb.publisher_name)
        self.set_api_token(pb.channels['telegram']['token'])
        delete_ret = self.api.deleteWebhook()
        if delete_ret:
            self.logger.warning("Successfully deleted.")
            return False
            #raise Exception('Received a telegram webhook request on a telegram disabled bot. The webhook was deleted now.')
        else:
            error = "Received a telegram webhook request on a telegram disabled bot and couldn't delete the invalid webhook"
            self.logger.error(error)
            raise Exception(error)

    def set_api_token(self, token: str):
        self.api = telepot.Bot(token)

    def to_bbot_request(self, request: str) -> str:
        return {'text': request}

    def get_webhook_url(self) -> str:
        return self.config['webhook_uri']

    def get_webhook_path(self) -> str:
        return urlparse(self.config['webhook_uri']).path

    ### Responses

    def send_response(self, bbot_response: dict):
        """
        Parses BBot output response and sends content to telegram
        """
        # @TODO check if we can avoid sending separate api request for each text if there are more than one

        bbot_output = bbot_response['output']
        
        # Iterate through bbot responses
        for br in bbot_output:
            buttons = None
            if 'suggestedActions' in br: # this must be first
                buttons = br['suggestedActions']['actions']

            if 'text' in br:
                    self.send_text(br['text'], buttons)
            if 'attachments' in br:
                for a in br['attachments']:
                    if a['contentType'] == 'application/vnd.microsoft.card.audio':
                        self.send_audio_card(a['content'], buttons)
                    if a['contentType'] == 'application/vnd.microsoft.card.video':
                        self.send_video_card(a['content'], buttons)
                    if a['contentType'] in ['application/vnd.microsoft.card.hero', 'application/vnd.microsoft.card.thumbnail', 'image/png', 'image/jpeg']:                        
    
                        self.send_image_hero_card(a['content'], buttons)


    def _get_keyboard(self, buttons: list):
        if not buttons or len(buttons) == 0:
            return None
        telegram_buttons = []
        for button in buttons:
            if button['type'] == 'imBack':
                telegram_buttons.append([InlineKeyboardButton(text=button['title'], callback_data=button['value'])])
            #@TODO add button with link    
        keyboard = InlineKeyboardMarkup(inline_keyboard=telegram_buttons)        
        return keyboard
        
    def send_text(self, text: list, buttons: list):
        """
        Sends text to telegram
        """        
        if len(text) == 0:
            text = "..."

        keyboard = self._get_keyboard(buttons)
        self.api.sendMessage(self.user_id, text, parse_mode=self.default_text_encoding, reply_markup=keyboard)
            
    
    def send_image_hero_card(self, card: dict, buttons: list):
        url = None
        if card.get('media'):
            url = card['media'][0]['url']
        elif card.get('images'):
            url = card['images'][0]['url']            
        caption = self._common_media_caption(card)
        keyboard = self._get_keyboard(buttons)
        self.logger.debug('Sending image to Telegram: url: ' + url)
        self.api.sendPhoto(self.user_id, url, caption=caption, parse_mode=self.default_text_encoding, disable_notification=None, 
            reply_to_message_id=None, reply_markup=keyboard)

    def send_audio_card(self, card: dict, buttons: list):
        url = card['media'][0]['url']
        caption = self._common_media_caption(card)
        keyboard = self._get_keyboard(buttons)
        self.logger.debug('Sending audio to Telegram: url: ' + url)
        self.api.sendAudio(self.user_id, url, caption=caption, parse_mode=self.default_text_encoding, duration=None, performer=None,
           title=None, disable_notification=None, reply_to_message_id=None, reply_markup=keyboard)

    def send_video_card(self, card: dict, buttons: list):
        url = card['media'][0]['url']
        caption = self._common_media_caption(card)
        keyboard = self._get_keyboard(buttons)
        self.logger.debug('Sending video to Telegram: url: ' + url)
        self.api.sendVideo(self.user_id, url, duration=None, width=None, height=None, caption=caption, parse_mode=self.default_text_encoding, 
            supports_streaming=None, disable_notification=None, reply_to_message_id=None, reply_markup=keyboard)

    def _common_media_caption(self, card: dict):        
        
        title = None  # Seems title arg in sendAudio() is not working...? we add it in caption then
        caption = ""
        if card.get('title'):
            caption += f"{self.emOpen}{card['title']}{self.emClose}"
        if card.get('subtitle'):
            if len(caption) > 0:
                caption += "\n"
            caption += card['subtitle']
        if card.get('text'):
            if len(caption) > 0:
                caption += "\n\n"
            caption += card['text']
        
        if len(caption) == 0:
            caption = None
        return caption

    ### Request

    def get_user_id(self, request: dict):
        if request.get('message'): #regular text
            self.user_id = str(request['message']['from']['id'])
            return self.user_id

        if request.get('callback_query'): # callback from a button click
            self.user_id = str(request['callback_query']['from']['id'])
            return self.user_id

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

        sleep_time = 3 # 20 requests per minute is ok?

        # get all telegram enabled bots
        telegram_pubbots = self.dotdb.find_publisherbots_by_channel('telegram')
        
        if not telegram_pubbots:
            self.logger.debug('No telegram enabled bots')
            return

        # cert file only used on local machines with self-signed certificate
        cert_file = open(self.config['cert_filename'], 'rb') if self.config.get('cert_filename') else None

        for tpb in telegram_pubbots:                    
            if tpb.channels['telegram']['token']:
                self.logger.debug('---------------------------------------------------------------------------------------------------------------')
                self.logger.debug('Checking Telegram webhook for publisher name ' + tpb.publisher_name + ' publisher token: ' + tpb.token + ' - bot id: ' + tpb.bot_id + '...')
                self.logger.debug('Setting token: ' + tpb.channels['telegram']['token'])
                
                try:
                    self.set_api_token(tpb.channels['telegram']['token'])

                    # build webhook url
                    url = self.get_webhook_url().replace('<publisherbot_token>', tpb.token)

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
                        self.logger.info(f'Setting webhook for bot id ' + tpb.bot_id + f' with webhook url {url}')
                        set_ret = self.api.setWebhook(url=url, certificate=cert_file)
                        self.logger.debug("setWebHook response: " + str(set_ret))
                        if set_ret:
                            self.logger.info("Successfully set.")
                        else:
                            error = "Couldn't set the webhook"
                            self.logger.error(error)
                            raise Exception(error)
                    else:
                        self.logger.debug("Webhook is correct")
                except telepot.exception.TelegramError:
                    self.logger.debug('Invalid Telegram token') # This might happen when the token is invalid. We need to ignore and ontinue

                time.sleep(sleep_time)
