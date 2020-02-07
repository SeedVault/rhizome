"""BBot engine based on DirectLine API."""
import logging
import copy
import requests
import json
import datetime
import uuid
from bbot.core import BBotCore, ChatbotEngine, ChatbotEngineError, BBotLoggerAdapter, BBotException


class BotBuilderConnector(ChatbotEngine):
    
    def __init__(self, config: dict, dotbot: dict) -> None:
        """
        Initialize the plugin.

        :param config: Configuration values for the instance.
        """
        super().__init__(config, dotbot)

        self.dotdb = None

        
    def init(self, core: BBotCore):
        """
        Initializebot engine 
        """
        super().init(core)
        
        self.logger = BBotLoggerAdapter(logging.getLogger('bbconnector_cbe'), self, self.core)

    def get_response(self, request: dict) -> dict:
