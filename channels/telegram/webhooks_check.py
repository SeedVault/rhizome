"""Telegram Webhooks check."""
import logging.config
import os
from bbot.core import Plugin
from bbot.config import load_configuration

config_path = os.path.abspath(os.path.dirname(__file__) + "../../../instance")
config = load_configuration(config_path, "BBOT_ENV")
t_config = config["channel_telegram"]
telegram = Plugin.load_plugin(t_config)
logging.config.dictConfig(config['logging'])

telegram.webhooks_check()
