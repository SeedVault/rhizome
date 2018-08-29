"""Regex match."""
import re
from flow.chatbot_engine import Extension, FlowError

class RegexMatch(Extension):
    """RegexMatch plugin - defined .flow function regexMatch to match with
    patterns based on regular expresions"""


    def __init__(self, flow):
        super().__init__(flow)
        class_name = self.__class__.__module__ + '.' + self.__class__.__name__
        flow.register_dot_flow_function('regexMatch', {
            'class': class_name, 'method': 'match'})


    def match(self, args: dict) -> bool:
        """
        Matches the 'pattern' with the user input

        :param args extension arguments        
        """
        pattern = args[0]
        input_text = args[1]
        cap = dict()
        result = re.search(pattern, input_text, cap)
        if result == 1: # matched
            # check for named capture and set var
            if cap:
                for var_name, value in cap.items():
                    # only named captures. nonnamed captures are
                    # not going to be saved
                    if not var_name.is_numeric():
                        self.flow.session.set_var(var_name, value)
            return True

        if result == 0:  # not match
            return False

        raise FlowError(f'Bad regex pattern {pattern}')
