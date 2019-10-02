"""Registers bot activity"""

import logging
import time
import datetime
from pymongo import MongoClient, DeleteMany
from bson.objectid import ObjectId
import smokesignal
from bbot.core import BBotCore, ChatbotEngine, BBotException, BBotLoggerAdapter

class ActivityLogger():
    """Registers in a DB some bot activity"""

    ACTIVITY_TYPE_VOLLEY    = 1
    ACTIVITY_TYPE_FUNCTION  = 2

    def __init__(self, config: dict, dotbot: dict) -> None:
        """
        Initialize the plugin.
        """
        self.config = config
        self.dotbot = dotbot
        
        self.logger_level = ''

        self.core = None
        self.logger = None

        self.logger = BBotLoggerAdapter(logging.getLogger('core_ext.reg_act'), self, self.core, 'RegisterActivity')        
     
    def init(self, core: BBotCore):
        """
        :param bot:
        :return:
        """
        self.core = core
        
        # Initialize the connection @TODO improve this
        if 'mongodb_uri' not in self.config:
            raise RuntimeError("FATAL ERR: Missing config var uri")
        uri = self.config['mongodb_uri']
        client = MongoClient(uri)
        parts = uri.split("/")
        last_part = parts.pop()
        parts = last_part.split("?")
        database_name = parts[0]
        self.mongo = client[database_name]

        smokesignal.on(BBotCore.SIGNAL_CALL_BBOT_FUNCTION_AFTER, self.register_function_call)
        smokesignal.on(BBotCore.SIGNAL_GET_RESPONSE_AFTER, self.register_volley)

    def register_volley(self, data):
        """
        Register each volley
        """
        
        self.logger.debug('Registering volley activity')        
        self.register_activity({
            'type': self.ACTIVITY_TYPE_VOLLEY, 
            'code': BBotCore.FNC_RESPONSE_OK,
            'cost': self.dotbot.per_use_cost
            })

    def register_function_call(self, data):
        """
        Register each function call
        """
        if data['register_enabled'] is True:
            self.logger.debug('Registering function call activity: function name "' + data['name'])
            
            if 'error_message' in data:
                data['error_message'] = data['error_message']

            self.register_activity({
                'data': rfc_data, 
                'type': self.ACTIVITY_TYPE_FUNCTION, 
                'code': data['response_code'],
                'cost': data['cost']})        

    def register_activity(self, data):
        """
        Common register function
        """                    
        doc = {
            "_id" : ObjectId(),
            "type": data['type'], 
            "code": data['code'],
            "datetime": datetime.datetime.utcnow(),
            "botId": self.core.bot.bot_id,
            "userId": self.core.bot.user_id, 
            'pubId': self.core.bot.pub_id,
            "cost": data['cost']
        }
        if data.get('data') is not None:
            doc = {**doc, **data['data']}

        self.mongo.activity.insert(doc)

    
    
    