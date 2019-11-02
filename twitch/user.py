import enum


class Broadcaster(enum.Enum):
    NONE = 0
    AFFILIATE = 1
    PARTNER = 2


class UserType(enum.Enum):
    REGULAR = 0
    GLOBAL_MOD = 1
    ADMIN = 2
    STAFF = 3


class User:
    def __init__(self, json, *, session):
        self.broadcaster = User._to_broadcaster(json.get('broadcaster_type'))
        self.description = json.get('description')
        self.display_name = json.get('display_name')
        self.email = json.get('email')
        user_id = json.get('id')
        self.user_id = int(user_id) if user_id else None
        self.login = json.get('login')
        self.offline_image_url = json.get('offline_image_url')
        self.profile_image_url = json.get('profile_image_url')
        self.user_type = User._to_type(json.get('type'))
        self.view_count = json.get('view_count')
        self._session = session

    @staticmethod
    def _to_broadcaster(broadcaster_type):
        if broadcaster_type == 'partner':
            return Broadcaster.PARTNER
        elif broadcaster_type == 'affiliate':
            return Broadcaster.AFFILIATE
        else:
            return Broadcaster.NONE

    @staticmethod
    def _to_type(user_type):
        if user_type == 'staff':
            return UserType.STAFF
        elif user_type == 'admin':
            return UserType.ADMIN
        elif user_type == 'global_mod':
            return UserType.GLOBAL_MOD
        else:
            return UserType.REGULAR
