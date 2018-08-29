"""Read configuration from a restful server."""
import requests
import os
import errno
import json
from bbot.core import ConfigReader

class HttpRequest(ConfigReader):
    """Read configuration from a restful server."""

    def __init__(self, config: dict) -> None:
        """
        Initialize the plugin.

        :param config: Configuration values for the instance.
        """
        self.url = ''
        super().__init__(config)


    def read(self, bot_id: str) -> dict:
        """Read configuration.
        
        :return: A dictionary of configuration settings.
        """
        super().read()
        
        r = requests.get(self.url.replace('{dotbotid}', str(bot_id)))
        
        if r.status_code == 200:
            return r.json()
            
        