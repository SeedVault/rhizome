""""""
import requests
import logging
import sys, traceback, os
from bbot.core import BBotCore, ChatbotEngine, BBotException, BBotLoggerAdapter, BBotExtensionException

class RemoteAPIs():
    """Calls remote API endpoints"""

    def __init__(self, config: dict, dotbot: dict) -> None:
        """
        Initialize the plugin.
        """
        self.config = config
        self.dotbot = dotbot        

        # vars set from plugins
        self.logger_level = ''
        self.request_timeout = 1
        self.dotdb = None

        self.core = None
        
    def init(self, core: BBotCore):
        """

        :param bot:
        :return:
        """
        self.core = core
        self.logger = BBotLoggerAdapter(logging.getLogger('ext.r_services'), self, self.core.bot, '$call_api')                

        # get services for the bot    
        services = self.get_bot_services()        
        for serv in services:
            if serv['url'] is not '': # if empty means service is registered from code
                self.logger.debug('Register service ' + serv['name'])
                self.logger.debug(str(serv))
                core.register_function(serv['function_name'], {
                    'object': self,         
                    'method': serv['function_name'], 
                    'owner_name': serv['ownerName'],
                    'url': serv['url'],
                    'request_method': serv['method'],
                    'timeout': serv['timeout'],
                    'cost': serv['cost'], 
                    'subscription_type': serv['subscriptionType'],
                    'predefined_vars': serv['predefined_vars'],
                    'headers': serv['headers'], 
                    'user': serv.get('user'),
                    'passwd': serv.get('passwd'),                     
                    'mapped_vars': serv['mapped_vars'],
                    'subscription_id': serv['subscriptionId'],
                    'register_enabled': True
                })
        
    def get_bot_services(self):
        return self.dotbot.services
    
    def __getattr__(self, fname):                        
            def function(*args,**kwargs):                               
                r_api_data = self.core.functions_map[fname]
                self.logger.debug('Calling remote API ' + fname + ' args: ' + str(args) + ' - metadata: ' + str(r_api_data))        
                auth = None
                if r_api_data.get('user'):
                        auth = (r_api_data['user'], r_api_data['passwd'])

                # map args to variables
                c = 0
                params = {}
                for mv in r_api_data['mapped_vars']:
                    try:
                        params[mv] = self.core.resolve_arg(args[c])        
                        c += 1
                    except IndexError:
                        raise BBotException({'code': 250, 'function': fname, 'arg': c, 'message': 'Parameter ' + str(c) +  ' is missing'})
                
                params = {**params, **r_api_data['predefined_vars']}

                # interpolate args to url
                url = r_api_data['url']
                c = 0                
                for arg in args[0]:                          
                    url = url.replace('{{' + str(c) + '}}', str(args[c]))
                    c += 1
                    
                try: 
                    
                    if r_api_data['request_method'] == 'get':                        
                        r = requests.get(
                            url,  
                            params = params, 
                            headers = r_api_data['headers'], 
                            timeout = self.request_timeout or r_api_data['timeout'],        # <<<< custom per service?
                            auth=auth,
                            allow_redirects=True,
                            )  
                    else:
                        r = requests.post(
                            url, 
                            data = params, 
                            headers = r_api_data['headers'], 
                            timeout = self.request_timeout or r_api_data['timeout'], 
                            auth=auth,
                            allow_redirects=True
                            )

                    self.logger.debug('Response:' + str(r))
                    self.logger.debug('Headers: ' + str(r.headers))
                    if r.status_code == requests.codes.ok:
                        if 'application/json' in r.headers.get('Content-Type') or 'application/javascript' in r.headers.get('Content-Type'):
                            return r.json()                
                        else: # default
                            return r.text              
                    
                    # On error
                    r.raise_for_status()
                except Exception as e:
                    self.logger.debug(str(e) + "\n" + str(traceback.format_exc())) # errors in remote apis are not critical for us. This should be alerted to service dev
                    if os.environ['BBOT_ENV'] == 'development':
                        raise BBotExtensionException(str(e), BBotCore.FNC_RESPONSE_ERROR)
                    else:
                        return None

            return function
    