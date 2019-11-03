from collections import namedtuple

"""
# heartbeat/keep-alive events
----------------------------
PINGED = 'ping'
PONGED = 'pong'

# request events
----------------------------
TAG_REQUEST_ACKED = 'tag_request_acked'

# connection state events
----------------------------
CONNECTED = 'connected'
DISCONNECT = 'disconnect'

# raw socket events
----------------------------
SOCKET_SEND = 'socket_send'
SOCKET_RECEIVE = 'socket_receive'

# standard events
----------------------------
MESSAGE = 'message'
USER_JOIN_CHANNEL = 'user_join_channel'
USER_LEFT_CHANNEL = 'user_leave_channel'
LIST_USERS = 'list_users'
MOD_STATUS_CHANGED = 'mod_status_updated'
CHAT_CLEARED = 'chat_cleared'
MESSAGE_CLEARED = 'message_cleared'
HOST_MODE_CHANGED = 'host_mode_updated'
CHANNELS_REJOINED = 'channels_rejoined'
CHANNEL_STATE_CHANGED = 'channel_state_update'
USER_NOTIFICATION = 'user_noitification'
USER_STATE_CHANGED = 'user_updated'

# unknown event
----------------------------
# will notify listeners about any undocumented and/or
# error messages from twitch
UNKNOWN = 'unknown'

# reserved events
----------------------------
AUTHENTICATED = '_authenticated'

"""

EventDef = namedtuple('EventDef', 'PINGED '
                                  'PONGED '
                                  'CONNECTED '
                                  'DISCONNECT '
                                  'SOCKET_SEND '
                                  'SOCKET_RECEIVE '
                                  'MESSAGE '
                                  'USER_JOIN_CHANNEL '
                                  'USER_LEFT_CHANNEL '
                                  'LIST_USERS '
                                  'MOD_STATUS_CHANGED '
                                  'CHAT_CLEARED '
                                  'MESSAGE_CLEARED '
                                  'HOST_MODE_CHANGED '
                                  'CHANNELS_REJOINED '
                                  'CHANNEL_STATE_CHANGED '
                                  'USER_NOTIFICATION '
                                  'USER_STATE_CHANGED '
                                  'UNKNOWN '
                                  'TAG_REQUEST_ACKED '
                                  'MEMBERSHIP_REQUEST_ACKED '
                                  'COMMANDS_REQUEST_ACKED '
                                  'CHAT_ROOMS_REQUEST_ACKED '
                                  'AUTHENTICATED')

Event = EventDef(PINGED='ping',
                 PONGED='pong',
                 CONNECTED='connected',
                 DISCONNECT='disconnect',
                 SOCKET_SEND='socket_send',
                 SOCKET_RECEIVE='socket_receive',
                 MESSAGE='message',
                 USER_JOIN_CHANNEL='user_join_channel',
                 USER_LEFT_CHANNEL='user_leave_channel',
                 LIST_USERS='list_users',
                 MOD_STATUS_CHANGED='mod_status_updated',
                 CHAT_CLEARED='chat_cleared',
                 MESSAGE_CLEARED='message_cleared',
                 HOST_MODE_CHANGED='host_mode_updated',
                 CHANNELS_REJOINED='channels_rejoined',
                 CHANNEL_STATE_CHANGED='channel_state_update',
                 USER_NOTIFICATION='user_noitification',
                 USER_STATE_CHANGED='user_updated',
                 TAG_REQUEST_ACKED='tag_request_acked',
                 MEMBERSHIP_REQUEST_ACKED='membership_request_acked',
                 COMMANDS_REQUEST_ACKED='commands_request_acked',
                 CHAT_ROOMS_REQUEST_ACKED='chat_rooms_request_acked',
                 UNKNOWN='unknown',
                 AUTHENTICATED='_authenticated')
