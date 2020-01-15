"""Manages tokens with the Seed Wallet"""
import logging
import json
#from requests_futures.sessions import FuturesSession
import requests
from bbot.core import BBotLoggerAdapter
from bbot.extensions.token_manager import TokenManagerInsufficientFundsException

class TokenManagerSeedWallet():

    web3 = None

    def __init__(self, config: dict, dotbot: dict) -> None:
        """Initializes class"""
        self.config = config
        self.dotbot = dotbot
        
        self.logger_level = ''

        self.core = None
        self.seed_wallet_api_key = ''
        self.seed_wallet_url = ''
                
        self.logger = BBotLoggerAdapter(logging.getLogger('token_seedwallet'), self, self, '')        

    def init(self, core):
        """Initializes some values"""
        pass

    def transfer(self, fromUsername: str, toUsername: str, amount: float, credential: str=''):
        """
        Transfers tokens from one user to another

        :param fromUsername: (string) Username source
        :param toUsername: (string) Username destination
        :param amount: (float) amount of tokens to be transfered
        :param credential: (string) optional. Credentials needed to move funds from source (usually passphrase or private key)
        :returns: (string) TX hash
        """        
        self.logger.debug('Transfering ' + str(amount) + ' SEED from user ' + fromUsername + ' to user ' + toUsername)
        payload = {
            'username': fromUsername,
            'to': toUsername,
            'amount': str(amount)
        }
        r = self.do_request('post', 'send', payload)
        
        try:
            aw = r.json()
        except json.decoder.JSONDecodeError: 
            raise Exception('Seed Wallet error response: ' + r.text)
        
        if r.status_code != 200:
            # check if the error is insufficient funds
            if r.status_code == 422 and aw['errors'].get('amount', {}).get('message') == 'domain.wallet.validation.insufficient_funds':
                raise TokenManagerInsufficientFundsException()

            raise Exception('Seed Wallet error response: ' + str(aw))

        self.logger.debug('Transaction hash: ' + str(aw['transactionId']))
        return aw['transactionId']

    def get_balance(self, username: str):
        """
        """
        self.logger.debug('Getting user balance')
        r = self.do_request('get', 'balance', {'username': username})
        
        aw = r.json()
        if r.status_code != 200:
            raise Exception('Seed Wallet error response: ' + str(aw))
        
        return float(aw['balance'])

    def do_request(self, type: str, method: str, payload: str=dict):
        """
        """
        headers = {'API-INTEGRATION-KEY': self.seed_wallet_api_key, "Content-type": "application/json"}
        self.logger.debug('Requesting to Seed Wallet at url ' + self.seed_wallet_url + method)
        if type == 'post':            
            r =  requests.post(self.seed_wallet_url + method, json=payload, headers=headers)
        if type == 'get':
            r =  requests.get(self.seed_wallet_url + method, params=payload, headers=headers)
        self.logger.debug('Seed Wallet response: Code: ' + str(r.status_code) + ': ' + str(r.text[0:300]))
        return r
        