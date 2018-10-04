"""MongoDB repository."""
import logging
import json
from typing import Any
from pymongo import MongoClient, DeleteMany
from flow.session import Session

class MongoDB(Session):
    """MongoDB session."""

    def __init__(self, config: dict) -> None:
        """Set up MongoDB."""
        super().__init__(config)
        uri = config["uri"]
        self.client = MongoClient(uri)
        parts = uri.split("/")
        last_part = parts.pop()
        parts = last_part.split("?")
        self.database_name = parts[0]
        self.user_data = self.client[self.database_name]["userData"]


    def reset_all(self, user_id: str) -> None:
        """
        Delete all data from a user.

        :param user_id: User ID
        """
        super().reset_all(user_id)        
        self.user_data.delete_many({'userId': user_id})


    def get(self, user_id: str, key: str) -> Any:
        """
        Retrieve a value from a user's session.

        :param user_id: User ID
        :param key: Key to retrieve
        """
        data = self.user_data.find_one({'userId': user_id})
        if data is None:
            return ""

        var_value = self.get_dot_notation(data, key)
        if var_value is None:
            return ""

        return var_value
        


    def set(self, user_id: str, key: str, value: str) -> None:
        """
        Set a value in a user's session.

        :param user_id: User ID
        :param key: Key to set
        :param value: Value to set
        """
        self.user_data.update_one({'userId': user_id}, {"$set":{key:value}},
                                  upsert=True)


    def set_var(self, user_id: str, key: str, value: any) -> None:
        """
        Set any user data for later use.

        :param user_id: User ID
        :param key: Key to set
        :param value: Value to set
        """
        key = 'userVars.' + key
        # value = json.dumps(value) << @TODO not needed? (it adds double quotes to the value)
        return self.set(user_id, key, value)

    def get_var(self, user_id: str, key=None) -> Any:
        """
        Retrieve any user data for later use.

        :param user_id: User ID
        :param key: Key to set        
        """
        final_key = "userVars"
        if key:
            final_key += "." + key
        return self.get(user_id, final_key)


    def get_dot_notation(self, d: dict, dotted_key: str) -> Any:
        """
        Allows to retrieve values from a dict using dot notation

        :param d: Dictionary
        :param keys: Regular key or key with dot notation
        """
        if "." in dotted_key:
            key, rest = dotted_key.split(".", 1)
            if d.get(key, None) is None:
                return None
            return self.get_dot_notation(d[key], rest)
        else:
            return d.get(dotted_key, None)
