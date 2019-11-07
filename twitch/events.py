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
        async def socket_send(user):
            print(f'Bot username: {user.login}')
            print(f'Bot id: {user.id}')
    """

    DISCONNECT = 'disconnect'
    """
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
    """

    MEMBERSHIP_REQUEST_ACKED = 'membership_request_acked'
    """
    """

    COMMANDS_REQUEST_ACKED = 'commands_request_acked'
    """
    """

    CHAT_ROOMS_REQUEST_ACKED = 'chat_rooms_request_acked'
    """
    """

    GLOBAL_USERSTATE_RECEIVED = 'global_userstate_received'
    """
    """

    ROOMSTATE_RECEIVED = 'roomstate_received'
    """
    """

    UNKNOWN = 'unknown'

    _AUTHENTICATED = '_authenticated'
