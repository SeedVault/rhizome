import logging

class Console:
    """"""
    def __init__(self, config: dict, dotbot: dict=None) -> None:
        """

        """
        self.config = config
        self.dotdb = None  #

        self.logger = logging.getLogger("channel_console")

