.. currentmodule:: twitch

.. _gettingstarted:

Getting Started
===============

Welcome to the documentation for twitch.py! A Python wrapper around the Twitch's Helix and IRC API.

Requirements
---------------
twitch.py was developed on Python 3.7.4, so that is the guaranteed minimum version supported.
There is no Python 2.7 support, and will most likely not work under Python 3.5 (untested).

.. _installing:

Installing
-----------

TODO (need to publish on PyPi)


Basic Concepts
---------------

twitch.py's main concept is joining twitch channels and listening for events that occur. After you are connected
to the client, you must manually join channels, otherwise you wont receive any useful twitch-related events.

Here's a quick example to show how to join a channel and listen for all the messages sent in the channel:

.. code-block:: python3

    import twitch

    client = twitch.Client()


    @client.event(twitch.Event.CONNECTED)
    async def on_connected(user):
        print(f'Bot username: {user.login}')
        print(f'Bot id: {user.id}')
        await client.join_channel('channel_name')


    @client.event(twitch.Event.MESSAGE)
    async def message_listener(message):
        print(f'[#{message.channel.name}] {message.author.login}: {message.content}')

    client.run('login_name', 'access_token')
