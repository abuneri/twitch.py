import enum
from .tags import Tags
from .color import Color


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
        self._broadcaster = User._to_broadcaster(json.get('broadcaster_type'))
        self._description = json.get('description')
        self._display_name = json.get('display_name')
        self._email = json.get('email')
        user_id = json.get('id')
        self._user_id = int(user_id) if user_id else None
        self._login = json.get('login')
        self._offline_image_url = json.get('offline_image_url')
        self._profile_image_url = json.get('profile_image_url')
        self._user_type = User._to_type(json.get('type'))
        self._view_count = json.get('view_count')
        self._session = session
        # below are properties only set by tags
        self._color = None

    @property
    def broadcaster(self):
        return self._broadcaster

    @property
    def description(self):
        return self._description

    @property
    def display_name(self):
        return self._display_name

    @property
    def email(self):
        return self._email

    @property
    def id(self):
        return self._user_id

    @property
    def login(self):
        return self._login

    @property
    def offline_image_url(self):
        return self._offline_image_url

    @property
    def image_url(self):
        return self._profile_image_url

    @property
    def type(self):
        return self._user_type

    @property
    def view_count(self):
        return self._view_count

    @property
    def color(self):
        return self._color

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

    @classmethod
    def parse_tags(cls, user, tags_dict):
        color = tags_dict.get(Tags.COLOR)
        if color:
            user._color = Color(color)
