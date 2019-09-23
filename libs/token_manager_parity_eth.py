""""""
from web3 import Web3
import logging
from bbot.core import BBotLoggerAdapter

class TokenManagerParityETH():

    web3 = None

    def __init__(self, config: dict, dotbot: dict) -> None:
        """Initializes class"""
        self.config = config
        self.dotbot = dotbot
        
        self.logger_level = ''

        self.core = None
        self.parity_node_rpc_url = ''
                
        self.logger = BBotLoggerAdapter(logging.getLogger('token_parityeth'), self, self, '')        

    def init(self, core):
        """Initializes some values"""
        pass

    def connect(self):
        if not TokenManagerParityETH.web3:
            self.logger.debug('Connection to node ' + self.parity_node_rpc_url)
            if 'http' in self.parity_node_rpc_url:
                provider = Web3.HTTPProvider(self.parity_node_rpc_url)
            if 'ws://' in self.parity_node_rpc_url:
                provider = Web3.WebsocketProvider(self.parity_node_rpc_url)
            if 'file://' in self.parity_node_rpc_url:
                url = self.parity_node_rpc_url.replace('file://', '') #web3 does not recognize file:// scheme
                provider = Web3.IPCProvider(url)

            TokenManagerParityETH.web3 = Web3(provider)

    def transfer(self, fromAddress: str, toAddress: str, amount: float, credential: str=''):
        self.connect()
        self.logger.debug('Transfering ' + str(amount) + 'ETH from ' + fromAddress + ' to ' + toAddress)
        response = TokenManagerParityETH.web3.parity.personal.sendTransaction( 
            {
                'to': Web3.toChecksumAddress(toAddress), 
                'from': Web3.toChecksumAddress(fromAddress), 
                'value': Web3.toWei(amount, 'ether'),
                'gas': 21000,
                'gasPrice': 0 
            }, 
            credential)
        self.logger.debug('Transaction hash: ' + response.hex())
        return response

        
