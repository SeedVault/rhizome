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

    def register_volley(self, bbot_response):
        """
        Register each volley
        """
        self.logger.debug('Registering volley activity')
        self.register_activity({}, self.ACTIVITY_TYPE_VOLLEY, self.dotbot.get('volleyCost', 0))

    def register_function_call(self, name, response_code):
        """
        Register each function call
        """
        self.logger.debug('Registering function call activity')
        self.register_activity({'fname': name}, self.ACTIVITY_TYPE_FUNCTION, 1)
        

    def register_activity(self, data, type, cost):
        """
        Common register function
        """                    
        doc = {
            "_id" : ObjectId(),
            "type": type, 
            "datetime": datetime.datetime.utcnow(),
            "botId": self.core.bot.bot_id,
            "userId": self.core.bot.user_id, 
            "cost": cost
        }
        doc = {**doc, **data}

        self.mongo.activity.insert(doc)

    
    
    