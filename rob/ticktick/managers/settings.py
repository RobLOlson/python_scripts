import deal
class SettingsManager:

    @deal.pure
    def __init__(self, client_class):
        self._client = client_class
        self.access_token = ''

    @deal.pure
    def get_templates(self):
        # https://api.ticktick.com/api/v2/templates
        pass

    @deal.pure
    def get_user_settings(self):
        # https://api.ticktick.com/api/v2/user/preferences/settings?includeWeb=true
        pass
