import logging

class Restful:
    """"""
    def __init__(self, config: dict) -> None:
        """

        """
        self.config = config
        self.dotdb = None  #

        self.logger = logging.getLogger("channel_restful")

