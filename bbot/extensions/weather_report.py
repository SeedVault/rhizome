""""""
import requests
import logging
import smokesignal
from bbot.core import BBotCore, ChatbotEngine, BBotException, BBotLoggerAdapter, BBotExtensionException

class WeatherReport():
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

        self.core = None
        self.logger = None

    def init(self, core: BBotCore):
        """

        :param bot:
        :return:
        """
        self.core = core
        self.logger = BBotLoggerAdapter(logging.getLogger('core_fnc.weather'), self, self.core.bot, '$weather')                

        self.method_name = 'weather'
        self.accuweather_text = 'Weather forecast provided by Accuweather'
        self.accuweather_image_url = 'https://static.seedtoken.io/AW_RGB.png'
        
        core.register_function('weather', {'object': self, 'method': self.method_name, 'cost': 0.1, 'register_enabled': True})
        # we register this to add accuweather text even when result is cached from extensions_cache decorator
        smokesignal.on(BBotCore.SIGNAL_CALL_BBOT_FUNCTION_AFTER, self.add_accuweather_text)
        

    @BBotCore.extensions_cache
    def weather(self, args, f_type):
        """
        Returns weather report
        @TODO return forecast based on args[1] date

        :param args:
        :param f_type:
        :return:
        """                
        try:
            location = self.core.resolve_arg(args[0], f_type)
        except IndexError:
            raise BBotException({'code': 0, 'function': 'weather', 'arg': 0, 'message': 'Location is missing.'})

        try:
            date = args[1]
        except IndexError:
            date = 'today'  # optional. default 'today'

        self.logger.info(f'Retrieving weather for {location}')
        st = self.search_text(location)

        if not st:
            self.logger.info("Location not found. Invalid location")
            return {
                'text': '<No weather data or invalid location>',  #@TODO should raise a custom exception which will be used for flow exceptions
                'canonicalLocation': location
            }

        location_key = st[0].get('Key', None)

        self.logger.debug("Accuweather Location Key: " + location_key)

        canonical_location = st[0]['LocalizedName'] + ', ' + st[0]['Country']['LocalizedName']
        self.logger.debug('Canonical location: ' + canonical_location)
        self.logger.debug('Requeting Accuweather current conditions...')
        r = requests.get(
            f'http://dataservice.accuweather.com/currentconditions/v1/{location_key}?apikey={self.accuweather_api_key}&details=false')
        self.logger.debug('Accuweather response: ' + str(r.json())[0:300])
        if r.status_code == 200:
            aw = r.json()
            
            return {
                'text': aw[0]['WeatherText'],
                'temperature': {
                    'metric': str(aw[0]['Temperature']['Metric']['Value']),
                    'imperial': str(aw[0]['Temperature']['Imperial']['Value'])
                    },
                'canonicalLocation': canonical_location
            }

        err_msg = r.json()['fault']['faultstring']
        self.logger.critical(err_msg)            
        raise BBotExtensionException(err_msg, BBotCore.FNC_RESPONSE_ERROR)
        

    def search_text(self, location):
        # get locationkey based on provided location
        self.logger.info(f'Requesting Accuweather location key...')
        r = requests.get(
            f'http://dataservice.accuweather.com/locations/v1/search?apikey={self.accuweather_api_key}&q={location}&details=false')
        self.logger.debug('Accuweather response: ' + str(r.json())[0:300])
        if r.status_code == 200:
            return r.json()            

        err_msg = r.json()['fault']['faultstring']
        self.logger.critical(err_msg)
        raise BBotExtensionException(err_msg, BBotCore.FNC_RESPONSE_ERROR)
        
    def add_accuweather_text(self, data):
        # check if call is made from a weather call
        if data['name'] is self.method_name:               
            # check if the call was successful
            if data['response_code'] is BBotCore.FNC_RESPONSE_OK:
                # check if text is already added
                if not self.core.bbot.outputHasText(self.accuweather_text):
                    # adds accuweather logo to the bots response
                    self.core.bbot.text(self.accuweather_text)
                    self.core.bbot.image(self.accuweather_image_url)            
