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

    @app.route('/channels/telegram/<bot_id>', methods=['POST'])
    def rest(bot_id):                                       # pylint: disable=W0612
        """
        Telegram webhook endpoint.
        """
        logger.debug(f'Received a Telegram webhook request for botid {bot_id}')

        try:
            params = request.get_json(force=True)
            org_id = 1

            # checks if bot is telegram enabled
            # if not, it delete the webhook and throw an exception
            enabled = webhook_check(bot_id)
            if enabled:
                dotbot = telegram.dotdb.find_dotbot_by_container_id(bot_id).dotbot
                token = dotbot['channels']['telegram']['token']
                telegram.set_api_token(token)

                user_id = telegram.get_user_id(params)
                telegram_recv = telegram.get_message(params)
                logger.debug('POST data from Telegram: ' + str(params))
                bbot_request = telegram.to_bbot_request(telegram_recv)

                bbot = BBotCore.create_bot(config, dotbot)
                logger.debug('User id: ' + user_id)
                req = bbot.create_request(bbot_request, user_id, bot_id, org_id)
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


    def webhook_check(bot_id):

        dotbot = telegram.dotdb.find_dotbot_by_container_id(bot_id).dotbot

        if dotbot['channels']['telegram']['enabled']:
            return True

        logger.warning(f'Deleting invalid Telegram webhook for botid {bot_id}')
        telegram.set_api_token(dotbot['channels']['telegram']['token'])
        delete_ret = telegram.api.deleteWebhook()
        if delete_ret:
            logger.warning("Successfully deleted.")
            return False
            #raise Exception('Received a telegram webhook request on a telegram disabled bot. The webhook was deleted now.')
        else:
            error = "Received a telegram webhook request on a telegram disabled bot and couldn't delete the invalid webhook"
            logger.error(error)
            raise Exception(error)


    return app

