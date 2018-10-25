""""""
import requests
import logging
from bbot.core import ChatbotEngine, BBotException
from engines.dotflow2.chatbot_engine import DotFlow2, DotFlow2LoggerAdapter


class DotFlow2WeatherReport():
    """Returns Weather Report"""

    def __init__(self, config: dict, dotbot: dict) -> None:
        """
        Initialize the plugin.
        """
        self.config = config
        self.dotbot = dotbot

        # vars set from plugins
        self.accuweather_api_key = ''
        self.logger_level = ''

        self.bot = None
        self.logger = None

    def init(self, bot: ChatbotEngine):
        """

        :param bot:
        :return:
        """
        self.bot = bot
        self.logger = DotFlow2LoggerAdapter(logging.getLogger('df2_ext.weather'), self, self.bot, '$weather')
        bot.register_dotflow2_function('weather', {'object': self, 'method': 'df2_weather'})
        bot.register_template_function('weather', {'object': self, 'method': 'df2_weather'})

    @DotFlow2.extensions_cache
    def df2_weather(self, args, f_type):
        """
        Returns weather report
        @TODO return forecast based on args[1] date

        :param args:
        :param f_type:
        :return:
        """
        try:
            location = self.bot.resolve_arg(args[0], f_type)
        except IndexError:
            raise BBotException({'code': 0, 'function': 'sendEmail', 'arg': 0, 'message': 'Location is missing.'})

        try:
            date = args[1]
        except:
            date = 'today'  # optional. default 'today'

        self.logger.debug(f'Retrieving weather for {location}')
        st = self.search_text(location)

        if not st:
            self.logger.debug("Location not found. Invalid location")
            return {
                'text': '<No weather data or invalid location>',  #@TODO should raise a custom exception which will be used for flow exceptions
                'canonicalLocation': location
            }

        location_key = st[0].get('Key', None)

        self.logger.debug("Accuweather Location Key: " + location_key)

        canonical_location = st[0]['LocalizedName'] + ', ' + st[0]['Country']['LocalizedName']
        self.logger.debug("Canonical location: " + canonical_location)

        r = requests.get(
            f'http://dataservice.accuweather.com/currentconditions/v1/{location_key}?apikey={self.accuweather_api_key}&details=false')

        if r.status_code == 200:
            aw = r.json()
            return {
                'text': aw[0]['WeatherText'],
                'canonicalLocation': canonical_location
            }

            self.logger.error(r.text)
        #raise FlowError('Weather report request status code ' + str(r.status_code))

    def search_text(self, location):
        # get locationkey based on provided location
        r = requests.get(
            f'http://dataservice.accuweather.com/locations/v1/search?apikey={self.accuweather_api_key}&q={location}&details=false')
        if r.status_code == 200:
            return r.json()
            # @TODO there should be a .bot config to narrow search location to a country or region

            self.logger.error(r.text)
        #raise FlowError('Weather location key request status code ' + str(r.status_code))

