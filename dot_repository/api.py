"""RESTful API."""
import os
from flask import Flask, request, jsonify, Response, g
from flask_restful import Resource, Api
from marshmallow import ValidationError

from bbot.config import load_configuration
from bbot.core import Plugin
from .models import AuthenticationError
from .schemas import CredentialsSchema, AuthSchema, DotBotContainerSchema, DotFlowContainerSchema

app = Flask(__name__)
config_path = os.path.abspath(os.path.dirname(__file__) + "/../instance")
config = load_configuration(config_path, "BBOT_ENV")
app.config.from_mapping(config)
dr_config = config["dot_repository"]
dotdb = Plugin.load_plugin(dr_config)
api = Api(app, prefix="/api")

def json_response(data: dict, status_code: int = 200) -> Response:
    """
    Sintax sugar to create a custom HTTP response.

    :param data: A dictionary to be serialized as a JSON string
    :status_code: HTTP status code. Defaults to 200.
    :return: Response
    """
    response = jsonify(data)
    response.status_code = status_code
    return response


def authentication_required(func):
    """Verify authentication token."""

    def wrapper(*args, **kwargs):
        user = dotdb.find_user_by_token(request.args.get('token', None))
        if not user:
            return json_response({'status': 'unauthorized'}, 401)
        g.user = user
        return func(*args, **kwargs)

    return wrapper

def get_fields_from_url():
    """Returns a list of fields defined in the url as expected by the RESTful standard"""
    return request.args.get('fields', '').split(",")

class Auth(Resource):
    """Authentication."""

    def get(self):
        """Verify credentials and retrieve an authentication token."""
        params = {'username': request.args.get('username', None),
                  'password': request.args.get('password', None)}
        try:
            _ = CredentialsSchema().load(params)
            auth_info = dotdb.login(params['username'], params['password'])
            schema = AuthSchema()
            return schema.dump(auth_info)
        except ValidationError as err:
            return json_response({'validation_errors': err.messages}, 400)
        except AuthenticationError:
            return json_response({'status': 'fail'}, 401)

    def delete(self):
        """Sign out a user by removing its authentication token."""
        dotdb.logout(request.args.get('username', None))
        return json_response({'status': 'success'})


class DotBot(Resource):
    """A DotBot."""

    @authentication_required
    def get(self, dotbot_idname: str = '') -> dict:
        """Get a DotBot by its ID."""
        if not dotbot_idname:
            return self.get_list()

        dotbot = dotdb.find_dotbot_by_idname(dotbot_idname)
        if not dotbot:
            return json_response({})
        schema = DotBotContainerSchema()
        return schema.dump(dotbot)

    @authentication_required
    def get_list(self) -> list:
        """Get all dotbots."""
        dotbots = dotdb.find_dotbots({'deleted': '0'})
        schema = DotBotContainerSchema(many=True)
        return schema.dump(dotbots)

    @authentication_required
    def post(self) -> dict:
        """Add a DotBot."""
        # check if id is already in use in the organization
        json_data = request.get_json()
        old_dotbot = dotdb.find_dotbot_by_idname(json_data['name'])
        if old_dotbot:
            return json_response({'error': 'Name already in use'}, 400)

        dotbot = dotdb.create_dotbot(json_data, g.user.organization)
        schema = DotBotContainerSchema()
        return schema.dump(dotbot)

    @authentication_required
    def put(self, dotbot_idname: str) -> dict:
        """Update a DotBot."""
        json_data = request.get_json()
        old_dotbot = dotdb.find_dotbot_by_idname(json_data['name'])
        if old_dotbot:
            return json_response({'error': 'Name already in use'}, 400)

        dotbot = dotdb.update_dotbot_by_idname(dotbot_idname, json_data)
        schema = DotBotContainerSchema()
        return schema.dump(dotbot)

    @authentication_required
    def delete(self, dotbot_idname: str) -> dict:
        """Delete a DotBot."""
        dotdb.delete_dotbot_by_idname(dotbot_idname)
        return json_response({})


class DotBotFormIdsList(Resource):
    """Lists all formId on all DotBot's flow"""

    @authentication_required
    def get(self, dotbot_id: str) -> list:
        return dotdb.find_dotflow_formids(dotbot_id)


class DotBotFieldIdsList(Resource):
    """Lists all fieldId on all DotBot's flow"""

    @authentication_required
    def get(self, dotbot_id: str) -> list:
        return dotdb.find_dotflow_fieldids(dotbot_id)


class DotFlow(Resource):
    """A dotflow."""

    @authentication_required
    def get(self, dotflow_idname: str = '', dotbot_idname: str = '') -> dict:
        """Get a dotflow by its ID."""
        if not dotflow_idname and dotbot_idname:
            return self.get_list(dotbot_idname)

        dotflow_container = dotdb.find_dotflow_by_idname(dotflow_idname)
        if not dotflow_container:
            return json_response({})
        schema = DotFlowContainerSchema()
        return schema.dump(dotflow_container)

    @authentication_required
    def get_list(self, dotbot_idname: str) -> list:
        """Get all dotflows in a dotbot."""
        dotbot_container = dotdb.find_dotbot_by_idname(dotbot_idname)
        if not dotbot_container:
            return json_response({'error': 'DotBot not found'}, 404)

        dotflows = dotdb.find_dotflows_by_dotbot_idname(dotbot_idname, fields=get_fields_from_url())
        schema = DotFlowContainerSchema(many=True)
        return schema.dump(dotflows)

    @authentication_required
    def post(self, dotbot_idname: str) -> dict:
        """Add a dotflow."""
        json_data = request.get_json()
        dotbot_container = dotdb.find_dotbot_by_idname(dotbot_idname)
        if not dotbot_container:
            return json_response({'error': 'DotBot not found'}, 404)

        dotflow = dotdb.create_dotflow(json_data, dotbot_container.dotbot)
        schema = DotFlowContainerSchema()
        return schema.dump(dotflow)

    def put(self, dotflow_idname: str, dotbot_idname: str = '') -> dict:
        """Update a dotflow."""
        json_data = request.get_json()
        dotflow = dotdb.update_dotflow_by_idname(dotflow_idname, json_data)
        schema = DotFlowContainerSchema()
        return schema.dump(dotflow)

    @authentication_required
    def delete(self, dotflow_idname: str) -> dict:
        """Delete a DotFlow."""
        dotdb.delete_dotflow_by_idname(dotflow_idname)
        return json_response({})


# Register all resources
api.add_resource(Auth, '/system/login/')
# @TODO bot name and flow name are not unique. we need to replace this with endpoints with ref with composite key organization/botname
api.add_resource(DotBot,
                 '/dotbots/',
                 '/dotbots/<string:dotbot_idname>')
api.add_resource(DotBotFormIdsList, '/dotbots/<string:dotbot_id>/formIds/')
api.add_resource(DotBotFieldIdsList, '/dotbots/<string:dotbot_id>/fieldIds/')
api.add_resource(DotFlow,
                 '/dotbots/<string:dotbot_idname>/dotflows/',
                 '/dotbots/<string:dotbot_idname>/dotflows/<string:dotflow_idname>',
                 '/dotflows/<string:dotflow_idname>')
