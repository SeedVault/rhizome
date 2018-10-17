"""Models."""
import datetime

class Organization():
    """Represent an organization."""

    def __init__(self) -> None:
        """Initialize values."""
        self.id = ''
        self.name = '' # Unique organization name


class User():
    """Represent a user."""

    def __init__(self) -> None:
        """Initialize values."""
        self.id = ''
        self.username = ''        # Unique username
        self.hashed_password = '' # Password in plain text that won't be stored.
        self.organization = Organization()  # Organization
        self.is_admin = 0         # 1: Admin, 0: Regular user
        self.token = ''           # Authentication token
        self.created_at = datetime.datetime.utcnow()
        self.updated_at = datetime.datetime.utcnow()


class Token():
    """Represent an authentication token."""

    def __init__(self) -> None:
        """Initialize values."""
        self.status = ''
        self.token = ''

class AuthenticationError(Exception):
    """Authentication error."""


class DotBotContainer():
    """Represent a DotBot container object."""

    def __init__(self) -> None:
        """Initialize values."""
        self.dotbot = {}  # Actual dotbot data
        self.organization = Organization()  # Organization
        self.deleted = 0          # 1: Deleted, 0: Not deleted
        self.createdAt = datetime.datetime.utcnow()
        self.updatedAt = datetime.datetime.utcnow()


class DotFlowContainer():
    """Represent a DotFlow container object."""

    def __init__(self) -> None:
        """Initialize values."""
        self.dotflow = {}  # Actual DotFlow data
        self.dotbot = DotBotContainer()  # DotBot
        self.createdAt = datetime.datetime.utcnow()
        self.updatedAt = datetime.datetime.utcnow()
