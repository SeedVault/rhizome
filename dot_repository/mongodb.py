"""MongoDB adapter."""
import os
import datetime
from pymongo import MongoClient, ASCENDING
from bson.objectid import ObjectId
import bcrypt
from .models import User, Organization, DotBotContainer, DotBot, PublisherBot, Token, DotFlowContainer, AuthenticationError, RemoteAPI


class DotRepository():
    """MongoDB client."""

    def __init__(self, config: dict, dotbot: dict=None) -> None:
        """Initialize the connection."""

        self.connection_timeout = 5000

        if 'uri' not in config:
            raise RuntimeError("FATAL ERR: Missing config var uri")
        uri = config['uri']
        client = MongoClient(uri, serverSelectionTimeoutMS=self.connection_timeout)
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
        #self.mongo.dotbot.create_index('dotbot.name', unique=True)
        # Unique dotflow name by dotbot
        #self.mongo.dotflow.create_index([('name', ASCENDING),
        #                                 ('dotbot_id', ASCENDING)],
        #                               unique=True)

    @staticmethod
    def get_projection_from_fields(fields: list=[]):
        """Returns a mongodb projection based on a list of fieldnames in dot notation (note _id will be included always)"""
        return dict([field, 1] for field in fields if len(field) > 0) if len(fields[0]) else None


### ORGANIZATIONS (deprecated?)

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

### USERS/AUTH (deprecated?)

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


