
class Tags:
    BADGE_INFO = 'badge-info'
    BADGES = 'badges'
    BAN_DURATION = 'ban-duration'
    BITS = 'bits'
    COLOR = 'color'
    DISPLAY_NAME = 'display-name'
    EMOTE_SETS = 'emote-sets'
    EMOTE_ONLY = 'emote-only'
    EMOTES = 'emotes'
    FOLLOWERS_ONLY = 'followers-only'
    ID = 'id'
    LOGIN = 'login'
    MESSAGE = 'message'
    MOD = 'mod'
    R9K = 'r9k'
    ROOM_ID = 'room-id'
    SLOW = 'slow'
    SUBS_ONLY = 'subs-only'
    SYSTEM_MSG = 'system-msg'
    TMI_SENT_TS = 'tmi-sent-ts'
    USER_ID = 'user-id'


class Color:
    def __init__(self, hex_rgb):
        self._red = None
        self._green = None
        self._blue = None
        self._hex = hex_rgb
        hex_rgb = hex_rgb.lstrip('#') if hex_rgb.startswith('#') else hex_rgb

        hex_parts = list(hex_rgb)
        parts_itr = iter(hex_parts)
        hex_components = [hex + next(parts_itr) for hex in parts_itr]
        if len(hex_components) != 3:
            raise ValueError(f'invalid hexadecimal color code {hex_rgb}')
        self._red = int(hex_components[0], 16)
        self._green = int(hex_components[1], 16)
        self._blue = int(hex_components[2], 16)

    @property
    def red(self):
        return self._red

    @property
    def green(self):
        return self._green

    @property
    def blue(self):
        return self._blue

    @property
    def hex(self):
        return self._hex


class MsgParamTags:
    CUMULATIVE_MONTHS = 'msg-param-cumulative-months'
    DISPLAY_NAME = 'msg-param-displayName'
    LOGIN = 'msg-param-login'
    MONTHS = 'msg-param-months'
    PROMO_GIFT_TOTAL = 'msg-param-promo-gift-total'
    PROMO_NAME = 'msg-param-promo-name'
    RECIPIENT_DISPLAY_NAME = 'msg-param-recipient-display-name'
    RECIPIENT_ID = 'msg-param-recipient-id'
    RECIPIENT_USERNAME = 'msg-param-recipient-user-name'
    SENDER_LOGIN = 'msg-param-sender-login'
    SENDER_NAME = 'msg-param-sender-name'
    SHOULD_SHARE_STREAK = 'msg-param-should-share-streak'
    STREAK_MONTHS = 'msg-param-streak-months'
    SUB_PLAN = 'msg-param-sub-plan'
    SUB_PLAN_NAME = 'msg-param-sub-plan-name'
    VIEWER_COUNT = 'msg-param-viewerCount'
    RITUAL_NAME = 'msg-param-ritual-name'
    THRESHOLD = 'msg-param-threshold'


