"""MongoDB adapter."""
import os
import datetime
from pymongo import MongoClient, ASCENDING
from bson.objectid import ObjectId
import bcrypt
from .models import User, Organization, DotBot, Token, DotFlow, AuthenticationError


class DotRepository():
    """MongoDB client."""

    def __init__(self, config: dict, dotbot: dict=None) -> None:
        """Initialize the connection."""
        if not 'uri' in config:
            raise RuntimeError("FATAL ERR: Missing config var uri")
        uri = config['uri']
        client = MongoClient(uri)
        parts = uri.split("/")
        last_part = parts.pop()
        parts = last_part.split("?")
        database_name = parts[0]
        self.mongo = client[database_name]

    def restart_from_scratch(self):
        """Drop and recreate each collection in database."""
        collections = ['organizations', 'users', 'dotbot', 'dotflow']
        collections_in_db = self.mongo.list_collection_names()
        for collection_name in collections:
            if collection_name in collections_in_db:
                self.mongo.drop_collection(collection_name)
            self.mongo.create_collection(collection_name)
        # Unique organization name
        self.mongo.organizations.create_index('name', unique=True)
        # Unique username and token
        self.mongo.users.create_index('username', unique=True)
        self.mongo.users.create_index('token', unique=True)
        # Unique dotbot name
        self.mongo.dotbot.create_index('name', unique=True)
        # Unique dotflow name by dotbot
        self.mongo.dotflow.create_index([('name', ASCENDING),
                                         ('dotbot_id', ASCENDING)],
                                        unique=True)

    @staticmethod
    def get_projection_from_fields(fields: list=[]):
        """Returns a mongodb projection based on a list of fieldnames in dot notation (note _id will be included always)"""
        return dict([field, 1] for field in fields if len(field) > 0) if len(fields[0]) else None


    def create_organization(self, name: str) -> Organization:
        """
        Create a new organization.

        :param name: Unique organization name.
        :return: The organization created.
        """
        params = {
            'name': name
        }
        organization_id = self.mongo.organizations.insert_one(params).inserted_id
        result = self.mongo.organizations.find_one({"_id": ObjectId(str(organization_id))})
        organization = Organization()
        organization.id = str(organization_id)
        organization.name = result['name']
        return organization

    def find_one_organization(self, filters: dict) -> Organization:
        """
        Retrieve an organization by filters.

        :param filters: Dictionary with matching conditions.
        :return: Organization instance or None if not found.
        """
        result = self.mongo.organizations.find_one(filters)
        if not result:
            return None
        organization = Organization()
        organization.id = str(result['_id'])
        organization.name = result['name']
        return organization

    def find_one_user(self, filters: dict) -> User:
        """
        Retrieve a user by filters.

        :param filters: Dictionary with matching conditions.
        :return: User instance or None if not found.
        """
        result = self.mongo.users.find_one(filters)
        if not result:
            return None
        user = User()
        user.id = str(result['_id'])
        user.username = result['username']
        user.hashed_password = result['hashed_password']
        organization_id = ObjectId(str(result['organization_id']))
        user.organization = self.find_one_organization({'_id': organization_id})
        return user

    def create_user(self, username: str, plaintext_password: str,
                    organization: Organization, is_admin: int) -> User:
        """
        Create a new user.

        :param username: Unique username.
        :param plaintext_password: Password in plain text that won't be stored.
        :param organization: A valid organization.
        :param is_admin: If the user has administrative privileges: 1.
                         Default: 0.
        :return: User created.
        """
        param = {
            'username': username,
            'hashed_password': bcrypt.hashpw(plaintext_password,  # pylint: disable=no-member
                                             bcrypt.gensalt()),
            'organization_id': organization.id,
            'is_admin': is_admin,
            'token': '',
            'created_at': datetime.datetime.utcnow(),
            'updated_at': datetime.datetime.utcnow()
        }
        user_id = self.mongo.users.insert_one(param).inserted_id
        return self.find_one_user({"_id": ObjectId(str(user_id))})

    def login(self, username: str, plaintext_password: str) -> Token:
        """
        Try to authenticate a user.

        :param username: Unique username.
        :param plaintext_password: Password.
        :raise AuthenticationError: on failure.
        :return: Authentication token.
        """
        token = Token()
        user = self.find_one_user({"username": username})
        if user:
            if bcrypt.checkpw(plaintext_password,  # pylint: disable=no-member
                              user.hashed_password):
                token.status = 'success'
                token.token = os.urandom(24).hex()
                self.mongo.users.update_one({"username": username},
                                            {"$set": {"token": token.token,
                                                      'updated_at': datetime.datetime.utcnow()}})
        if token.status != 'success':
            raise AuthenticationError()
        return token

    def logout(self, username: str) -> None:
        """
        Remove the authentication token from a user.

        :param username: A valid username
        :return: None
        """
        self.mongo.users.update_one({"username": username},
                                    {"$set": {"token": "", "updated_at": \
                                        datetime.datetime.utcnow()}})

    def find_user_by_token(self, token: str) -> User:
        """
        Retrieve a user by its authentication token.

        :param token: A valid authentication token.
        :return: User related to token.
        """
        return self.find_one_user({"token": token})

    def find_dotbots(self, filters: dict) -> list:
        """
        Retrieve a list of dotbots.

        :param filters: Dictionary with matching conditions.
        :return: List of dotbots
        """
        results = self.mongo.dotbot.find(filters)
        dotbots = []
        for result in results:
            dotbots.append(self.marshall_dotbot(result))
        return dotbots

    def marshall_dotbot(self, result) -> DotBot:
        """
        Marshall a dotbot.

        :param result: A mongodb document representing a dotbot.
        :return: DotBot instance
        """
        dotbot = DotBot()
        dotbot.id = str(result['_id'])
        dotbot.organization = self.find_one_organization({'_id': ObjectId(str(result['organizationId']))})
        dotbot.deleted = result['deleted']
        dotbot.createdAt = result['createdAt']
        dotbot.updatedAt = result['updatedAt']
        dotbot.dotbot = result['dotbot']
        return dotbot

    def find_one_dotbot(self, filters: dict) -> DotBot:
        """
        Retrieve a dotbot by filters.

        :param filters: Dictionary with matching conditions.
        :return: DotBot instance or None if not found.
        """
        result = self.mongo.dotbot.find_one(filters)
        if not result:
            return None
        return self.marshall_dotbot(result)

    def find_dotbot_by_id(self, dotbot_id: str) -> DotBot:
        """
        Retrieve a dotbot by its ID.

        :param dotbot_id: DotBot ID
        :return: DotBot instance or None if not found.
        """
        return self.find_one_dotbot({"_id": ObjectId(str(dotbot_id))})

    def find_dotbot_by_name(self, name: str) -> DotBot:
        """
        Retrieve a dotbot by its name.

        :param name: DotBot name
        :return: DotBot instance or None if not found.
        """
        return self.find_one_dotbot({'dotbot.name': name})

    def find_dotbots_by_channel(self, channel: str) -> list:
        """
        Retrieve a dotbot list by its enabled channels

        :param channel: DotBot enabled channel
        :return: DotBot intance list
        """

        return self.find_dotbots({'dotbot.channels.' + channel + '.enabled': True})


    def create_dotbot(self, dotbot: dict, organization: Organization) -> DotBot:
        """
        Create a new DotBot.

        :param dotbot: DotBot data
        :param organization: A valid organization.
        :return: DotBot created.
        """
        param = {
            'dotbot': dotbot['dotbot'],
            'organizationId': organization.id,
            'deleted': '0',
            'createdAt': datetime.datetime.utcnow(),
            'updatedAt': datetime.datetime.utcnow()
        }
        dotbot_id = self.mongo.dotbot.insert_one(param).inserted_id
        return self.find_one_dotbot({"_id": ObjectId(str(dotbot_id))})

    def update_dotbot(self, dotbot_id: str, dotbot: dict) -> DotBot:
        """
        Update a DotBot.

        :param dotbot: DotBot
        :return: DotBot updated.
        """
        self.mongo.dotbot.update_one({"_id": ObjectId(str(dotbot_id))},
                                     {"$set": {
                                         "dotbot": dotbot['dotbot'],
                                         "updatedAt": datetime.datetime.utcnow()
                                     }})
        return self.find_one_dotbot({"_id": ObjectId(str(dotbot_id))})

    def delete_dotbot(self, dotbot_id: str) -> None:
        """
        Soft-delete a DotBot.

        :param dotbot_id: DotBot ID
        """
        self.mongo.dotbot.update_one({"_id": ObjectId(str(dotbot_id))},
                                     {"$set": {"deleted": 1, "updatedAt": datetime.datetime.utcnow()}})



    ### DOTFLOWS

    def find_dotflows(self, filters: dict, projection: dict=None) -> list:
        """
        Retrieve a list of DotFlows.

        :param filters: Dictionary with matching conditions.
        :param projection: Dictionary with projection setting.
        :return: List of dotflows.
        """

        results = self.mongo.dotflow.find(filters, projection)
        dotflows = []
        for result in results:
            dotflows.append(self.marshall_dotflow(result))
        return dotflows

    def marshall_dotflow(self, result) -> DotFlow:
        """
        Marshall a DotFlow.

        :param result: A mongodb document representing a DotFlow.
        :return: DotFlow instance
        """
        dotflow = DotFlow()
        dotflow.id = str(result.get('_id'))
        dotflow.dotflow = result.get('dotflow')
        dotflow.createdAt = result.get('createdAt')
        dotflow.updatedAt = result.get('updatedAt')
        if result.get('dotbotId'): dotflow.dotbot = self.find_one_dotbot({'_id': ObjectId(str(result['dotbotId']))})
        return dotflow

    def find_one_dotflow(self, filters: dict) -> DotFlow:
        """
        Retrieve a DotFlow by filters.

        :param filters: Dictionary with matching conditions.
        :return: DotFlow instance or None if not found.
        """
        result = self.mongo.dotflow.find_one(filters)
        if not result:
            return None
        return self.marshall_dotflow(result)

    def find_dotflow_by_id(self, dotflow_id) -> DotFlow:
        """
        Retrieve a dotflow by its ID.

        :param dotflow_id: DotFlow ID
        :return: DotFlow instance or None if not found.
        """
        return self.find_one_dotflow({"_id": ObjectId(str(dotflow_id))})

    def find_dotflow_by_name(self, name) -> DotFlow:
        """
        Retrieve a dotflow by its name.

        :param name: DotFlow Name
        :return: DotFlow instance or None if not found.
        """
        return self.find_one_dotflow({'dotbot.name': name})

    def find_dotflows_by_dotbot_id(self, dotbot_id: str, fields: list=[]):
        query = {'dotbotId': dotbot_id}
        projection = DotRepository.get_projection_from_fields(fields)
        return self.find_dotflows(query, projection)

    def find_dotflows_by_context(self, dotbot_id: str, context: str) -> list:
        """
        Retrieve a list of DotFlow2 tagged with the specified context

        :param dotbot_id: DotBot ID
        :param context: Context
        :return: List of DotFlow2 objects
        """
        # Get flows with nodes with the wanted context
        query = {"$and": [{"dotbotId": dotbot_id}, {"dotflow.nodes": {"$elemMatch": {"context": context}}}]}
        projection = {"dotflow.nodes": 1}
        dotflows = self.find_dotflows(query, projection)

        # Get nodes with the context
        context_nodes = []
        for df in dotflows:
            for n in df.dotflow['nodes']:
                if context in n['context']:
                    context_nodes.append(n)

        print(context_nodes)
        return context_nodes

    def create_dotflow(self, dotflow: dict, dotbot: DotBot) -> DotFlow:
        """
        Create a new dotflow.

        :param name: Unique dotflow name in dotbot.
        :param flow: DotFlow code as a JSON string.
        :param dotbot: A valid dotbot.
        :return: DotFlow created.
        """
        param = {
            'dotflow': dotflow['dotflow'],
            'dotbotId': dotbot.id,
            'createdAt': datetime.datetime.utcnow(),
            'updatedAt': datetime.datetime.utcnow()
        }
        dotflow_id = self.mongo.dotflow.insert_one(param).inserted_id
        return self.find_one_dotflow({"_id": ObjectId(str(dotflow_id))})

    def update_dotflow(self, dotflow_id: str, dotflow: dict) -> DotFlow:
        """
        Update a dotflow.

        :param dotflow_id: DotFlow ID
        :param name: Unique dotflow name in dotbot.
        :return: DotFlow updated.
        """

        # check updatedAt for mid-air collisions

        self.mongo.dotflow.update_one({"_id": ObjectId(str(dotflow_id))},
                                      {"$set": {"dotflow": dotflow['dotflow'],
                                                "updatedAt": datetime.datetime.utcnow()}})
        return self.find_one_dotflow({"_id": ObjectId(str(dotflow_id))})

    def delete_dotflow(self, dotflow_id: str) -> None:
        """
        Delete a dotflow.

        :param dotflow_id: DotFlow ID
        """
        self.mongo.dotflow.delete_one({"_id": ObjectId(str(dotflow_id))})

    def find_dotflow_formids(self, dotbot_id: str) -> list:
        """
        Retrieve a list of form-ids used in the dotbot's dotflows

        :param dotbot_id
        :return: list if forms ids
        """
        dotflows = self.mongo.dotflow.find({"$and": [{"flow.nodes.formId": {"$exists": True}}, {"_id": dotbot_id}]})
        nodes = []
        for f in dotflows:
            nodes += f['dotflow']['nodes']
        formids = set()
        for n in nodes:
            if n.get('formId'):
                formids.add(n['formId'])
        return list(formids)

    def find_dotflow_fieldids(self, dotbot_id: str) -> list:
        """
        Retrieve a list of field-ids used in the dotbo's dotflows

        :param dotbot_id
        :return: list of field-ids
        """
        dotflows = self.mongo.dotflow.find({"$and": [{"dotflow.nodes.fieldId": {"$exists": True}}, {"_id": dotbot_id}]})
        nodes = []
        for f in dotflows:
            nodes += f['dotflow']['nodes']
        fieldids = set()
        for n in nodes:
            if n.get('fieldId'):
                fieldids.add(n['fieldId'])
        return list(fieldids)
