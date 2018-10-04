"""Plain text eq match."""
from flow.chatbot_engine import Extension

class PlainTextEqMatch(Extension):
    """PlainTextEqMatch plugin - defined .flow function plainTextEqMatch to
    match based on plain text equal"""


    def __init__(self, flow):
        super().__init__(flow)
        class_name = self.__class__.__module__ + '.' + self.__class__.__name__
        flow.register_dot_flow_function('plainTextEqMatch', {
            'class': class_name, 'method': 'match'})


    def match(self, pattern: str, input_text: str) -> bool:
        """
        Matches the 'pattern' with the user input

        :param pattern: pattern rule
        :param input_text: input text
        """
        return pattern.lower() == input_text.strip().lower()
