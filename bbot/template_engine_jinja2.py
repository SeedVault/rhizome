"""Template engine."""
from jinja2 import Template
from bbot.core import TemplateEngine

class TemplateEngineJinja2(TemplateEngine):
    """Read configuration from a restful server."""

    def __init__(self, config: dict) -> None:
        """
        Initialize the plugin.

        """
        super().__init__(config)


    def render(self, flow: object, template: str, vars: dict) -> str:
        """
        """
        super().render()
        template = Template(template)
        
        for tfunc in flow.template_functions: # register template functions from extensions
            template.globals[tfunc] = lambda *args: flow.call_dot_flow_function(tfunc, args)

        return template.render(vars) # return rendered text output

        