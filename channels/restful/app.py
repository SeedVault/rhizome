"""BBot Web Application."""

import sys, traceback
import os
import json
import logging
import logging.config

from flask_cors import CORS, cross_origin
from flask import Flask, request, render_template
from collections import defaultdict
from bbot.core import create_bot, ChatbotEngine, Plugin
from bbot.config import load_configuration


def create_app():
    """Create and configure an instance of the application."""
    app = Flask(__name__)
    CORS(app, support_credentials=True)

    config_path = os.path.abspath(os.path.dirname(__file__) + "../../../instance")
    config = load_configuration(config_path, "BBOT_ENV")
    app.config.from_mapping(config)
    w_config = config["channel_restful"]
    restful = Plugin.load_plugin(w_config)
    logging.config.dictConfig(config['logging'])
    logger = logging.getLogger("channel_restful")

    @app.route('/restful_channel', methods=['POST'])
    @cross_origin(supports_credentials=True)
    def rest():                                       # pylint: disable=W0612
        try:
            restful.params = request.get_json(force=True)
            logger.debug("Received request:" + str(restful.params))
            user_id = restful.params['userId']
            bot_id = restful.params['botId']
            org_id = restful.params['orgId']
            input_params = restful.params['input']
            
            # if 'runBot' in params:
            #    run_bot = restful.params['runBot']
            dotbotContainer = restful.dotdb.find_dotbot_by_container_id(bot_id)            
            if not dotbotContainer:
                raise Exception('Bot not found')
            restful.dotbot = dotbotContainer.dotbot # needed for methods below
            bot = create_bot(config, dotbotContainer.dotbot)
            input_text = ""
            #for input_type, input_value in input_params.items():
                # bot.get_response(input_type, input_value)
            #    _ = input_type
            #    input_text = input_text + input_value
            req = ChatbotEngine.create_request(input_params, user_id, bot_id, org_id)
            bot_response = bot.get_response(req)

            response = defaultdict(lambda: defaultdict(dict))    # create a response dict with autodict property
            for br in bot_response.keys():
                response[br] = bot_response[br]

            # html escape (@TODO change this when enabling bbot response textMD and textHTML)
            response['output'] = restful.escape_html_from_text(response['output'])
            logger.debug('Escaped response text: ' + str(response['output']))


        except Exception as e:
            response = {'error': {'message': str(e)}}
            #@TODO add config to enable/disable show exception errors on chatbot output
            #@TODO the whole error handling needs to be refactored. logs/exceptions/response object

        logger.debug("Response: " + str(response))
        return json.dumps(response)

    @app.route('/TestWebChatBot')
    def test():                                     # pylint: disable=W0612
        return render_template('test.html')


    return app
