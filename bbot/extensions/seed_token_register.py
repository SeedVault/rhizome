"""Registers bot activity"""

import logging
import time
import datetime
from pymongo import MongoClient, DeleteMany
from bson.objectid import ObjectId
from pydispatch import dispatcher
from bbot.core import BBotCore, ChatbotEngine, BBotException

class SeedTokenRegister():
    """Registers in a DB some bot activity"""

    def __init__(self, config: dict, dotbot: dict) -> None:
        """
        Initialize the plugin.
        """
        self.config = config
        self.dotbot = dotbot
        
        self.logger_level = ''

        self.bot = None
        self.logger = None

    def init(self, bot: ChatbotEngine):
        """
        :param bot:
        :return:
        """
        self.bot = bot
        
        if 'mongodb_uri' not in self.config:
            raise RuntimeError("FATAL ERR: Missing config var uri")

        uri = self.config["mongodb_uri"]
        self.client = MongoClient(uri)
        parts = uri.split("/")
        last_part = parts.pop()
        parts = last_part.split("?")
        self.database_name = parts[0]
        self.volleys = self.client[self.database_name]["volleys"]

        dispatcher.connect(self.register_volley, signal=BBotCore.SIGNAL_GET_RESPONSE_AFTER, sender=dispatcher.Any)    
    
    def register_volley(self, message):
        """
        Registers volley on db
        """
        
        ts = time.time()
        date_iso = datetime.datetime.utcnow()
        self.volleys.insert({
            "_id" : ObjectId(),
            "version" : 1,
            "type" : "volley",
            "timestamp" : ts,
            "timestamp_iso" :  date_iso,
            "key" : "bbc37f6e1382c5f8fbb9397e960152c2",
            "root_flow" : 0,
            "service" : "seed",
            "endpoint" : "finance_balance",
            "current_status" : "unsent",
            "transaction_id" : False,
            "token_value" : 0.01,
            "transaction" : False,
            "transaction_detail" : False,
            "volley_target" : "botone",
            "status" : [
                    {
                            "status" : "unsent",
                            "timestamp" : ts,
                            "timestamp_iso" : date_iso
                    }
            ]
        }
)
