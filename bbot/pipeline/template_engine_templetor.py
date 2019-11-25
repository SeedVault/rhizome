"""Template engine."""
import logging
import re
from web.template import *
from bbot.core import BBotCore, ChatbotEngine, BBotLoggerAdapter, BBotException

class TemplateEngineTemplator():
    """."""

    def __init__(self, config: dict, dotbot: dict) -> None:
        """
        Initialize the plugin.
        """
        self.config = config
        self.dotbot = dotbot

        self.logger_level = ''

        self.core = None
        self.logger = None

    def init(self, core: BBotCore):
        """

        :param bot:
        :return:
        """
        self.core = core        
        self.logger = BBotLoggerAdapter(logging.getLogger('pipeline.templator'), self, self.core, 'Templetor')
                                
    def get_functions(self):
        """
        Adds custom functions to template @TODO this should be initialized just once at runtime, not at every render!!

        :return:
        """
        c_functions = {}
        for f_name in self.core.functions_map:  # register template functions from extensions
            self.logger.debug('Adding template custom function "' + f_name + '"')
            c_functions[f_name] = getattr(self.core.bbot, f_name)            
        return c_functions

    def render(self, string: str) -> str:
        """
        Renders any string with configured bbot custom functions and bot session vars
        """                
        # We still need a way to know if a string is a template or not, but Templator don't need enclosing
        # So for Templator, just enclose the whole string with {{ }} for BBot to know it is a template
        if re.search('({%).*(%})|({{.*}})', string) is None:
            self.logger.debug('Nothing to render')
            return string
        string = string.replace('{{', '')
        string = string.replace('}}', '')
        string = string.replace('{%', '')
        string = string.replace('%}', '')

        session_vars = {}
        if hasattr(self.core.bot, 'session'):
            session_vars = self.core.bot.session.get_var(self.core.bot.user_id)

        t_globals = session_vars
        # add predefined vars from publishers
        if hasattr(self.dotbot, 'botsubscription'):
            if hasattr(self.dotbot.botsubscription, 'predefined_vars'):
                t_globals = {**t_globals, **self.dotbot.botsubscription.predefined_vars}

        # get custom functions from extensions
        c_functions = self.get_functions()        
        t_globals = {**t_globals, **c_functions}

        self.logger.debug('Rendering template: "' + str(string) + '"')
        templator_obj = Template(string, globals=t_globals)
        try:
            response = str(templator_obj())
        except NameError as e:
            err_msg = 'Template error: ' + str(e)
            self.core.logger.debug(err_msg)            
            raise BBotException({'message': err_msg})

        if response[-1:] == '\n':       # Templator seems to add a trailing \n, remove it
            response = response[:-1]

        self.logger.debug('Template response: "' + response + '"')

        if response.find('<function BBotFunctionsProxy') is not -1:
            self.logger.error('Templator returned an invalid response. Botdev forgot to escape $?')
            response = '<TEMPLATE RENDERING ERROR. CHECK DEBUG DATA>'  # @TODO add debug data in context to the instruction executed
        
        return response

    def process(self):
        """
        Runs as pipeline process
        """        
        for k, r in enumerate(self.core.response['output']):            
            response_type = list(r)[0]
            if response_type == 'text': #@TODO this should traverse the whole dict not just text
                response = r['text']
                self.core.response['output'][k]['text'] = self.render(response)

        

        

  