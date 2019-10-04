"""Token Manager"""
import logging
import codecs
import smokesignal
from bbot.core import BBotCore, BBotCoreHalt, ChatbotEngine, BBotException, BBotLoggerAdapter, BBotExtensionException

class TokenManager():
    """Executes payments on a private development Ethereum parity node using personal module for seed token demo page"""

    SUSCRIPTION_TYPE_FREE = 'free'
    SUSCRIPTION_TYPE_PER_USE = 'perUse'
    SUSCRIPTION_TYPE_MONTHLY = 'monthly'

    def __init__(self, config: dict, dotbot: dict) -> None:
        """
        Initialize the plugin.
        """
        self.config = config
        self.dotbot = dotbot
        
        self.logger_level = ''        
        self.minimum_accepted_balance = 5
        self.core = None    
        self.token_manager = None

    def init(self, core: BBotCore):
        """
        :param bot:
        :return:
        """
        self.core = core
        self.logger = BBotLoggerAdapter(logging.getLogger('ext.token_mgnt'), self, self.core.bot, '$token')                

        smokesignal.on(BBotCore.SIGNAL_CALL_BBOT_FUNCTION_AFTER, self.function_payment)
        smokesignal.on(BBotCore.SIGNAL_GET_RESPONSE_AFTER, self.volley_payment)
        #smokesignal.on(BBotCore.SIGNAL_GET_RESPONSE_BEFORE, self.payment_check)  disabled for demo

    def payment_check(self, data):
        """
        Check before anything if the payment for the service is paid for current period
        """
        
        if self.core.get_publisher_subscription_type() == TokenManager.SUSCRIPTION_TYPE_MONTHLY:
            self.logger.debug('Monthly suscription. Will check payment status')
            pstatus = self._check_period_payment_status(TokenManager.SUSCRIPTION_TYPE_MONTHLY)
            self.logger.debug('Last payment date: ' + pstatus['last_payment_date'] + ' Payment status: ' + pstatus['status'])
            if pstatus['status'] == False:
                self.core.reset_output()
                self.core.bbot.text('Sorry, the bot is not available at this moment. Please try again later.') # @TODO ?
                raise BBotCoreHalt('Bot halted by monthly paiment not paid')    
                
        if self.core.get_publisher_subscription_type() == TokenManager.SUSCRIPTION_TYPE_PER_USE and self.get_bot_volley_cost() > 0:
            self.logger.debug('Per use suscription. Will check balance first')
            if not self.previous_checkings():
                return

            pbalance = self.token_manager.get_balance(self.core.get_publisher_id())
            if pbalance < self.minimum_accepted_balance:
                self.logger.debug('Publisher balance is less than ' + str(self.minimum_accepted_balance))                
                self.insufficient_funds()
                
    def check_period_payment_status(self, period_type):
        return {'last_payment_date': 123123123, 'status': True}

    def volley_payment(self, data):
        """
        Volley payment from publisher to bot owner
        """   

        if self.core.get_publisher_subscription_type() == TokenManager.SUSCRIPTION_TYPE_FREE:
            self.logger.debug('Free suscription. No payment needed.')
            return
        if self.core.get_publisher_subscription_type() == TokenManager.SUSCRIPTION_TYPE_MONTHLY:
            self.logger.debug('Monthly suscription. No volley payment needed.')
            return
        if self.core.get_publisher_subscription_type() == TokenManager.SUSCRIPTION_TYPE_PER_USE:

            volley_cost = self.get_bot_volley_cost()

            if volley_cost is not None: # register bot volleys only if it has declared volley cost (can be 0)
                self.logger.debug('Paying volley activity')        
                if not self.previous_checkings():
                    return

                try:
                    self.token_manager.transfer(self.core.get_publisher_id(), self.dotbot.owner_id, volley_cost)
                except TokenManagerInsufficientFundsException as e:
                    self.insufficient_funds()

    def function_payment(self, data):
        """
        Function payment from bot owner to service owner
        """
        if data['register_enabled'] is True:
            self.logger.debug('Paying function activity: ' + str(data))        

            if data['data'].get('subscription_type') == TokenManager.SUSCRIPTION_TYPE_FREE:
                self.logger.debug('Free suscription. No payment needed.')
                return
            if data['data'].get('subscription_type') == TokenManager.SUSCRIPTION_TYPE_MONTHLY:
                self.logger.debug('Monthly suscription. No payment needed.')
                return

            # get service owner user id form function name
            service_owner_name = data['data']['owner_name']
            if self.dotbot.owner_name == service_owner_name:
                self.logger.debug('Bot owner is at the same time the service owner. No payment needed.')
                return True

            try:
                self.token_manager.transfer(self.dotbot.owner_name, service_owner_name, data['data']['cost'])
            except TokenManagerInsufficientFundsException as e:
                self.insufficient_funds()

    def previous_checkings(self):
        """
        Some previous checks before payment
        """
        if not self.core.get_publisher_name():
            self.core.reset_output()
            self.core.bbot.text('This bot is not free. Please, set publisher token.') # @TODO ?
            raise BBotCoreHalt('Bot halted missing publisher token')    

        if self.dotbot.owner_name == self.core.get_publisher_name():
            self.logger.debug('Publisher is at the same time the bot owner. No need to do payment.')
            return False
        
        return True
        
    def insufficient_funds(self):
        """
        When there is insufficient funds we reset output, send error message and halt bot 
        """
        self.core.reset_output()
        self.core.bbot.text('Sorry, the bot is not available at this moment. Please try again later.') # @TODO chec environment to show different message
        raise BBotCoreHalt('Bot halted by insufficient funds')    

    def get_bot_volley_cost(self):
        if self.core.get_publisher_subscription_type() == TokenManager.SUSCRIPTION_TYPE_PER_USE:
            return self.dotbot.per_use_cost
        if self.core.get_publisher_subscription_type() == TokenManager.SUSCRIPTION_TYPE_PER_MONTH:
            return self.dotbot.per_month_cost
        return None
            
class TokenManagerInsufficientFundsException(Exception):
    """ """
