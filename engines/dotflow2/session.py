"""Manage user sessions."""
import abc
from bbot.core import Plugin

@Plugin.register
class Session(Plugin, metaclass=abc.ABCMeta):
    """Abstract base class for data persistence."""

    @abc.abstractmethod
    def __init__(self, config: dict) -> None:
        """
        Initialize the instance.

        :param config: Configuration values for the instance.
        """
        super(Session, self).__init__(config)

    @abc.abstractmethod
    def reset_all(self, user_id: str) -> None:
        """
        Delete all data from a user.

        :param user_id: User ID
        """

    @abc.abstractmethod
    def get(self, user_id: str, key: str) -> str:
        """
        Retrieve a value from a user's session.

        :param user_id: User ID
        :param key: Key to retrieve
        """

    @abc.abstractmethod
    def set(self, user_id: str, key: str, value: str) -> None:
        """
        Set a value in a user's session.

        :param user_id: User ID
        :param key: Key to set
        :param value: Value to set
        """
