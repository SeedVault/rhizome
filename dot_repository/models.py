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
    """Represent a DotBotContainer object."""

    def __init__(self) -> None:
        """Initialize values."""
        self.dotbot = {}  # Actual dotbot data
        self.organization = Organization()  # Organization
        self.deleted = 0          # 1: Deleted, 0: Not deleted
        self.createdAt = datetime.datetime.utcnow()
        self.updatedAt = datetime.datetime.utcnow()

class DotBot():
    """Represent a DotBot container object."""

    def __init__(self) -> None:
        """Initialize values."""
        self.ownerName = ''
        self.bot_id = ''
        self.name = ''
        self.title = ''
        self.chatbot_engine = {}
        self.per_use_cost = 0
        self.per_month_cost = 0
        self.updated_at = None
        self.enabled_locales = []
        self.default_locale = ''
        self.tts_voice_id = None
        self.default_tts_voice_id = 0
        self.tts_time_scale = None
        self.default_tts_time_scale = 100

class PublisherBot():
    """Represent a PublisherBot container object."""

    def __init__(self) -> None:
        """Initialize values."""
        self.id = ''
        self.token = ''
        self.publisher_name = ''
        self.bot_id = ''
        self.bot_name = ''
        self.subscription_type = ''
        self.updated_at = None
        self.channels = {}
        self.services = []

class DotFlowContainer():
    """Represent a DotFlow container object."""

    def __init__(self) -> None:
        """Initialize values."""
        self.dotflow = {}  # Actual DotFlow data
        self.dotbot = DotBotContainer()  # DotBot
        self.createdAt = datetime.datetime.utcnow()
        self.updatedAt = datetime.datetime.utcnow()

class RemoteAPI():
    """Represent a RemoteAPI object."""

    def __init__(self) -> None:
        """Initialize values."""        
        self.name = ''
        self.category = None
        self.function_name = ''
        self.url = ''
        self.method = ''
        self.headers = []
        self.timeout = 0,
        self.user = '',
        self.passwd = '',        
        self.predefined_vars = []
        self.mapped_vars = []
