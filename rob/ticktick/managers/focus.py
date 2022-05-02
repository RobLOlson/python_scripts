import deal
class FocusTimeManager:

    @deal.pure
    def __init__(self, client_class):
        self._client = client_class
        self.access_token = ''

    #   ---------------------------------------------------------------------------------------------------------------
    #   Focus Timer Methods

    @deal.pure
    def start(self):
        """Starts the focus timer"""
        pass
