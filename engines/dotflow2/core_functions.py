""""""
import re
import logging
from bbot.core import ChatbotEngine, BBotException
from engines.dotflow2.chatbot_engine import DotFlow2LoggerAdapter


class DotFlow2CoreFunctions():
    """."""

    def __init__(self, config: dict, dotbot: dict) -> None:
        """

        :param config:
        :param dotbot:
        """
        self.config = config
        self.dotbot = dotbot

        self.logger_level = ''

        self.bot = None
        self.logger = None
        self.functions = []

    def init(self, bot: ChatbotEngine):

        self.bot = bot
        self.logger = DotFlow2LoggerAdapter(logging.getLogger('df2_ext.core'), self, self.bot, 'DF2CoreFnc')

        self.functions = ['input', 'eq', 'gt', 'lt', 'gte', 'lte', 'code', 'goto', 'return',
                          'set', 'get', 'regexMatch', 'and', 'or']

        for f in self.functions:
            bot.register_dotflow2_function(f, {'object': self, 'method': 'df2_' + f})
            bot.register_template_function(f, {'object': self, 'method': 'df2_' + f})



    ####################################################################################################################

    #### Flow control

    def df2_goto(self, args, f_type):
        # @TODO if target node of the goto does not need to wait for user input, it should execute it directly. If botdev doesn't want this, they should use $gotoAndWait
        """
        Sets internal follow-up context.

        :param args: 0: Node ID where to go next
        :param f_type:
        :return:
        """
        # Existence of node id should be done previously. Bot engine will raise an exception if can't find it
        try:
            node_id = self.bot.resolve_arg(args[0], f_type)
        except IndexError:
            raise BBotException({'code': 100, 'function': 'goto', 'arg': 0, 'message': 'Node ID missing.'})

        self.bot.set_followup_context(node_id)

    def df2_return(self, args, f_type):
        """
        Returns flow control to the previous caller's context.
        If there is no previous call in the call stack, won't do anything

        :param args:
        :param f_ype:
        :return:
        """

        #@TODO call function is not supported yet. Just reset fu context
        self.logger.debug('$return: No previous call in the stack.')


    #### Storing user data

    def df2_set(self, args, f_type):
        """
        Stores values on user variables.

        :param args:
        :param f_type:
        :return:
        """
        try:
            var_name = self.bot.resolve_arg(args[0], f_type, True)
        except IndexError:
            raise BBotException({'code': 110, 'function': 'set', 'arg': 0, 'message': 'Variable name missing.'})
        if type(var_name) is not str:
            raise BBotException({'code': 111, 'function': 'set', 'arg': 0, 'message': 'Variable name should be a string.'})

        try:
            var_value = self.bot.resolve_arg(args[1], f_type, True)
        except IndexError:
            raise BBotException({'code': 112, 'function': 'set', 'arg': 1, 'message': 'Variable value missing.'})

        self.bot.session.set_var(self.bot.user_id, var_name, var_value)

    def df2_get(self, args, f_type) -> any:
        """
        Return value stored in user variable

        :param args:
        :param f_type:
        :return:
        """
        try:
            var_name = self.bot.resolve_arg(args[0], f_type, True)
        except IndexError:
            raise BBotException({'code': 120, 'function': 'get', 'arg': 0, 'message': 'Variable name missing.'})
        if type(var_name) is not str:
            raise BBotException({'code': 121, 'function': 'get', 'arg': 0, 'message': 'Variable name should be a string.'})

        return self.bot.session.get_var(self.bot.user_id, var_name)


    #### Misc

    def df2_input(self, args, f_type):
        """
        Returns user input

        :return:
        """
        return self.bot.request['input']['text']

    def df2_code(self, args, f_type):
        """
        !!!!WARNING!!!! THIS FUNCTION RUNS UNRESTRICTED PYTHON CODE. DON'T EXPOSE IT TO PUBLIC ACCESS!!
        @TODO this will be replaced by Templator template

        This function is used to run any python code on conditions and responses objects.
        Of course you can use DotFlow2 functions inside it
        :param args:    0: string with python code
                        1: string. 'C' to get expression result (only expressions works). 'R' to run any kind of python code (no result is returned)
        :return:
        """
        try:
            code = self.bot.resolve_arg(args[0], f_type)
        except IndexError:
            raise BBotException({'code': 130, 'function': 'code', 'arg': 0, 'message': 'Code missing.'})

        if type(code) is not str:
             raise BBotException({'code': 131, 'function': 'code', 'arg': 0, 'message': 'Argument 0 should be string'})

        # Transpile $code code into Python code ready to run in DotFlow2 environment
        for f in self.bot.dotflow2_functions_map:
            # shortcut: no need to prefix "self.bot.df2." on all Dotflow2 functions
            code = code.replace(f + '(', 'self.bot.df2.' + f + '(')

        self.logger.debug('$code: Running python code: "' + code + "'...")
        result = None
        if f_type == 'C':           # If it's called from Condition object we need a result from the expression
            result = eval(code)
        elif f_type == 'R':         # If it's called from Responses object we need to freely run the code. No expression returned
            exec(code)

        self.logger.debug('$code: Returning: ' + str(result))

        return result

    #
    # Comparators

    def df2_eq(self, args, f_type):
        """
        Evaluates equivalency between two values

        :return:
        """
        try:
            value1 = self.bot.resolve_arg(args[0], f_type)
        except IndexError:
            raise BBotException({'code': 140, 'function': 'eq', 'arg': 0, 'message': 'Value in arg 0 is missing.'})

        try:
            value2 = self.bot.resolve_arg(args[1], f_type)
        except IndexError:
            raise BBotException({'code': 141, 'function': 'eq', 'arg': 0, 'message': 'Value in arg 1 is missing.'})

        return value1 == value2

    def df2_gt(self, args, f_type):
        """
        Evaluates greater-than

        :param args:
        :param f_type:
        :return:
        """
        try:
            value1 = self.bot.resolve_arg(args[0], f_type)
        except IndexError:
            raise BBotException({'code': 150, 'function': 'gt', 'arg': 0, 'message': 'Value in arg 0 is missing.'})

        try:
            value2 = self.bot.resolve_arg(args[1], f_type)
        except IndexError:
            raise BBotException({'code': 151, 'function': 'gt', 'arg': 1, 'message': 'Value in arg 1 is missing.'})

        return value1 > value2

    def df2_lt(self, args, f_type):
        """
        Evaluates lesser-than

        :param args:
        :param f_type:
        :return:
        """
        try:
            value1 = self.bot.resolve_arg(args[0], f_type)
        except IndexError:
            raise BBotException({'code': 150, 'function': 'lt', 'arg': 0, 'message': 'Value in arg 0 is missing.'})

        try:
            value2 = self.bot.resolve_arg(args[1], f_type)
        except IndexError:
            raise BBotException({'code': 151, 'function': 'lt', 'arg': 1, 'message': 'Value in arg 1 is missing.'})

        return value1 < value2

    def df2_gte(self, args, f_type):
        """
        Evaluates greater-than or equal

        :param args:
        :param f_type:
        :return:
        """
        try:
            value1 = self.bot.resolve_arg(args[0], f_type)
        except IndexError:
            raise BBotException({'code': 150, 'function': 'gte', 'arg': 0, 'message': 'Value in arg 0 is missing.'})

        try:
            value2 = self.bot.resolve_arg(args[1], f_type)
        except IndexError:
            raise BBotException({'code': 151, 'function': 'gte', 'arg': 1, 'message': 'Value in arg 1 is missing.'})

        return value1 >= value2

    def df2_lte(self, args, f_type):
        """
        Evaluates lesser-than or equal

        :param args:
        :param f_type:
        :return:
        """
        try:
            value1 = self.bot.resolve_arg(args[0], f_type)
            tmp = float(value1)
        except IndexError:
            raise BBotException({'code': 150, 'function': 'lte', 'arg': 0, 'message': 'Value in arg 0 is missing.'})

        try:
            value2 = self.bot.resolve_arg(args[1], f_type)
        except IndexError:
            raise BBotException({'code': 151, 'function': 'lte', 'arg': 1, 'message': 'Value in arg 1 is missing.'})

        return value1 <= value2

    #
    # Logical operators

    def df2_and(self, args, f_type):
        """
        Logical operator AND.
        It accepts unlimited values

        :param args:
        :param f_type:
        :return:
        """
        if len(args) == 0:
            raise BBotException({'code': 160, 'function': 'and', 'arg': 0, 'message': 'Value in arg 0 is missing.'})

        if len(args) == 1:
            raise BBotException({'code': 161, 'function': 'and', 'arg': 1, 'message': 'Value in arg 1 is missing.'})

        for arg in args:
            resolved_arg = self.bot.resolve_arg(arg, f_type)
            if not resolved_arg:
                return False

        return True

    def df2_or(self, args, f_type):
        """
        Logical operator OR.
        It accepts unlimited values

        :param args:
        :param f_type:
        :return:
        """
        if len(args) == 0:
            raise BBotException({'code': 170, 'function': 'or', 'arg': 0, 'message': 'Value in arg 0 is missing.'})

        if len(args) == 1:
            raise BBotException({'code': 171, 'function': 'or', 'arg': 1, 'message': 'Value in arg 1 is missing.'})

        for arg in args:
            resolved_arg = self.bot.resolve_arg(arg, f_type)
            if resolved_arg:
                return True

        return False

    #
    # Simple pattern matcher

    def df2_regexMatch(self, args, f_type):
        """
        Evaluates regular expression.
        Supports named groups

        :param args:
        :param f_type:
        :return:
        """
        try:
            pattern = self.bot.resolve_arg(args[0], f_type)
        except IndexError:
            raise BBotException({'code': 180, 'function': 'regexMatch', 'arg': 0, 'message': 'Pattern in arg 1 is missing.'})

        try:
            text = self.bot.resolve_arg(args[1], f_type)
        except IndexError:
            raise BBotException({'code': 181, 'function': 'regexMatch', 'arg': 1, 'message': 'Text in arg 1 is missing.'})

        m = re.search(pattern, text)
        if m:
            # look for named groups and store them
            for var_name, var_value in m.groupdict().items():
                if var_value is not None:
                    self.bot.session.set_var(self.bot.user_id, var_name, var_value)
                    self.bot.detected_entities[var_name] = var_value
                    self.logger.debug('$regexMatch: Storing named group "' + var_name + '" with value "' + var_value + '"')
                else:
                    self.logger.debug('$regexMatch: Named group "' + var_name + '" not found.')

            return True
        else:
            return False


