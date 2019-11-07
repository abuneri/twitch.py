import enum
from .tags import Tags, Badge, Color


class User:
    class Broadcaster(enum.Enum):
        """
        Represents the different broadcaster options that a user can be
        """
        NORMAL = 0  #:
        AFFILIATE = 1  #:
        PARTNER = 2  #:

    class Type(enum.Enum):
        """
        Represents the type of user
        """
        REGULAR = 0  #:
        GLOBAL_MOD = 1  #:
        ADMIN = 2  #:
        STAFF = 3  #:

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
        view_count = json.get('view_count')
        self._view_count = int(view_count) if view_count else None
        self._session = session
        # below are properties only set by tags
        self._color = None
        self._badges = None
        self._is_mod = None

    @property
    def broadcaster(self):
        """
        The user's broadcaster type

        :type: :class:`Broadcaster`
        """
        return self._broadcaster

    @property
    def description(self):
        """
        The user's channel description

        :type: :class:`str`
        """
        return self._description

    @property
    def display_name(self):
        """
        The user's current display name

        :type: :class:`str`
        """
        return self._display_name

    @property
    def email(self):
        """
        The user's email

        Returns ``None`` if the client's access token doesn't have the
        ``user:read:email`` scope.

        :type: :class:`str`
        """
        return self._email

    @property
    def id(self):
        """
        The user's ID

        :type: :class:`int`
        """
        return self._user_id

    @property
    def login(self):
        """
        The user's login name. This may not be the same as the display name.

        :type: :class:`str`
        """
        return self._login

    @property
    def offline_image_url(self):
        """
        Url to the user's offline channel image.

        :type: :class:`str`
        """
        return self._offline_image_url

    @property
    def image_url(self):
        """
        Url to the user's profile image.

        :type: :class:`str`
        """
        return self._profile_image_url

    @property
    def type(self):
        """
        The user's type

        :type: :class:`Type`
        """
        return self._user_type

    @property
    def view_count(self):
        """
        The users total number of views on their channel

        :type: :class:`int`
        """
        return self._view_count

    @property
    def color(self):
        """
        The user's color when in chat

        :type: :class:`Color`
        """
        return self._color

    @property
    def badges(self):
        """"""
        return self._badges

    @property
    def is_mod(self):
        """"""
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
        if mod:
            self._is_mod = int(mod) == 1

        # user id only set if its different than the current user id
        # (which it should never be, but this is just for completeness)
        user_id = tags_dict.get(Tags.USER_ID)
        if user_id:
            self._user_id == user_id if user_id != self.id else self.id

        # TODO: parse emote-sets. Only useful for making requests to the V5
        #  API which currently isn't supported

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
