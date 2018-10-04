"""Template engine."""
from jinja2 import Template, Environment
from bbot.core import TemplateEngine, ChatbotEngine


class PluginTemplateEngine(TemplateEngine):
    """."""

    def __init__(self, config: dict, dotbot: dict) -> None:
        """
        Initialize the plugin.

        """
        super().__init__(config)

    def init(self, bot: ChatbotEngine):
        pass

    def add_functions(self, template: Template, bot: ChatbotEngine):
        """
        Adds custom functions to template @TODO this should be initialized just once at runtime, not a every render!!

        :return:
        """
        for t_func in bot.template_functions_map:  # register template functions from extensions
            bot.logger_df2.debug('Adding template custom function "' + t_func + '"')
            template.globals[t_func] = lambda *args: bot.call_dotflow2_function(t_func, args) #@TODO should call to callback directly

    def render(self, bot: object, template: str, vars: dict) -> str:
        """
        """
        super().render()
        bot.logger_df2.debug('Rendering template: "' + template + '"')
        template = Template(template)


        # add custom functions from plugins
        self.add_functions(template, bot)

        response = template.render(vars)  # return rendered text output

        bot.logger_df2.debug('Template response: ' + response)
