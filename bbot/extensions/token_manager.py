"""Token Manager"""
import logging
import codecs
import smokesignal
import datetime
import dateutil.relativedelta
from bbot.core import BBotCore, BBotCoreHalt, ChatbotEngine, BBotException, BBotLoggerAdapter, BBotExtensionException

class TokenManager():
    """Executes payments on a private development Ethereum parity node using personal module for seed token demo page"""

    SUBSCRIPTION_TYPE_FREE = 'free'
    SUBSCRIPTION_TYPE_PER_USE = 'perUse'
    SUBSCRIPTION_TYPE_MONTHLY = 'perMonth'

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
        self.greenhousedb = None

    def init(self, core: BBotCore):
        """
        :param bot:
        :return:
        """
        self.core = core
        self.logger = BBotLoggerAdapter(logging.getLogger('ext.token_mgnt'), self, self.core.bot, '$token')                

        smokesignal.on(BBotCore.SIGNAL_CALL_BBOT_FUNCTION_AFTER, self.function_payment)
        smokesignal.on(BBotCore.SIGNAL_GET_RESPONSE_AFTER, self.volley_payment)
        smokesignal.on(BBotCore.SIGNAL_GET_RESPONSE_BEFORE, self.payment_check)

    def payment_check(self, data):
        """
        Check before anything if the payment for the service is paid for current period
        """
        
        if self.core.get_publisher_subscription_type() == TokenManager.SUBSCRIPTION_TYPE_MONTHLY:
            self.logger.debug('Monthly suscription. Will check payment status')
            paid = self.check_period_payment_status(self.dotbot.botsubscription.id)
            if not paid:
                self.logger.debug('Publisher last payment is more than a month ago.')
                self.insufficient_funds()
        """
        Disabling this for now. We need to make tx async in order to stop wait for a response we dont need at the moment
        elif self.core.get_publisher_subscription_type() == TokenManager.SUBSCRIPTION_TYPE_PER_USE and self.dotbot.per_use_cost > 0:
            self.logger.debug('Per use suscription. Will check balance first')
            if not self.previous_checkings():
                return

            pbalance = self.token_manager.get_balance(self.core.get_publisher_name())
            if pbalance < self.minimum_accepted_balance:
                self.logger.debug('Publisher balance is less than ' + str(self.minimum_accepted_balance))                
                self.insufficient_funds()
        """        
    def check_period_payment_status(self, subscription_id):
        lastPaymentDate = self.greenhousedb.get_last_payment_date_by_subscription_id(subscription_id)
        if not lastPaymentDate:
            self.logger.debug('There is no payments')
            return False
        delta = (datetime.datetime.now() - lastPaymentDate).days
        self.logger.debug('Last payment date is ' + str(lastPaymentDate) + ' - days ago: ' + str(delta))
        if delta >= 30:
            return False
        return True
        
    def volley_payment(self, data):
        """
        Volley payment from publisher to bot owner
        """   

        if self.core.get_publisher_subscription_type() == TokenManager.SUBSCRIPTION_TYPE_FREE:
            self.logger.debug('Free suscription. No payment needed.')
            return
        if self.core.get_publisher_subscription_type() == TokenManager.SUBSCRIPTION_TYPE_MONTHLY:
            self.logger.debug('Monthly suscription. No volley payment needed.')
            return
        if self.core.get_publisher_subscription_type() == TokenManager.SUBSCRIPTION_TYPE_PER_USE:

            volley_cost = self.dotbot.per_use_cost

            if volley_cost is not None: # register bot volleys only if it has declared volley cost (can be 0)
                self.logger.debug('Paying volley activity')        
                if not self.previous_checkings():
                    return

                try:
                    self.token_manager.transfer(self.core.get_publisher_name(), self.dotbot.owner_name, volley_cost)
                except TokenManagerInsufficientFundsException as e:
                    self.insufficient_funds()

    def function_payment(self, data):
        """
        Function payment from bot owner to service owner
        """
        if data['register_enabled'] is True:
            self.logger.debug('Paying function activity: ' + str(data))        

            if data['data'].get('subscription_type') == TokenManager.SUBSCRIPTION_TYPE_FREE:
                self.logger.debug('Free suscription. No payment needed.')
                return
            elif data['data'].get('subscription_type') == TokenManager.SUBSCRIPTION_TYPE_MONTHLY:
                self.logger.debug('Monthly suscription. No payment needed.')
                return
            elif data['data'].get('subscription_type') == TokenManager.SUBSCRIPTION_TYPE_PER_USE:
                # get service owner user id form function name
                service_owner_name = data['data']['owner_name']
                if self.dotbot.owner_name == service_owner_name:
                    self.logger.debug('Bot owner is at the same time the service owner. No payment needed.')
                    return True

                try:
                    self.token_manager.transfer(self.dotbot.owner_name, service_owner_name, data['data']['cost'])
                except TokenManagerInsufficientFundsException as e:
                    self.insufficient_funds()
            else:
                self.logger.debug('No subscription type defined. Cancelling payment.')        

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
            
class TokenManagerInsufficientFundsException(Exception):
    """ """
