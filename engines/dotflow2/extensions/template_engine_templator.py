"""Template engine."""
import logging
from web.template import *
from bbot.core import TemplateEngine, ChatbotEngine
from engines.dotflow2.chatbot_engine import DotFlow2LoggerAdapter


class TemplateEngineTemplator():
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
        self.logger = DotFlow2LoggerAdapter(logging.getLogger('df2_ext.template_e'), self, self.bot, 'Templetor')

    def get_functions(self):
        """
        Adds custom functions to template @TODO this should be initialized just once at runtime, not at every render!!

        :return:
        """
        c_functions = {}
        for f_name in self.bot.core.bbot_functions_map:  # register template functions from extensions
            #self.logger.debug('Adding template custom function "' + f_name + '"')
            c_functions[f_name] = getattr(self.bot.core.bbot, f_name)
        return c_functions

    def render(self, tmpl: str) -> str:
        """
        """
        self.logger.debug('Rendering template: "' + tmpl + '"')

        # We still need a way to know if a string is a template or not, but Templator don't need enclosing
        # So for Templator, just enclose the whole string with {{ }} for BBot to know it is a template
        tmpl = tmpl.replace('{{', '')
        tmpl = tmpl.replace('}}', '')
        tmpl = tmpl.replace('{%', '')
        tmpl = tmpl.replace('%}', '')

        df2_vars = self.bot.session.get_var(self.bot.user_id)

        # get custom functions from extensions
        c_functions = self.get_functions()
        t_globals = {**df2_vars, **c_functions}

        templator_obj = Template(tmpl, globals=t_globals)
        response = str(templator_obj())

        if response[-1:] == '\n':       # Templator seems to add a trailing \n, remove it
            response = response[:-1]

        self.logger.debug('Template response: "' + response + '"')

        if response.find('<function DotFlow2FunctionsProxy') is not -1:
            self.logger.warning('Templator returned an invalid response. Botdev forgot to escape $?')
            response = '<TEMPLATE RENDERING ERROR. CHECK DEBUG DATA>'  # @TODO add debug data in context to the instruction executed

        return response
