import enum
from .tags import Tags, Badge, Color


class User:
    class Broadcaster(enum.Enum):
        NORMAL = 0
        AFFILIATE = 1
        PARTNER = 2

    class Type(enum.Enum):
        REGULAR = 0
        GLOBAL_MOD = 1
        ADMIN = 2
        STAFF = 3

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
        self._badges = None
        self._is_mod = None

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

    @property
    def badges(self):
        return self._badges

    @property
    def is_mod(self):
        return self._is_mod

    def add_tags_data(self, tags_dict):
        if not tags_dict:
            return

        bad_info = tags_dict.get(Tags.BADGE_INFO)
        badges_str = tags_dict.get(Tags.BADGES)
        badges = [Badge(badge, bad_info) for badge in badges_str.split(',') if
                  badges_str]

        self._badges = badges

        # TODO: bits

        color = tags_dict.get(Tags.COLOR)
        if color:
            self._color = Color(color)

        # display name only set if its different than the current display name
        display_name = tags_dict.get(Tags.DISPLAY_NAME)
        if display_name:
            self._display_name = display_name if display_name \
                                                 != self.display_name else \
                                                 self.display_name

        mod = tags_dict.get(Tags.MOD)
        self._is_mod = mod == 1

        # user id only set if its different than the current user id
        # (which it should never be, but this is just for completeness)
        user_id = tags_dict.get(Tags.USER_ID)
        if user_id:
            self._user_id == user_id if user_id != self.id else self.id

    @staticmethod
    def _to_broadcaster(broadcaster_type):
        if broadcaster_type == 'partner':
            return User.Broadcaster.PARTNER
        elif broadcaster_type == 'affiliate':
            return User.Broadcaster.AFFILIATE
        else:
            return User.Broadcaster.NORMAL

    @staticmethod
    def _to_type(user_type):
        if user_type == 'staff':
            return User.Type.STAFF
        elif user_type == 'admin':
            return User.Type.ADMIN
        elif user_type == 'global_mod':
            return User.Type.GLOBAL_MOD
        else:
            return User.Type.REGULAR