### DOTBOTCONTAINER

    def marshall_dotbot_container(self, result) -> DotBotContainer:
        """
        Marshall a dotbotcontainer.

        :param result: A mongodb document representing a dotbot.
        :return: DotBotContainer instance
        """
        dotbot_container = DotBotContainer()
        dotbot_container.dotbot = result['dotbot']
        dotbot_container.organization = self.find_one_organization({'_id': ObjectId(str(result['organizationId']))})
        dotbot_container.deleted = result['deleted']
        dotbot_container.createdAt = result['createdAt']
        dotbot_container.updatedAt = result['updatedAt']
        return dotbot_container

    def find_dotbot_containers(self, filters: dict) -> list:
        """
        Retrieve a list of dotbots.

        :param filters: Dictionary with matching conditions.
        :return: List of dotbots
        """
        results = self.mongo.dotbot.find(filters)
        dotbots = []
        for result in results:
            dotbots.append(self.marshall_dotbot_container(result))
        return dotbots

    def find_one_dotbot_container(self, filters: dict) -> DotBotContainer:
        """
        Retrieve a dotbotContainer by filters.

        :param filters: Dictionary with matching conditions.
        :return: DotBotContainer instance or None if not found.
        """
        
        result = self.mongo.dotbot.find_one(filters)
        
        if not result:
            return None
        return self.marshall_dotbot_container(result)

    def find_dotbot_container_by_container_id(self, container_id: str) -> DotBotContainer:
        """
        Retrieve a dotbot by its container ID.

        :param container_id: DotBot container ID
        :return: DotBotContainer instance or None if not found.
        """
        return self.find_one_dotbot_container({"_id": ObjectId(str(container_id))})

    def find_dotbot_container_by_idname(self, dotbot_idname: str) -> DotBotContainer:
        """
        Retrieve a dotbot by its id or name.

        :param dotbot_idname: DotBot id or name
        :return: DotBot instance or None if not found.
        """
        return self.find_one_dotbot_container({'$or': [{'dotbot.id': dotbot_idname}, {'dotbot.name': dotbot_idname}]})

    def find_dotbots_by_channel(self, channel: str) -> list:
        """
        Retrieve a dotbot list by its enabled channels

        :param channel: DotBot enabled channel
        :return: DotBot intance list
        """

        return self.find_dotbot_containers({'dotbot.channels.' + channel + '.enabled': True})

    def create_dotbot(self, dotbot: dict, organization: Organization) -> DotBotContainer:
        """
        Create a new DotBot.

        :param dotbot: DotBot data
        :param organization: A valid organization.
        :return: DotBot created.
        """
        oid = ObjectId()
        if not dotbot.get('id'):  # Insert oid on dotbot id if not set
            dotbot['id'] = str(oid)

        param = {
            '_id': oid,
            'dotbot': dotbot,
            'organizationId': organization.id,
            'deleted': '0',
            'createdAt': datetime.datetime.utcnow(),
            'updatedAt': datetime.datetime.utcnow()
        }
        self.mongo.dotbot.insert_one(param)
        return self.find_dotbot_container_by_container_id(oid)

    def update_dotbot_by_container_id(self, container_id: str, dotbot: dict) -> DotBotContainer:
        """
        Update a DotBot by its container id.

        :param container_id: DotBot container id
        :param dotbot: DotBotContainer object
        :return: Updated DotBot
        """
        self.mongo.dotbot.update_one({"_id": ObjectId(str(container_id))},
                                     {"$set": {
                                         "dotbot": dotbot,
                                         "updatedAt": datetime.datetime.utcnow()
                                     }})
        return self.find_dotbot_container_by_container_id(container_id)

    def update_dotbot_by_idname(self, dotbot_idname: str, dotbot: dict) -> DotBotContainer:
        """
        Update a DotBot by its id.

        :param dotbot_id: DotBot id
        :param dotbot: DotBot object
        :return: Updated DotBotContainer object
        """
        self.mongo.dotbot.update_one({'$or': [{'dotbot.id': dotbot_idname}, {'dotbot.name': dotbot_idname}]},
                                     {"$set": {
                                         "dotbot": dotbot,
                                         "updatedAt": datetime.datetime.utcnow()
                                     }})
        return self.find_dotbot_container_by_idname(dotbot_idname)

    def delete_dotbot_by_container_id(self, container_id: str) -> None:
        """
        Soft-delete a DotBot.

        :param container_id: DotBot container ID
        """
        self.mongo.dotbot.update_one({"_id": ObjectId(str(container_id))},
                                     {"$set": {"deleted": 1, "updatedAt": datetime.datetime.utcnow()}})

    def delete_dotbot_by_idname(self, dotbot_idname: str) -> None:
        """
        Soft-delete a DotBot.

        :param dotbot_idname: DotBot ID
        """
        self.mongo.dotbot.update_one({'$or': [{'dotbot.id': dotbot_idname}, {'dotbot.name': dotbot_idname}]},
                                     {"$set": {"deleted": 1, "updatedAt": datetime.datetime.utcnow()}})


    ### DOTBOT

    def marshall_dotbot(self, result) -> DotBot:
        """
        Marshall a dotbot.

        :param result: A mongodb document representing a dotbot.
        :return: DotBot instance
        """
        dotbot = DotBot()
        dotbot.owner_name = result['ownerName']
        dotbot.name = result['name']
        dotbot.bot_id = result['botId']
        dotbot.title = result['title']        
        dotbot.chatbot_engine = result['chatbotEngine']
        dotbot.per_use_cost = result['perUseCost']
        dotbot.per_month_cost = result['perMonthCost']
        dotbot.updated_at = result['updatedAt']
        return dotbot

    def find_one_dotbot(self, filters: dict) -> DotBot:
        """
        Retrieve a dotbot by filters.

        :param filters: Dictionary with matching conditions.
        :return: DotBot instance or None if not found.
        """       
        result = self.mongo.greenhouse_dotbots.find_one(filters)        
        if not result:
            return None
        return self.marshall_dotbot(result)

    def find_dotbots(self, filters: dict) -> list:
        """
        Retrieve a list of dotbots.

        :param filters: Dictionary with matching conditions.
        :return: List of dotbots
        """
        results = self.mongo.greenhouse_dotbots.find(filters)
        dotbots = []
        for result in results:
            dotbots.append(self.marshall_dotbot(result))
        return dotbots

    def find_dotbot_by_bot_id(self, bot_id: str) -> DotBot:
        return self.find_one_dotbot({'botId': bot_id})

    ### publisher_bot

    def find_publisherbot_by_publisher_token(self, pub_token: str):
        return self.find_one_publisherbot({'token': pub_token})

    def find_publisherbots_by_channel(self, channel: str) -> list:    
        field = 'channels.' + channel
        return self.find_publisherbots({field: {'$exists': True}})

    def find_one_publisherbot(self, filters: dict) -> PublisherBot:
        """
        Retrieve a publisherbot by filters.

        :param filters: Dictionary with matching conditions.
        :return: PublisherBot instance or None if not found.
        """    
        result = self.mongo.greenhouse_publisher_bots.find_one(filters)        
        if not result:
            return None
        return self.marshall_publisherbot(result)

    def find_publisherbots(self, filters: dict) -> list:                
        results = self.mongo.greenhouse_publisher_bots.find(filters)
        publisherbots = []
        for result in results:
            publisherbots.append(self.marshall_publisherbot(result))
        return publisherbots

    def marshall_publisherbot(self, result) -> PublisherBot:
        pub_bot = PublisherBot()
        pub_bot.id = result['subscriptionId']
        pub_bot.token = result['token']
        pub_bot.publisher_name = result['publisherName']
        pub_bot.bot_id = result['botId']
        pub_bot.bot_name = result['botName']
        pub_bot.subscription_type = result['subscriptionType']
        pub_bot.updated_at = result['updatedAt']
        pub_bot.channels = result['channels']
        pub_bot.services = result['services']
        return pub_bot

    ### DOTFLOWS

    def marshall_dotflow(self, result) -> DotFlowContainer:
        """
        Marshall a DotFlowContainer.

        :param result: A mongodb document representing a DotFlow.
        :return: DotFlow instance
        """
        dotflow_container = DotFlowContainer()
        if result.get('dotflow'): dotflow_container.dotflow = result['dotflow']
        if result.get('dotbotId'): dotflow_container.dotbot = self.find_dotbot_container_by_idname(result['dotbotId'])
        if result.get('createdAt'): dotflow_container.createdAt = result['createdAt']
        if result.get('updatedAt'): dotflow_container.updatedAt = result['updatedAt']
        return dotflow_container

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

    def find_one_dotflow(self, filters: dict) -> DotFlowContainer:
        """
        Retrieve a DotFlow by filters.

        :param filters: Dictionary with matching conditions.
        :return: DotFlow instance or None if not found.
        """
        result = self.mongo.dotflow.find_one(filters)
        if not result:
            return None
        return self.marshall_dotflow(result)

    def find_dotflow_by_container_id(self, container_id) -> DotFlowContainer:
        """
        Retrieve a dotflow by its ID.

        :param container_id: DotFlow ID
        :return: DotFlow instance or None if not found.
        """
        return self.find_one_dotflow({"_id": ObjectId(str(container_id))})

    def find_dotflow_by_idname(self, dotflow_idname) -> DotFlowContainer:
        """
        Retrieve a DotFlowContainer object by its ID or name.

        :param dotflow_idname: DotFlow ID or name
        :return: DotFlowContainer instance or None if not found.
        """
        return self.find_one_dotflow({'$or': [{'dotflow.id': dotflow_idname}, {'dotflow.name': dotflow_idname}]})

    def find_dotflow_by_node_id(self, dotbot_id: str, node_id: str) -> DotFlowContainer:
        """
        Retrieve a DotFlowContainer object containing the specified node id

        :param dotbot_id: DotBot ID
        :param node_id: Node ID
        :return: DotFlowContainer instance or None if not found.
        """
        return self.find_one_dotflow({'$and': [{'dotbotId': dotbot_id}, {'dotflow.nodes.id': node_id}]})

    def find_node_by_id(self, dotbot_id: str, node_id: str) -> dict:
        """
        Retrieve a node by its id.

        :param dotbot_id: DotBot ID.
        :param node_id: Node ID.
        :return:
        """
        dfc = self.find_dotflow_by_node_id(dotbot_id, node_id)
        if not dfc:
            return None

        for n in dfc.dotflow['nodes']:
            if n['id'] == node_id:
                return n

    def find_dotflows_by_dotbot_idname(self, dotbot_idname: str, fields: list=[]) -> list:
        """
        Retrieve a list of DotFlowContainer objects by DotBot id

        :param dotbot_idname: DotBot id
        :param fields: DotFlowContainer fields to project
        :return: List of DotFlowContainer objects
        """
        # we don't know if it's id or name. retrieve dotbot anyway to get id by id or name
        dotbot_container = self.find_dotbot_container_by_idname(dotbot_idname)

        query = {'dotbotId': dotbot_container.dotbot['id']}
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
                if context in n.get('context', []):
                    context_nodes.append(n)

        return context_nodes

    def create_dotflow(self, dotflow: dict, dotbot: dict) -> DotFlowContainer:
        """
        Create a new dotflow.

        :param name: Unique dotflow name in dotbot.
        :param flow: DotFlow code as a JSON string.
        :param dotbot: A valid dotbot.
        :return: DotFlow created.
        """
        oid = ObjectId()
        if not dotflow.get('id'):  # Insert oid on dotflow id if not set
            dotflow['id'] = str(oid)

        param = {
            '_id': oid,
            'dotflow': dotflow,
            'dotbotId': dotbot['id'],
            'createdAt': datetime.datetime.utcnow(),
            'updatedAt': datetime.datetime.utcnow()
        }
        self.mongo.dotflow.insert_one(param)
        return self.find_dotflow_by_container_id(oid)  #TODO maybe this should be done from the api?

    def update_dotflow_by_container_id(self, container_id: str, dotflow: dict) -> DotFlowContainer:
        """
        Update a dotflow.

        :param container_id: DotFlowContainer ID
        :param name: Unique dotflow name in dotbot.
        :return: DotFlow updated.
        """

        # check updatedAt for mid-air collisions

        self.mongo.dotflow.update_one({"_id": ObjectId(str(container_id))},
                                      {"$set": {"dotflow": dotflow,
                                                "updatedAt": datetime.datetime.utcnow()}})
        return self.find_dotflow_by_container_id(container_id)

    def update_dotflow_by_idname(self, dotflow_idname: str, dotflow: dict) -> DotFlowContainer:
        """
        Update a dotflow.

        :param dotflow_idname: DotFlow ID
        :param name: Unique dotflow name in dotbot.
        :return: DotFlow updated.
        """

        # check updatedAt for mid-air collisions

        self.mongo.dotflow.update_one({'$or': [{'dotflow.id': dotflow_idname}, {'dotflow.name': dotflow_idname}]},
                                      {"$set": {"dotflow": dotflow,
                                                "updatedAt": datetime.datetime.utcnow()}})
        return self.find_dotflow_by_idname(dotflow_idname)

    def delete_dotflow_by_container_id(self, container_id: str) -> None:
        """
        Delete a dotflow.

        :param container_id: DotFlowContainer ID
        """
        self.mongo.dotflow.delete_one({"_id": ObjectId(str(container_id))})

    def delete_dotflow_by_idname(self, dotflow_idname: str) -> None:
        """
        Delete a dotflow.

        :param dotflow_idname: DotFlow ID
        """
        self.mongo.dotflow.delete_one({'$or': [{'dotflow.id': dotflow_idname}, {'dotflow.name': dotflow_idname}]})

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

