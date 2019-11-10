class Event:
    """"""

    PINGED = 'ping'

    PONGED = 'pong'

    CONNECTED = 'connected'
    """
    Called when the Websocket client has successfully connected to the server.

    :param user: The twitch user that connected to the server

    .. code-block:: python3

        @client.event(twitch.Event.CONNECTED)
        async def on_connected(user):
            print(f'Bot username: {user.login}')
            print(f'Bot id: {user.id}')
    """

    DISCONNECT = 'disconnect'
    """
    Called when the Websocket client connection to the server is closed

    .. code-block:: python3

        @client.event(twitch.Event.DISCONNECT)
        async def on_disconnected():
            print('Client disconnected')
    """

    SOCKET_SEND = 'socket_send'
    """
    Called when the Websocket client sends a message to the server.

    :param raw_msg: The raw message sent to the server

    
    .. code-block:: python3

        @client.event(twitch.Event.SOCKET_SEND)
        async def socket_send(raw_msg):
            print(raw_msg)
    """

    SOCKET_RECEIVE = 'socket_receive'
    """
    Called when the Websocket client receives a message from the server.

    :param raw_msg: The raw message received from the server


    .. code-block:: python3

        @client.event(twitch.Event.SOCKET_RECEIVE)
        async def socket_recv(raw_msg):
            print(raw_msg)
    """

    MESSAGE = 'message'
    """
    Called when a message is sent in any of the channels your client has joined

    :param message: The message received from the server :class:`Message`


    .. code-block:: python3

        @client.event(twitch.Event.MESSAGE)
        async def message_handler(message):
            print(f'[#{message.channel.name}] '
                  f'{message.author.login}: '
                  f'{message.content}')
    """

    USER_JOIN_CHANNEL = 'user_join_channel'
    """
    """

    USER_LEFT_CHANNEL = 'user_leave_channel'
    """
    """

    LIST_USERS = 'list_users'
    """
    """

    MOD_STATUS_CHANGED = 'mod_status_updated'
    """
    """

    CHAT_CLEARED = 'chat_cleared'
    """
    Called when either all messages in a channel are deleted

    :param channel: The channel where the messages were deleted/cleared

    .. code-block:: python3

        @client.event(twitch.Event.CHAT_CLEARED)
        async def on_clear_chat(channel):
            print(f'The messages in {channel.name}s chat we're just cleared!')
    """

    MESSAGE_CLEARED = 'message_cleared'
    """
    """

    USER_BANNED = 'user_banned'
    """
    """

    USER_PERMANENT_BANNED = 'user_permanent_banned'
    """
    """

    HOST_MODE_CHANGED = 'host_mode_updated'
    """
    """

    CHANNELS_REJOINED = 'channels_rejoined'
    """
    """

    CHANNEL_STATE_CHANGED = 'channel_state_update'
    """
    """

    USER_NOTIFICATION = 'user_noitification'
    """
    """

    USER_STATE_CHANGED = 'user_updated'
    """
    """

    TAG_REQUEST_ACKED = 'tag_request_acked'
    """
    Called after the client has requested the tags capability and the server
    successfully acknowledges/includes the behaviour.

    .. code-block:: python3

        @client.event(twitch.Event.TAG_REQUEST_ACKED)
        async def tags_acked(message):
            print(f'We have the tags capability!')
    """

    MEMBERSHIP_REQUEST_ACKED = 'membership_request_acked'
    """
    Called after the client has requested the membership capability and the
    server successfully acknowledges/includes the behaviour.

    .. code-block:: python3

        @client.event(twitch.Event.MEMBERSHIP_REQUEST_ACKED)
        async def membership_acked(message):
            print(f'We have the membership capability!')
    """

    COMMANDS_REQUEST_ACKED = 'commands_request_acked'
    """
    Called after the client has requested the commands capability and the
    server successfully acknowledges/includes the behaviour.

    .. code-block:: python3

        @client.event(twitch.Event.COMMANDS_REQUEST_ACKED)
        async def commands_acked(message):
            print(f'We have the commands capability!')
    """

    CHAT_ROOMS_REQUEST_ACKED = 'chat_rooms_request_acked'
    """
    Called after the client has requested the chat rooms capability and the
    server successfully acknowledges/includes the behaviour.

    .. code-block:: python3

        @client.event(twitch.Event.CHAT_ROOMS_REQUEST_ACKED)
        async def chat_rooms_acked(message):
            print(f'We have the chat rooms capability!')
    """

    GLOBAL_USERSTATE_RECEIVED = 'global_userstate_received'
    """
    """

    ROOMSTATE_RECEIVED = 'roomstate_received'
    """
    """

    UNKNOWN = 'unknown'

    _AUTHENTICATED = '_authenticated'
