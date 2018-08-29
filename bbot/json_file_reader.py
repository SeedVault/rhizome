"""Read configuration from a json file."""

import os
import errno
import json
from bbot.core import ConfigReader

class JsonFileReader(ConfigReader):
    """Read configuration from a json file."""

    def __init__(self, config: dict) -> None:
        """
        Initialize the plugin.

        :param config: Configuration values for the instance.
        """
        self.filename = ''
        super().__init__(config)


    def read(self, bot_id: str) -> dict:
        """Read configuration.

        :raises FileNotFoundError if the configuration file is not found.
        :return: A dictionary of configuration settings.
        """
        super().read()
        if not os.path.isfile(self.filename):
            raise FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), self.filename)
        with open(self.filename, "r") as data_file:
            return json.load(data_file)