# TODO: for these guys, it'd probably be best to just emit this constant, then
# expose a method for the user to be able to 'get notice message from tag id'
# also emit a user object if possible or any other models depending on the msg.
# Might be more robust to just have these guys essentially as 'reserved' events
# Will be much easier design-wise if the models they return end up being
# being different. And leaves less work for the user :)
class MsgIdTags:
    ALREADY_BANNED = 'already_banned'
    ALREADY_EMOTE_ONLY_OFF = 'already_emote_only_off'
    ALREADY_EMOTE_ONLY_ON = 'already_emote_only_on'
    ALREADY_R9K_OFF = 'already_r9k_off'
    ALREADY_R9K_ON = 'already_r9k_on'
    ALREADY_SUBS_OFF = 'already_subs_off'
    ALREADY_SUBS_ON = 'already_subs_on'
    BAD_BAN_ADMIN = 'bad_ban_admin'
    BAD_BAN_ANON = 'bad_ban_anon'
    BAD_BAN_BROADCASTER = 'bad_ban_broadcaster'
    BAD_BAN_GLOBAL_MOD = 'bad_ban_global_mod'
    BAN_BAN_MOD = 'bad_ban_mod'
    BAD_BAN_SELF = 'bad_ban_self'
    BAD_BAN_STAFF = 'bad_ban_staff'
    BAD_COMMERCIAL_ERROR = 'bad_commercial_error'
    BAD_DELETE_MESSAGE_BROADCASTER = 'bad_delete_message_broadcaster'
    BAD_DELETE_MESSAGE_MOD = 'bad_delete_message_mod'
    BAD_HOST_ERROR = 'bad_host_error'
    BAD_HOST_HOSTING = 'bad_host_hosting'
    BAD_HOST_RATE_EXCEEDED = 'bad_host_rate_exceeded'
    BAD_HOST_REJECTED = 'bad_host_rejected'
    BAD_HOST_SELF = 'bad_host_self'
    BAD_MARKER_CLIENT = 'bad_marker_client'
    BAD_MOD_BANNED = 'bad_mod_banned'
    BAD_MOD_MOD = 'bad_mod_mod'
    BAD_SLOW_DURATION = 'bad_slow_duration'
    BAD_TIMEOUT_ADMIN = 'bad_timeout_admin'
    BAD_TIMEOUT_ANON = 'bad_timeout_anon'
    BAD_TIMEOUT_BROADCASTER = 'bad_timeout_broadcaster'
    BAD_TIMEOUT_DURATION = 'bad_timeout_duration'
    BAD_TIMEOUT_GLOBAL_MOD = 'bad_timeout_global_mod'
    BAD_TIMEOUT_MOD = 'bad_timeout_mod'
    BAD_TIMEOUT_SELF = 'bad_timeout_self'
    BAD_TIMEOUT_STAFF = 'bad_timeout_staff'
    BAD_UNBAN_NO_BAN = 'bad_unban_no_ban'
    BAD_UNHOST_ERROR = 'bad_unhost_error'
    BAD_UNHOST_MOD = 'bad_unmod_mod'
    BAN_SUCCESS = 'ban_success'
    CMDS_AVAILABLE = 'cmds_available'
    COLOR_CHANGED = 'color_changed'
    COMMERCIAL_SUCCESS = 'commercial_success'
    DELETE_MESSAGE_SUCCESS = 'delete_message_success'
    EMOTE_ONLY_OFF = 'emote_only_off'
    EMOTE_ONLY_ON = 'emote_only_on'
    FOLLOWERS_OFF = 'followers_off'
    FOLLOWERS_ON = 'followers_on'
    FOLLOWERS_ONZERO = 'followers_onzero'
    HOST_OFF = 'host_off'
    HOST_ON = 'host_on'
    HOST_SUCCESS = 'host_success'
    HOST_SUCCESS_VIEWERS = 'host_success_viewers'
    HOST_TARGET_WENT_OFFLINE = 'host_target_went_offline'
    HOSTS_REMAINING = 'hosts_remaining'
    INVALID_USER = 'invalid_user'
    MOD_SUCCESS = 'mod_success'
    MSG_BANNED = 'msg_banned'
    MSG_BAD_CHARACTERS = 'msg_bad_characters'
    MSG_CHANNEL_BLOCKED = 'msg_channel_blocked'
    MSG_CHANNEL_SUSPENDED = 'msg_channel_suspended'
    MSG_DUPLICATE = 'msg_duplicate'
    MSG_EMOTEONLY = 'msg_emoteonly'
    MSG_FACEBOOK = 'msg_facebook'
    MSG_FOLLOWERSONLY = 'msg_followersonly'
    MSG_FOLLOWERSONLY_FOLLOWED = 'msg_followersonly_followed'
    MSG_FOLLOWERSONLY_ZERO = 'msg_followersonly_zero'
    MSG_R9K = 'msg_r9k'
    MSG_RATELIMIT = 'msg_ratelimit'
    MSG_REJECTED = 'msg_rejected'
    MSG_REJECTED_MANDATORY = 'msg_rejected_mandatory'
    MSG_ROOM_NOT_FOUND = 'msg_room_not_found'
    MSG_SLOWMODE = 'msg_slowmode'
    MSG_SUBSONLY = 'msg_subsonly'
    MSG_SUSPENDED = 'msg_suspended'
    MSG_TIMEDOUT = 'msg_timedout'
    MSG_VERIFIED_EMAIL = 'msg_verified_email'
    NO_HELP = 'no_help'
    NO_MODS = 'no_mods'
    NOT_HOSTING = 'not_hosting'
    NO_PERMISSION = 'no_permission'
    R9K_OFF = 'r9k_off'
    R9K_ON = 'r9k_on'
    RAID_ERROR_ALREADY_RAIDING = 'raid_error_already_raiding'
    RAID_ERROR_FORBIDDEN = 'raid_error_forbidden'
    RAID_ERROR_SELF = 'raid_error_self'
    RAISE_ERROR_TOO_MANY_VIEWERS = 'raid_error_too_many_viewers'
    RAID_ERROR_UNEXPECTED = 'raid_error_unexpected'
    RAID_NOTICE_MATURE = 'raid_notice_mature'
    RAID_NOTICE_RESTRICTED_CHAT = 'raid_notice_restricted_chat'
    ROOM_MODS = 'room_mods'
    SLOW_OFF = 'slow_off'
    SLOW_ON = 'slow_on'
    SUBS_OFF = 'subs_off'
    SUBS_ON = 'subs_on'
    TIMEOUT_NO_TIMEOUT = 'timeout_no_timeout'
    TIMEOUT_SUCCESS = 'timeout_success'
    TOS_BAN = 'tos_ban'
    TURBO_ONLY_COLOR = 'turbo_only_color'
    UNBAN_SUCCESS = 'unban_success'
    UNMOD_SUCCESS = 'unmod_success'
    UNRAID_ERROR_NO_ACTIVE_RAID = 'unraid_error_no_active_raid'
    UNRAID_ERROR_UNEXPECTED = 'unraid_error_unexpected'
    UNRAID_SUCCESS = 'unraid_success'
    UNRECOGNIZED_CMD = 'unrecognized_cmd'
    UNSUPPORTED_CHATROOMS_CMD = 'unsupported_chatrooms_cmd'
    UNTIMEOUT_BANNED = 'untimeout_banned'
    UNTIMEOUT_SUCCESS = 'untimeout_success'
    USAGE_BAN = 'usage_ban'
    USAGE_CLEAR = 'usage_clear'
    USAGE_COLOR = 'usage_color'
    USAGE_COMMERICAL = 'usage_commercial'
    USAGE_DISCONNECT = 'usage_disconnect'
    USAGE_EMOTE_ONLY_OFF = 'usage_emote_only_off'
    USAGE_EMOTE_ONLY_ON = 'usage_emote_only_on'
    USAGE_FOLLOWERS_OFF = 'usage_followers_off'
    USAGE_FOLLWERS_ON = 'usage_followers_on'
    USAGE_HELP = 'usage_help'
    USAGE_HOST = 'usage_host'
    UUSAGE_MARKER = 'usage_marker'
    USAGE_ME = 'usage_me'
    USAGE_MOD = 'usage_mod'
    USAGE_MODS = 'usage_mods'
    USAGE_R9K_OFF = 'usage_r9k_off'
    USAGE_R9k_ON = 'usage_r9k_on'
    USAGE_RAID = 'usage_raid'
    USAGE_SLOW_OFF = 'usage_slow_off'
    USAGE_SLOW_ON = 'usage_slow_on'
    USAGE_SUBS_OFF = 'usage_subs_off'
    USAGE_SUBS_ON = 'usage_subs_on'
    USAGE_TIMEOUT = 'usage_timeout'
    USAGE_UNBAN = 'usage_unban	'
    USAGE_UNHOST = 'usage_unhost'
    USAGE_UNMOD = 'usage_unmod'
    USAGE_UNRAID = 'usage_unraid'
    USAGE_UNTIMEOUT = 'usage_untimeout'
    WHISPER_BANNED = 'whisper_banned'
    WHISPER_BANNED_RECIPIENT = 'whisper_banned_recipient'
    WHISPER_INVALID_ARGS = 'whisper_invalid_args'
    WHISPER_INVALID_LOGIN = 'whisper_invalid_login'
    WHISPER_INVALID_SELF = 'whisper_invalid_self'
    WHISPER_LIMIT_PER_MIN = 'whisper_limit_per_min'
    WHISPER_LIMIT_PER_SEC = 'whisper_limit_per_sec'
    WHISPER_RESTRICTED = 'whisper_restricted'
    WHISPER_RESTRICTED_RECIPIENT = 'whisper_restricted_recipient'
