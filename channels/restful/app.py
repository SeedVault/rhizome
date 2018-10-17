"""BBot Web Application."""

import os
import json
import logging
import logging.config
from flask import Flask, request, render_template
from bbot.core import create_bot, ChatbotEngine, Plugin
from bbot.config import load_configuration


def create_app():
    """Create and configure an instance of the application."""
    app = Flask(__name__)
    config_path = os.path.abspath(os.path.dirname(__file__) + "../../../instance")
    config = load_configuration(config_path, "BBOT_ENV")
    app.config.from_mapping(config)
    w_config = config["channel_restful"]
    restful = Plugin.load_plugin(w_config)
    logging.config.dictConfig(config['logging'])
    logger = logging.getLogger("channel_restful")

    @app.route('/Channels/RESTfulWebService', methods=['POST'])
    def rest():                                       # pylint: disable=W0612
        try:
            params = request.get_json(force=True)
            logger.debug("Received request:" + str(params))
            user_id = params['userId']
            bot_id = params['botId']
            org_id = params['orgId']
            input_params = params['input']
            # if 'runBot' in params:
            #    run_bot = params['runBot']
            dotbotContainer = restful.dotdb.find_dotbot_by_container_id(bot_id)
            if not dotbotContainer:
                raise Exception('Bot not found')
            bot = create_bot(config, dotbotContainer.dotbot)
            input_text = ""
            #for input_type, input_value in input_params.items():
                # bot.get_response(input_type, input_value)
            #    _ = input_type
            #    input_text = input_text + input_value
            req = ChatbotEngine.create_request(input_params, user_id, bot_id, org_id)
            response = bot.get_response(req)
        except Exception as e:
            response = {'error': {'message': str(e)}}

        logger.debug("Response: " + str(response))
        return json.dumps(response)


    @app.route('/TestWebChatBot')
    def test():                                     # pylint: disable=W0612
        return render_template('test.html')


    return app
