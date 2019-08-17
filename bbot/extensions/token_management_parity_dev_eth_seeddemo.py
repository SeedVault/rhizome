""""""
import logging
import codecs
import smokesignal
from web3 import Web3
from bbot.core import BBotCore, ChatbotEngine, BBotException, BBotLoggerAdapter, BBotExtensionException

class TokenManagementParityDevETHSeedDemo():
    """Executes payments on a private development Ethereum parity node using personal module for seed token demo page"""

    def __init__(self, config: dict, dotbot: dict) -> None:
        """
        Initialize the plugin.
        """
        self.config = config
        self.dotbot = dotbot
        
        self.logger_level = ''

        self.seed_demo_node_rpc_url = ''
        self.seed_demo_token_address = ''
        self.seed_demo_token_password = ''
        self.seed_demo_volley_to_address = ''
        self.seed_demo_volley_cost = ''
        self.seed_demo_function_to_address = ''
        self.seed_demo_function_cost = ''

        self.core = None
        self.logger = None

    def init(self, core: BBotCore):
        """
        :param bot:
        :return:
        """
        self.core = core
        self.logger = BBotLoggerAdapter(logging.getLogger('ext.token_demo'), self, self.core.bot, '$token')                

        smokesignal.on(BBotCore.SIGNAL_CALL_BBOT_FUNCTION_AFTER, self.function_payment)
        smokesignal.on(BBotCore.SIGNAL_GET_RESPONSE_AFTER, self.volley_payment)

        self.logger.debug('Connection to node ' + self.seed_demo_node_rpc_url)
        self.web3 = Web3(Web3.HTTPProvider(self.seed_demo_node_rpc_url))
            
    def volley_payment(self, data):
        """
        """               
        self.logger.debug('Paying volley activity')        
        self.payment(self.seed_demo_token_address, self.seed_demo_volley_to_address, self.seed_demo_volley_cost)

    def function_payment(self, data):
        """
        """
        if data['register_enabled'] is True:
            self.logger.debug('Paying function activity: ' + str(data))        
            self.payment(self.seed_demo_token_address, self.seed_demo_function_to_address, self.seed_demo_function_cost)

    def payment(self, fromAddress, toAddress, value):
        """
        """
        self.logger.debug('Transfering ' + value + 'ETH from ' + fromAddress + ' to ' + toAddress)
        response = self.web3.parity.personal.sendTransaction( 
            {
                'to': Web3.toChecksumAddress(toAddress), 
                'from': Web3.toChecksumAddress(fromAddress), 
                'value': Web3.toWei(value, 'ether'),
                'gas': 21000,
                'gasPrice': 0 
            }, 
            self.seed_demo_token_password)
        self.logger.debug('Transaction hash: ' + response.hex())
        