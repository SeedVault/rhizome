"""Multimedia."""
from flow.engine import Extension

class Media(Extension):
    """Media plugin - defines .flow functions video, image and audio"""


    def __init__(self, flow):
        super().__init__(flow)
        class_name = self.__class__.__module__ + '.' + self.__class__.__name__
        flow.register_dot_flow_function('media', {
            'class': class_name, 'method': 'get_response'})
        flow.register_dot_flow_function('video', {
            'class': class_name, 'method': 'get_response'})
        flow.register_dot_flow_function('image', {
            'class': class_name, 'method': 'get_response'})
        flow.register_dot_flow_function('audio', {
            'class': class_name, 'method': 'get_response'})


    def get_response(self, node):
        """Get response for node."""
        self.flow.set_output('card', node['info'])
