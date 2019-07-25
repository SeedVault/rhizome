"""Fallback bots."""
import logging
from bbot.core import BBotCore, ChatbotEngine, BBotLoggerAdapter

class FallbackBots():
    """."""

    def __init__(self, config: dict, dotbot: dict) -> None:
        """
        Initialize the plugin.
        """
        self.config = config
        self.dotbot = dotbot

        self.logger_level = ''

        self.core = None
        self.logger = None

    def init(self, core: BBotCore):
        """

        :param bot:
        :return:
        """
        self.core = core           
        self.logger = BBotLoggerAdapter(logging.getLogger('pipeline.fallbackbots'), self, self.core, 'FallbackBots')
   
    def process(self):
        """
        @TODO this will be called from a pubsub event, so args might change
        Call to fallback bots defined in dotbot when the main bot has a no match o
        or when it doesnt answer or has an invalid response
        @TODO this might be replaced by a conditional pipeline

        :param bot:
        :param response:
        :return:
        """            
        if not self.core.bot.is_fallback and (self.core.response.get('noMatch') or self.core.response.get('error')):
            self.logger.debug('Bot engine has a no match. Looking fallback bots')

            # try import bots
            fbbs = self.core.dotbot.get('fallbackBots', [])
            for bot_name in fbbs:
                self.logger.debug(f'Trying with bot {bot_name}')
                bot_dotbot_container = self.core.dotdb.find_dotbot_by_idname(bot_name)
                if not bot_dotbot_container:
                    raise Exception(f'Fallback bot not found {bot_name}')
                else:
                    bot_dotbot = bot_dotbot_container.dotbot

                config_path = os.path.abspath(os.path.dirname(__file__) + "/../instance")
                config = load_configuration(config_path, "BBOT_ENV")
                bbot = create_bot(config, bot_dotbot)
                bbot.is_fallback = True
                req = ChatbotEngine.create_request(core.request['input'], core.user_id, 1, 1)
                fallback_response = bbot.get_response(req)
                if fallback_response.get('error'):
                    self.logger.error('Fallback bot returned an invalid response. Discarding.')
                    continue
                if not fallback_response.get('noMatch'):
                    self.logger.debug('Fallback bot has a response. Returning this to channel.')
                    self.core.response = fallback_response
                    return
            if fbbs:
                self.logger.debug('Fallback bot don\'t have a response either. Sending original main bot response if any')
            else:
                self.logger.debug('No fallback defined for this bot. Sending original main bot response if any')
        
        self.logger.debug('Bot responded with a match. No fallback needed.')            
        return