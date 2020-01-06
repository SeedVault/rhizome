"""RESTful channel"""

import os
import logging
from flask_cors import CORS, cross_origin
from flask import Flask, request, render_template, Response, jsonify
from collections import defaultdict

from bbot.core import Plugin
from bbot.config import load_configuration

"""Create and configure an instance of the application."""
app = Flask(__name__)
CORS(app)

config = load_configuration(os.path.abspath(os.path.dirname(__file__) + "../../../instance"), "BBOT_ENV")
app.config.from_mapping(config)
logging.config.dictConfig(config['logging'])

restful = Plugin.load_plugin(config['channel_restful'])
print("Listening RESTful from path: " + restful.get_endpoint_path())
telegram = Plugin.load_plugin(config['channel_telegram'])
print("Listening Telegram from path: " + telegram.get_webhook_path())

@app.route(restful.get_endpoint_path(), methods=['POST'])
@cross_origin(origins=restful.config['cors_origin'])
def restful_endpoint(): # pylint: disable=W0612    
    response = restful.endpoint(request)
    return Response(response['response'], status=response['status'], mimetype=response['mimetype'])

@app.route('/TestWebChatBot')
def test(): # pylint: disable=W0612
    return render_template('test.html')

@app.route(telegram.get_webhook_path(), methods=['POST'])
def telegram_endpoint(publisherbot_token):  # pylint: disable=W0612
    """
    Telegram webhook endpoint.
    """
    telegram.endpoint(request, publisherbot_token)
    # be sure to respond 200 code. telegram will keep sending it if doesnt get it
    return jsonify(success=True)
    
@app.route('/ping')
def ping(): # pylint: disable=W0612
    print('Received ping request')
    return "[BBOT RESTFUL SERVER] pong!\n"


