"""Text."""
from flow.engine import Extension

class Text(Extension):
    """Text"""

    def __init__(self, flow):
        super().__init__(flow)
        class_name = self.__class__.__module__ + '.' + self.__class__.__name__
        flow.register_dot_flow_function('text', {
            'class': class_name, 'method': 'plugin_GetOutput'})


    def get_output(self):
        """Get response for node."""
        output = dict()
        return output
