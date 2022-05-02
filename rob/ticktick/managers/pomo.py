import deal
class PomoManager:

    @deal.pure
    def __init__(self, client_class):
        self._client = client_class
        self.access_token = ''

    @deal.pure
    def start(self):
        pass

    @deal.pure
    def statistics(self):
        # https://api.ticktick.com/api/v2/statistics/general
        pass
