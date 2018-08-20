"""Variable Eval."""
from flow.engine import Extension

class VariableEval(Extension):
    """
    VariableEval plugin - defines pseudo function variableEval.

    This will be called on each matched node to evaluate any conditional
    defined in the flow.
    """

    def __init__(self, flow):
        super().__init__(flow)
        class_name = self.__class__.__module__ + '.' + self.__class__.__name__
        flow.register_dot_flow_function('variableEval', {
            'class': class_name, 'method': 'match'})


    def match(self, pre):
        """Evaluate conditions."""
        var_name = pre['var_name']
        oper = pre['op']
        value = pre['value']
        var_value = self.flow.session.get_var(var_name)
        ret = None
        if oper == 'eq':
            ret = var_value.strip().lower() == value.strip().lower()
        elif oper == 'neq':
            ret = var_value.strip().lower() != value.strip().lower()
        elif oper == 'gt':
            ret = var_value > value if var_value.isdigit() else None
        elif oper == 'lt':
            ret = var_value < value if var_value.isdigit() else None
        return ret
