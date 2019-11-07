.. currentmodule:: twitch

API Reference
===============

The following section outlines the API of twitch.py.

Client
-------

.. autoclass:: Client
    :members:
    :undoc-members:
    :exclude-members: clear, close, connect

Capabilities
------------
.. autoclass:: CapabilityConfig
    :members:

.. _events:

Events
------

This section enumerates the different types of events you can choose to listen to with the :class:`Client`.

.. autoattribute:: twitch.Event.SOCKET_SEND
    :annotation:

.. autoattribute:: twitch.Event.SOCKET_RECEIVE
    :annotation:

.. autoattribute:: twitch.Event.CONNECTED
    :annotation:

.. autoattribute:: twitch.Event.DISCONNECT
    :annotation:

.. autoattribute:: twitch.Event.MESSAGE
    :annotation:

.. autoattribute:: twitch.Event.CHAT_CLEARED
    :annotation:

.. autoattribute:: twitch.Event.MESSAGE_CLEARED
    :annotation:

.. autoattribute:: twitch.Event.GLOBAL_USERSTATE_RECEIVED
    :annotation:

.. autoattribute:: twitch.Event.ROOMSTATE_RECEIVED
    :annotation:

.. autoattribute:: twitch.Event.MOD_STATUS_CHANGED
    :annotation:

.. autoattribute:: twitch.Event.USER_JOIN_CHANNEL
    :annotation:

.. autoattribute:: twitch.Event.USER_LEFT_CHANNEL
    :annotation:

.. autoattribute:: twitch.Event.USER_BANNED
    :annotation:

.. autoattribute:: twitch.Event.USER_PERMANENT_BANNED
    :annotation:

.. autoattribute:: twitch.Event.USER_NOTIFICATION
    :annotation:

.. autoattribute:: twitch.Event.USER_STATE_CHANGED
    :annotation:

.. autoattribute:: twitch.Event.LIST_USERS
    :annotation:

.. autoattribute:: twitch.Event.CHANNEL_STATE_CHANGED
    :annotation:

.. autoattribute:: twitch.Event.CHANNELS_REJOINED
    :annotation:

.. autoattribute:: twitch.Event.HOST_MODE_CHANGED
    :annotation:

.. autoattribute:: twitch.Event.TAG_REQUEST_ACKED
    :annotation:

.. autoattribute:: twitch.Event.MEMBERSHIP_REQUEST_ACKED
    :annotation:

.. autoattribute:: twitch.Event.COMMANDS_REQUEST_ACKED
    :annotation:

.. autoattribute:: twitch.Event.CHAT_ROOMS_REQUEST_ACKED
    :annotation:

