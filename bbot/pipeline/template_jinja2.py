"""Template engine. DEPRECATED"""
import logging
from jinja2 import Template, Environment
from bbot.core import TemplateEngine, ChatbotEngine
from engines.dotflow2.chatbot_engine import DotFlow2LoggerAdapter


class PluginTemplateEngine():
    """."""

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
        self.logger = DotFlow2LoggerAdapter(logging.getLogger('df2_ext.template_e'), self, self.bot, 'Jinja2')

    def add_functions(self, template: Template):
        """
        Adds custom functions to template @TODO this should be initialized just once at runtime, not at every render!!

        :return:
        """
        for f_name in self.bot.functions_map:  # register template functions from extensions
            #self.logger.debug('Adding template custom function "' + f_name + '"')
            template.globals[f_name] = getattr(self.bot.df2, f_name)

    def render(self, template: str) -> str:
        """
        """
        self.logger.debug('Rendering template: "' + template + '"')

        df2_vars = self.bot.session.get_var(self.bot.user_id)

        template = Template(template)

        # add custom functions from extensions
        self.add_functions(template)

        response = template.render(df2_vars)  # return rendered text output
        self.logger.debug('Template response: "' + response + '"')
        return response
