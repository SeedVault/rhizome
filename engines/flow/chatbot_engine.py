"""BBot engine based on Flow."""
import importlib
import numbers
import more_itertools as mit
from bbot.core import ChatbotEngine
# from flow.extensions.text import Text

class FlowError(Exception):
    """Flow error."""

class Flow(ChatbotEngine):
    """BBot engine based on Flow."""

    def __init__(self, config: dict, dotbot: dict) -> None:
        """
        Initialize the plugin.

        :param config: Configuration values for the instance.
        """
        super().__init__(config)

        # 
        self.dotbot_reader = None # ConfigReader        
        self.nodes_reader = None # ConfigReader
        self.session = None # Session
        self.template_engine = None # TemplateEngine
        self.cache = None # Cache
        
        #
        self.inp = {}                   # type: dict
        self.out = {}                   # type: dict
        self.flow_functions_map = {}    # type: dict
        self.plugins_objects = {}       # type: dict
        self.dotbot = {} # type: dict
        self.bot_nodes = {} # type: dict
        self.extensions = {} # type: list
        self.plugin_functions = {} # type: dict
        self.extensions_instances = {} # type: dict
        self.template_functions = [] # type: list
        
        # Credentials and server data
        self.weather_api_key = '' # type: str
        self.chatscript_flowext_host = '' # type: str
        self.chatscript_flowext_port = 0 # type: int
        self.chatscript_flowext_bot_id = '' # type: str
        self.azure_location = '' # type: str
        self.azure_subscription_key = '' # type: str
        
        #
        self.last_matched_node_id = ''
        self.last_matched_connection = ''
        self.last_matched_pattern = ''
        self.last_matched_node_found_in = ''

        # Load enabled extensions
        self.extensions = []
        for enabled_extension in config['extensions']:
            parts = enabled_extension.strip().split(".")
            class_name = parts.pop()
            package_name = ".".join(parts)
            module = importlib.import_module(package_name)
            dynamic_class = getattr(module, class_name)
            extension = dynamic_class(self)
            self.extensions_instances[enabled_extension.strip()] = extension
            


    def register_dot_flow_function(self, flow_function, plugin_function):
        """
        Register .flow $function mapped to its plugin method.

        :param flow_function: .flow function name
        :param plugin_function: callable array class/method of plugin method
        """
        self.flow_functions_map[flow_function] = plugin_function

        if plugin_function.get('is_template_function', None):
            self.template_functions.append(flow_function)


    def call_dot_flow_function(self, flow_function, args):
        """
        Executes the plugin function based on .flow function name.

        :param flow_function: .flow function name to be executed.
        :param args: dict of arguments.
        :return Any value returned by the function
        """
        if flow_function not in self.flow_functions_map:
            raise FlowError(f'Unknown .flow function: {flow_function}')
        
        key = self.flow_functions_map[flow_function]['class']
        ext = self.extensions_instances[key]
        method = getattr(ext, self.flow_functions_map[flow_function]['method'])
        return method(args)


    def get_raw_output(self) -> dict:
        """Return whole output object

        :return: whole output object
        """
        return self.out


    def get_response(self, request: dict) -> dict:
        """
        Return a response based on the input data.

        :param request: A dictionary with input data.
        :return: A response to the input data.
        """
        
        if not (request['user_id'] and request['bot_id'] and request['org_id']):
            raise FlowError('Invalid request data')
        self.user_id = request['user_id']
        self.bot_id = request['bot_id']
        self.org_id = request['org_id']
        self.dotbot = self.dotbot_reader.read(self.bot_id)      
        self.bot_nodes = self.nodes_reader.read(self.bot_id)
        input_text = request['input']['text']
        self.set_input('text', input_text)
        self.out = {}
        output = ''
        # Is it a command?
        if input_text.find(":") == 0:
            output = ''
            if input_text == ':help':
                output = 'Commands:\nreset all:    Delete all user data.'
            elif input_text == ':reset all':
                self.session.reset_all(self.user_id)
                output = 'User data has been deleted.'
            else:
                output = 'Unknown command. Type :help to list available commands.'
            self.set_output('text', output)
            return self.create_response(self.get_raw_output())
        # get node on which the user is at
        cNode = self.get_current_node()

        #look for match and output text
        output = ''
        mNode = None
        if not cNode: # no current node, it's initial welcome message
            self.logger_cs.debug("There is no current node. This is first welcome"
                                 + " mesage. Ignoring input.")
            # getting first node will provide the global user intents
            cNode = self.get_first_node()
            self.set_current_node_id(cNode['id'])
            self.set_response_by_node(cNode)
            return self.create_response(self.get_raw_output())
        else:
            # not first,  look for matchings on context current node and if it
            # fails go for global user intents in the first node
            match = self.find_flow_match(cNode)  # this returns matched
                                                 # connection object, not node

            if match:  # there is a match

                # check if we need to store input value in persistent storage
                # only store value if the match is in context, not on global
                # intents. doesn't matter if there is no node pointed from the
                # matched connection
                if cNode.get('fieldId', None) and self.last_matched_node_found_in == 'context':                                        
                    self.session.set_var(self.user_id, cNode['fieldId'], self.get_input())

                    # add question/answer pair to the form if formId is defined
                    form_id = cNode.get('formId', None)
                    if form_id:
                        # get text output from previous node to get the question
                        # pText = Text(self)
                        # cNodeOutput = pText.get_output(cNode)
                        cNodeOutput = self.extensions_instances['flow.extensions.text.Text'].get_node_output_text(cNode)
                        self.session.set(
                            self.user_id,
                            f"formVars.{form_id}.{cNode['fieldId']}",
                            {'question': cNodeOutput,
                             'answer': self.get_input()}
                        )
                        self.logger_cs.debug("Variable " + cNode['fieldId'] + " with value '" + self.get_input() + "' on formId " + form_id)
                    else:
                        self.logger_cs.debug("Variable " + cNode['fieldId'] + " with value '" + self.get_input() + "'")
                    


                # we have a match so set current node to keep the user on the rejoinder
                if self.last_matched_node_id: # mNode might be null if there is
                                              # no node set for the matched
                                              # connection
                    mNode = self.get_node(self.last_matched_node_id)
                    new_current_node = mNode
                    self.set_current_node_id(new_current_node['id'])
                    self.set_response_by_node(mNode) # this returns all output types from the node
                else:
                    # there is a match but there is no node defined.
                    # set current node to root. output will be the same as it
                    # there is no match
                    new_current_node = self.get_first_node()
                    self.set_current_node_id(new_current_node['id'])
                    self.logger_cs.debug("There is no node defined for the matched connection. Set current node to root")

                self.logger_cs.debug("New current node id " + new_current_node['id'])

            if not mNode: # if there is no match..
                # botdev should take care of no matches.
                # Add a wildcard intent to handle it
                self.set_output('text', '')

        return self.create_response(self.get_raw_output())


    def find_flow_match(self, context_node=None) -> str:
        """
        This will match current user input with the speified node.

        If it doesnt match, it will try to match user intent with global
        user intents from toplevel node.

        :param context_node: Node to try first match (usually the current node
                            there the user is as context)
        :return: Node id that the flow should go as it matched the user intent.
        """
        if not context_node:
            context_node = self.get_current_node()

        self.logger_cs.debug("Find match for user text \"" + self.inp['input']['text'] + "\" on context intent node id {" + context_node['id'] + "}...")

        # first try to match current node
        match = self.find_context_pattern_match(context_node)

        if match:
            self.last_matched_node_found_in = 'context'            
            self.logger_cs.debug("Match found on context intent node to node id " + str(self.last_matched_node_id))
            return match
        else:
            # second try to match toplevel node
            first_node = self.get_first_node()
            if first_node != context_node:
                self.logger_cs.debug("Match not found, try to match toplevel intent id (" + first_node['id'] + ")")

                match = self.find_context_pattern_match(first_node)
                if match:
                    self.last_matched_node_found_in = 'global'
                    self.logger_cs.debug("Match found on toplevel intent to node id " + self.last_matched_node_id)
                    return match
                else:
                    self.logger_cs.debug("Match not found on toplevel node")
            else:
               self.logger_cs.debug("Match not found, this is toplevel node, there is nothing more to do")

        return False



    def find_context_pattern_match(self, node) -> bool:
        """
        Convenience method to iterate through the connection's node to find match.

        :param node: a node
        :return: TRUE if match, otherwise FALSE
        """
        scores = dict()
        for c in node['connections']:
            if 'if' in c:
                if self.eval_conditional(c):
                    # eval conditional first as it's faster
                    # with flow 2.0 this will not be hardcoded.
                    # flow 2.0 will have a nested conditional criteria functions                       
                    # @TODO it might happen we need do this type of conditionals
                    # after matching as ML like luis will provide entities setting variables
                    # which we will want to evaluate in the conditionals intent
                    for pattern in c['if']['value']:                        
                        match = self.find_pattern_match(pattern, self.get_input(), c)

                        if match:  #match first TRUE
                            # @TODO would be better if current method returns
                            # an array/object with this data instead of setting
                            #  it on $this
                            self.last_matched_node_id = c['if']['then'] if c['if']['then'] != 'end' else None
                            self.last_matched_connection = c
                            self.last_matched_pattern = pattern
                            return True
                       
                        if match and isinstance(match, numbers.Number): # if it's numeric then it's a score. we need to collect all scores from node. then match high score
                            self.logger_cs.debug("Pattern match score " + str(match))

                            # if value is already set, then ignore. we want the first node with the value, so first node is matched
                            if not scores.get(match, False):
                                scores[match] = {
                                    'last_matched_node_id': c['if']['then'] if c['if']['then'] != 'end' else None,
                                    'last_matched_connection': c,
                                    'last_matched_pattern': pattern
                                }

        # get high score is any and return true
        if isinstance(scores, dict) and scores.items(): # there are matched intents with score. return higher score
            
            best_score = max(scores.keys())
            high_score_match = scores[best_score]
            self.last_matched_node_id = high_score_match['last_matched_node_id']
            self.last_matched_connection = high_score_match['last_matched_connection']
            self.last_matched_pattern = high_score_match['last_matched_pattern']
            self.logger_cs.debug("Best score match: " + str(best_score) + " - pattern: " + high_score_match['last_matched_pattern'])
            return True

        return False


    def eval_conditional(self, connection):
        """
        Executes evalConditional .flow function.

        (with .flow 2.0 this function wont be needed).

        :param conn: Connection object from the node.
        :return: True if it is evaluated as True
        """
        if 'pre' in connection['if']:
            return self.call_dot_flow_function('variableEval', [connection['if']['pre']])
        else:
            # if there is no conditional, just eval true
            return True


    def find_pattern_match(self, pattern, input_text, connection):
        """
        Finds pattern match based on the defined match function in .flow node connection.

        :param pattern: Pattern defined in connection node
        :param input_text: Input text
        :param connection: Object
        :return: True if it is a match
        """
        if connection['if']['op']:
            opts = dict()
            opts['op'] = connection['if']['op'] 
            opts['intentLabel'] = connection.get('name', None)

            if opts['op'] == 'pattern' or opts['op'] == 'eq': # pattern and eq ops are dicarded
                opts['op'] = 'chatscript'

            if connection['if']['context'] == 'sentimentAnalysis':
                opts['op'] = 'sentiment'

            self.logger_cs.debug(f"Test pattern '{pattern}' with op {opts['op']}")
            return self.call_dot_flow_function(opts['op'], [pattern, input_text, opts])

        # if there is no conditions, return true
        return True


    def set_response_by_node(self, node) -> str:
        """
        Returns output text from the specified node.

        If the node has multiple strings it will return a random pick.

        :param node: Node to get output text message
        :return: Output text message
        """
        
        # with .flow 2.0 this speacial treatment won't be needed
        # check if there are more outputs
        
        if node.get('info', False):
            if node['type'] == 'process' or node['type'] == 'card':
                 self.call_dot_flow_function(node['subType'], [node])
            else:
                 self.call_dot_flow_function(node['type'], [node])

        #check and send buttons to output
        self.call_dot_flow_function('buttons', [node])

        # regular msg
        if node['msg']:
            self.call_dot_flow_function('text', [node])


    def set_input(self, input_type, input_text):
        """
        Load the user input to the object

        :param input_type: Input type
        :param input_text: Input text
        """
        if 'input' not in self.inp:
            self.inp['input'] = dict()
        self.inp['input'][input_type] = input_text


    def get_input(self, input_type: str = 'text') -> str:
        """
        Returns user input

        :param input_type: Input type, defaults to 'text'
        :return: Input type
        """
        return self.inp['input'][input_type]


    def get_current_node(self):
        """
        Returns the current node where the user is.

        This is the volley position which brings context to the user intent.

        :return: Node data
        """
        current_node_id = self.get_current_node_id()
        if current_node_id:
            return self.get_node(current_node_id)
        else:
            return None


    def get_node_by_connection(self, connection):
        """
        Returns node object by connection

        :param connection: Conecction
        :return: Node data
        """
        node_id = self.get_node_id_by_connection(connection)
        if node_id:
            return self.get_node(node_id)
        else:
            return None


    def get_node_id_by_connection(self, connection):
        """
        Returns node id by connection.

        :param connection: Connection
        :return: Node ID
        """
        return connection['if']['then'] if connection['if']['then'] != 'end' else None


    def get_node(self, node_id, return_resolved_node=True):
        """
        Returns node array by its id.

        :param node_id: Node ID
        :param return_resolved_node: True to return node pointed by flowId if it's the case.
        :return: Node data.
        """
        for node in self.bot_nodes:
            # ugly thing I have to do because author's tool is not putting the right name on the flow
            if node['id'] == node_id or node['name'] == 'flow' + str(node_id):
                # @TODO fix this on author's tool!
                break

        if node:
            if return_resolved_node:
                if node['type'] == 'flowId':
                    if node.get('flowId', None):   # check if it's a flow or node connection
                        self.logger_cs.debug("It's a connection flow. Finding actual node...")
                        # look for the real node
                        flow_id = node['flowId']
                        root_node = self.get_node(flow_id)
                        m_node_id = root_node['connections'][0]['default']
                        if m_node_id == 'end':
                            m_node_id = None
                            node = None
                            self.logger_cs.debug("Flow is empty, discarding")
                        else:
                            self.logger_cs.debug("Found node id " + m_node_id)
                            node = self.get_node(m_node_id)
                    else:
                        self.logger_cs.debug("It's a connection node. ")
                        m_node_id = node['connections'][0]['default']
                        node = self.get_node(m_node_id)
        else:
            self.logger_cs.debug('node not found in flow')
            raise FlowError('node not found in flow')

        return node


    def get_first_node(self):
        """
        Returns the first node in which we have all global user intents

        :return: First node
        """
        for node in self.bot_nodes:
            if node['type'] != 'root':
                return node
        # raise FlowError('first node not found')


    def get_current_node_id(self) -> str:
        """
        Returns user current node id

        :return: Node UUID
        """
        return self.session.get(self.user_id, 'currentNodeId')


    def set_current_node_id(self, node_id):
        """
        Sets current node id

        :param node_id: Node UUID
        """
        self.session.set(self.user_id, 'currentNodeId', node_id)


    def set_output(self, my_type: str, output):
        """
        Sets bot output

        :param output: Bot output
        """
        if not my_type in self.out:
            self.out[my_type] = []

        self.out[my_type].append(output)


    def get_output(self, my_type: str = 'text'):
        """
        Return bot output

        :param my_type: Bot output
        """
        return self.out[my_type]


    def get_output_type_list(self):
        return self.out.keys()



class Extension():
    """Base class for extensions."""

    def __init__(self, flow: Flow) -> None:
        self.flow = flow


def extensions_cache(func):
    """
    Decorator to apply cache to flow extensions
    @TODO add ttl 5min
    """
    def function_wrapper(self, args):         
        # key = botid_methodname_arg0_arg1_arg2
        # adds args only if they are string, integer or boolean (avoiding nonhashagle values [even in nested values])        
        key = self.flow.bot_id + "_" + func.__name__
        for arg in args:
            if isinstance(arg, (str, int, bool)):
                key += "_" + str(arg)
        cached = self.flow.cache.get(key)
        if cached is None:
            value = func(self, args)                
            self.flow.cache.set(key, value)
            return value
        else:
            return cached            
    return function_wrapper