## REMOTE APIS

    def marshall_remote_api(self, result) -> RemoteAPI:
        """
        Marshall a RemoteAPI.

        :param result: A mongodb document representing a dotbot.
        :return: DotBot instance
        """
        rapi = RemoteAPI()
        rapi.name = result['name']
        rapi.category = result['category']
        rapi.function_name = result['function_name']
        rapi.url = result['url']
        rapi.method = result['method']
        rapi.headers = result.get('headers', {})
        rapi.predefined_vars = result.get('predefined_vars', {})
        rapi.mapped_vars = result.get('mapped_vars', [])
        rapi.cost = result['cost']
        return rapi


    def find_remote_api_by_id(self, remote_api_id) -> dict:
        """
        Retrieve a remote api doc
        
        """        
        if isinstance(remote_api_id, str):
            filter = {"_id": ObjectId(remote_api_id)}
        else:
            obj_ids = list(map(lambda x: ObjectId(x), remote_api_id))
            filter = {"_id": {"$in": obj_ids}}

        rapis = []        
        results = self.mongo.remote_apis.find(filter)                
        for result in results:            
            rapis.append(self.marshall_remote_api(result))
        return rapis

## WATSON ASSISTANT SESSION AND CONTEXT

    def get_watson_assistant_session(self, user_id: str):
        """
        Returns user session id and context 

        :param: user_id: A string with user id
        :return: A dict
        """
        r = self.mongo.watson_assistant_bot_data.find_one({'user_id': user_id})
        return r

    def set_watson_assistant_session(self, user_id: str, session_id: str, context: dict={}):
        """
        Stores user session id and context

        :param user_id: A string with user id
        :param session_id: A string with session id
        :param context: A dict with context
        """
        self.mongo.watson_assistant_bot_data.update({'user_id': user_id}, {'user_id': user_id, 'session_id': session_id, 'context': context}, upsert = True)
        

## GREENHOUSE SUBSCRIPTION_PAYMENTS

    def get_last_payment_date_by_subscription_id(self, subscription_id):
        res = self.mongo.subscription_payments.find_one({'subscriptionId': subscription_id})        
        if res:
            return res['lastPaymentDate']
        return None
