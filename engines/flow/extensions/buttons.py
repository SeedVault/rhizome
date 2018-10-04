"""Buttons."""
from flow.chatbot_engine import Extension

class Buttons(Extension):
    """
    Buttons plugin.

    This pseudo function will be called on each BBot->setResponse() and will
    provide buttons to the output if isButton attr is true will not be needed
    with dotflow2
    """


    def __init__(self, flow):
        super().__init__(flow)
        class_name = self.__class__.__module__ + '.' + self.__class__.__name__
        flow.register_dot_flow_function('buttons', {
            'class': class_name, 'method': 'get_response'})


    def get_response(self, args):
        """Get response for node."""

        node = args[0]
        output = self.get_buttons(node)
        for out in output:
            self.flow.set_output('buttons', out)


    def get_buttons(self, node):
        buttons = []        
        for conn in node['connections']:
            if conn.get('is_button', None):
                label = conn['if']['value'][0]
                if 'name' in conn and len(conn['name']) > 0:
                    label = conn['name']
                buttons.append(
                    {
                        'label': label,
                        'input': conn['if']['value'][0]
                    }
                )
        return buttons
