"""BBot Web Application."""

import os
import json
from flask import Flask, request, render_template
from bbot.core import create_bot, ChatbotEngine
from bbot.config import load_configuration

def create_app(test_config=None):
    """Create and configure an instance of the application."""
    app = Flask(__name__, instance_relative_config=True)
    config_path = os.path.abspath(os.path.dirname(__file__) \
    + "../../../instance")
    if test_config is not None:
        config_settings = load_configuration(config_path, "BBOT_ENV",
                                             "testing")
    else:
        config_settings = load_configuration(config_path, "BBOT_ENV")
    app.config.from_mapping(config_settings)


    @app.route('/Channels/RESTfulWebService', methods=['POST'])
    def rest():                                       # pylint: disable=W0612
        params = request.get_json(force=True)
        user_id = params['userId']
        bot_id = params['botId']
        org_id = params['orgId']
        input_params = params['input']
        # if 'runBot' in params:
        #    run_bot = params['runBot']
        bot = create_bot(config_settings)
        input_text = ""
        #for input_type, input_value in input_params.items():
            # bot.get_response(input_type, input_value)
        #    _ = input_type
        #    input_text = input_text + input_value
        req = ChatbotEngine.create_request(input_params, user_id, bot_id, org_id)
        res = bot.get_response(req)
        return json.dumps(res)


    @app.route('/TestWebChatBot')
    def test():                                     # pylint: disable=W0612
        return render_template('test.html')


    return app
