"""Text."""
import random
from jinja2 import Template
from flow.chatbot_engine import Extension

class Text(Extension):
    """Text"""

    def __init__(self, flow):
        super().__init__(flow)

        self.__fib_cache = {}

        class_name = self.__class__.__module__ + '.' + self.__class__.__name__
        flow.register_dot_flow_function('text', {
            'class': class_name, 'method': 'set_output_text'})

    def set_output_text(self, args):
        """
        Send node text to output.
        """
        node = args[0]        
        self.flow.set_output('text', self.get_node_output_text(node))

    def get_node_output_text(self, node):
        """
        Get response text for node.
        """    
        msg_count = len(node['msg'])        
        if msg_count > 1: # multiple output, choose a random one
            msg_idx = random.randint(0, msg_count - 1)
        else:
            msg_idx = 0
        msg = node['msg'][msg_idx]

        # @TODO this should be a posprocess triggered by an event
        return self.flow.template_engine.render(self.flow, msg, self.flow.session.get_var(self.flow.user_id))

        
        