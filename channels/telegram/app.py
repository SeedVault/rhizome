"""Telegram channel."""
import logging
import logging.config
import os
import traceback
from flask import Flask, request, jsonify
from bbot.core import BBotCore, ChatbotEngine, Plugin
from bbot.config import load_configuration


def create_app():
    """Create and configure an instance of the application."""
    app = Flask(__name__)
    config_path = os.path.abspath(os.path.dirname(__file__) + "../../../instance")
    config = load_configuration(config_path, "BBOT_ENV")
    app.config.from_mapping(config)
    t_config = config["channel_telegram"]
    telegram = Plugin.load_plugin(t_config)
    logging.config.dictConfig(config['logging'])
    logger = logging.getLogger("channel_telegram")

    logger.debug("Listening Telegram from path: " + telegram.get_webhook_path())

    @app.route(telegram.get_webhook_path(), methods=['POST'])
    def rest(publisherbot_token):                                       # pylint: disable=W0612
        """
        Telegram webhook endpoint.
        """
        print('------------------------------------------------------------------------------------------------------------------------')
        logger.debug(f'Received a Telegram webhook request for publisher token {publisherbot_token}')

        try:
            params = request.get_json(force=True)
            org_id = 1

            # checks if bot is telegram enabled
            # if not, it delete the webhook and throw an exception
            enabled = webhook_check(publisherbot_token)
            if enabled:
                # get publisher user id from token
                pub_bot = telegram.dotdb.find_publisherbot_by_publisher_token(publisherbot_token)
                if not pub_bot:
                    raise Exception('Publisher not found')
                logger.debug('Found publisher: ' + pub_bot.publisher_name + ' - for bot id: ' + pub_bot.bot_id)
                pub_id = pub_bot.publisher_name
                
                # if 'runBot' in params:
                #    run_bot = telegram.params['runBot']
            
                dotbot = telegram.dotdb.find_dotbot_by_bot_id(pub_bot.bot_id)                    
                if not dotbot:
                    raise Exception('Bot not found')
                bot_id = dotbot.bot_id
                # build extended dotbot 
                dotbot.services = pub_bot.services
                dotbot.channels = pub_bot.channels
                dotbot.botsubscription = pub_bot
                
                token = pub_bot.channels['telegram']['token']
                telegram.set_api_token(token)

                user_id = telegram.get_user_id(params)
                telegram_recv = telegram.get_message(params)
                logger.debug('POST data from Telegram: ' + str(params))
                bbot_request = telegram.to_bbot_request(telegram_recv)

                bbot = BBotCore.create_bot(config, dotbot)
                logger.debug('User id: ' + user_id)
                req = bbot.create_request(bbot_request, user_id, bot_id, org_id, pub_id)                           
                bbot_response = bbot.get_response(req)
                
        except Exception as e:           
            logger.critical(str(e) + "\n" + str(traceback.format_exc()))            
            if config['environment'] == 'development':
                bbot_response = {
                    'output': [{'text': str(e)}],
                    'error': {'traceback': str(traceback.format_exc())}
                    }
            else:
                bbot_response = {'output': [{'text': 'An error happened. Please try again later.'}]}
                # @TODO this should be configured in dotbot
                # @TODO let bot engine decide what to do?

        telegram.send_response(bbot_response)

        # be sure to respond 200 code. telegram will keep sending it if doesnt get it
        return jsonify(success=True)


    def webhook_check(publisherbot_token):

        pb = telegram.dotdb.find_publisherbot_by_publisher_token(publisherbot_token)

        if pb.channels.get('telegram'):
            return True

        logger.warning(f'Deleting invalid Telegram webhook for publisher bot token: {publisherbot_token} - publisher id: ' + pb.publisher_name)
        telegram.set_api_token(pb.channels['telegram']['token'])
        delete_ret = telegram.api.deleteWebhook()
        if delete_ret:
            logger.warning("Successfully deleted.")
            return False
            #raise Exception('Received a telegram webhook request on a telegram disabled bot. The webhook was deleted now.')
        else:
            error = "Received a telegram webhook request on a telegram disabled bot and couldn't delete the invalid webhook"
            logger.error(error)
            raise Exception(error)

    @app.route('/ping')
    def test():                                     # pylint: disable=W0612
        logger.debug('Received ping request ')
        return "pong!\n"

    return app

