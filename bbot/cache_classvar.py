"""Cache for run-time persistance."""
from bbot.core import Cache

class CacheClassvar(Cache):
    """Cache."""

    def __init__(self, config: dict, dotbot: dict) -> None:
        """
        Initialize the plugin.

        """
        self.cache = {} # type: dict

        super().__init__(config)


    def set(self, key: str, val):
        """
        """
        super().set()
        self.cache[key] = val

    def get(self, key: str):
        """
        """
        super().get()
        return self.cache.get(key)

