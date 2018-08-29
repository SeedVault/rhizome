"""Weather."""
import json
import requests
from flow.chatbot_engine import Extension, FlowError, extensions_cache

class Weather(Extension):
    """Weather"""

    def __init__(self, flow):
        super().__init__(flow)
        
        class_name = self.__class__.__module__ + '.' + self.__class__.__name__
        flow.register_dot_flow_function('weather', {
            'class': class_name, 'method': 'get_weather', 'is_template_function': True})

    @extensions_cache
    def get_weather(self, args):                
        location = args[0]      
        self.flow.logger.debug(f'Retrieving weather for {location}')  
        st = self.search_text(location)
                
        if st == []:
            self.flow.logger.debug("Location key not found. Invalid location")
            return {
                'text': '<No weather data or invalid location>',
                'canonicalLocation': location
            }

        location_key = st[0].get('Key', None)

        self.flow.logger.debug("Accuweather Location Key: " + location_key)

        canonical_location = st[0]['LocalizedName'] + ', ' + st[0]['Country']['LocalizedName']        
        self.flow.logger.debug("Canonical location: " + canonical_location)
        
        r = requests.get(f'http://dataservice.accuweather.com/currentconditions/v1/{location_key}?apikey={self.flow.weather_api_key}&details=false')

        if r.status_code == 200:
            aw = r.json()
            return {
                'text': aw[0]['WeatherText'],
                'canonicalLocation': canonical_location
            }

        self.flow.logger.error(r.text)
        raise FlowError('Weather report request status code ' + str(r.status_code))
        

    def search_text(self, location):
        # get locationkey based on provided location                
        r = requests.get(f'http://dataservice.accuweather.com/locations/v1/search?apikey={self.flow.weather_api_key}&q={location}&details=false')
        if r.status_code == 200:
            return r.json()        
            # @TODO there should be a .bot config to narrow search location to a country or region
            
        self.flow.logger.error(r.text)
        raise FlowError('Weather location key request status code ' + str(r.status_code))
        
        