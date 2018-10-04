"""Read configuration from a restful server."""
import requests
import os
import errno
import json
from bbot.core import ConfigReader
from dot_repository.mongodb import DotRepository as DotRepo

class DotBotReader(ConfigReader):
    """Read configuration from a restful server."""

    def __init__(self, config: dict) -> None:
        """
        Initialize the plugin.

        :param config: Configuration values for the instance.
        """
        super().__init__(config)

        dot_db = DotRepo({'MONGODB_URI': config['uri']})



    def read(self, bot_id: str) -> dict:
        """Read configuration.

        :return: A dictionary of configuration settings.
        """
        super().read()



