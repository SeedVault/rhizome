""""""
import re
from bbot.core import ChatbotEngine, BBotException

class DotFlow2CoreFunctions():
    """."""

    def __init__(self, bot: ChatbotEngine) -> None:
        """
        """

        self.bot = bot
        self.functions = ['input', 'eq', 'gt', 'lt', 'gte', 'lte', 'code', 'goto', ['return', 'df2_return'],
                          'store', 'variable', 'regexMatch', ['and', 'df2_and'], ['or', 'df2_or']]

        for f in self.functions:
            if type(f) is list:
                p_mname = f[1]
                df2_fname = f[0]
            else:
                p_mname = df2_fname = f

            bot.register_dotflow2_function(df2_fname, {'object': self, 'method': p_mname})
            bot.register_template_function(df2_fname, {'object': self, 'method': p_mname})



    ####################################################################################################################

    #### Flow control

    def goto(self, args, f_type):
        # @TODO if target node of the goto does not need to wait for user input, it should execute it directly. If botdev doesn't want this, they should use $gotoAndWait
        """
        Sets internal follow-up context.

        :param args: 0: Node ID where to go next
        :param f_type:
        :return:
        """
        # @TODO check existence of target node
        node_id = args[0]
        self.bot.set_followup_context(node_id)

    def df2_return(self, args, f_ype):
        """
        Returns flow control to the previous caller's context.
        If there is no previous call in the call stack, won't do anything

        :param args:
        :param f_ype:
        :return:
        """

        #@TODO call function is not supported yet. Just reset fu context
        self.bot.logger_df2_debug('$return: No previous call in the stack.')


    #### Storing user data

    def store(self, args, f_type):
        """
        Stores values on user variables.

        :param args:
        :param f_type:
        :return:
        """
        var_name = args[0]
        var_value = args[1]
        self.bot.session.set_var(self.bot.user_id, var_name, var_value)

    def variable(self, args, f_type) -> any:
        """
        Return value stored in user variable

        :param args:
        :param f_type:
        :return:
        """
        var_name = args[0]
        return self.bot.session.get_var(var_name)


    #### Misc

    def input(self, args, f_type):
        """
        Returns user input

        :return:
        """
        return self.bot.request['input']['text']

    def code(self, args, f_type):
        """
        !!!!WARNING!!!! THIS FUNCTION RUNS UNRESTRICTED PYTHON CODE. DON'T EXPOSE IT TO PUBLIC ACCESS!!

        This function is used to run any python code on conditions and responses objects.
        Of course you can use DotFlow2 functions inside it
        :param args:    0: string with python code
                        1: string. 'C' to get expression result (only expressions works). 'R' to run any kind of python code (no result is returned)
        :return:
        """
        code = args[0]
        if type(code) is not str:
            raise Exception('$code: Arg should be string')

        # Transpile $python code into Python code ready to run in DotFlow2 environment
        for f in self.bot.dotflow2_functions_map:
            # shortcut: no need to prefix "self.bot.df2." on all Dotflow2 functions
            code = code.replace(f + '(', 'self.bot.df2.' + f + '(')

        self.bot.logger_df2_debug('$code: Running python code: "' + code + "'...")
        result = None
        if f_type == 'C':           # If it's called from Condition object we need a result from the expression
            result = eval(code)
        elif f_type == 'R':         # If it's called from Responses object we need to freely run the code. No expression returned
            exec(code)

        self.bot.logger_df2_debug('$code: Returning: ' + str(result))
        return result

    #
    # Comparators

    def eq(self, args, f_type):
        """
        Evaluates equivalency between two args

        :return:
        """

        if type(args[0]) is str and type(args[1]) is str:
            response = args[0].strip().lower() == args[1].strip().lower()
        elif args[0].isdigit() and args[1].isdigit():
            response = args[0] == args[1]
        else:
            raise BBotException('$eq: Args are not strings or numbers')
        return response

    def gt(self, args, f_type):
        """
        Evaluates greater-than

        :param args:
        :param f_type:
        :return:
        """
        if args[0].isdigit() and args[1].isdigit():
            response = args[0] > args[1]
        else:
            raise BBotException('$gt: Args are not numbers')
        return response

    def lt(self, args, f_type):
        """
        Evaluates lesser-than

        :param args:
        :param f_type:
        :return:
        """
        if args[0].isdigit() and args[1].isdigit():
            response = args[0] < args[1]
        else:
            raise BBotException('$lt: Args are not numbers')
        return response

    def gte(self, args, f_type):
        """
        Evaluates greater-than or equal

        :param args:
        :param f_type:
        :return:
        """
        if args[0].isdigit() and args[1].isdigit():
            response = args[0] >= args[1]
        else:
            raise BBotException('$gte: Args are numbers')
        return response

    def lte(self, args, f_type):
        """
        Evaluates lesser-than or equal

        :param args:
        :param f_type:
        :return:
        """
        if args[0].isdigit() and args[1].isdigit():
            response = args[0] <= args[1]
        else:
            raise BBotException('$lte: Args are numbers')
        return response

    #
    # Boolean operators

    def df2_and(self, args, f_type):
        """
        Boolean operator AND.
        It accepts unlimited values

        :param args:
        :param f_type:
        :return:
        """
        response = args[0]
        for i in args[1:]:
            response = response and i

        return response

    def df2_or(self, args, f_type):
        """
        Boolean operator OR.
        It accepts unlimited values

        :param args:
        :param f_type:
        :return:
        """
        response = args[0]
        for i in args[1:]:
            response = response or i

        return response


    #
    # Simple pattern matcher

    def regexMatch(self, args, f_type):
        """
        Evaluates regular expression.
        Supports named groups

        :param args:
        :param f_type:
        :return:
        """
        pattern = args[0]
        text = args[1]

        m = re.search(pattern, text)
        if m:
            # look for named groups and store them
            for var_name, var_value in m.groupdict().items():
                if var_value is not None:
                    self.bot.session.set_var(self.bot.user_id, var_name, var_value)
                    self.bot.detected_entities[var_name] = var_value
                    self.bot.logger_df2_debug('$regexMatch: Storing named group "' + var_name + '" with value "' + var_value + '"')
                else:
                    self.bot.logger_df2_debug('$regexMatch: Named group "' + var_name + '" not found.')

            return True
        else:
            return False








