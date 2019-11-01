# twitch.py
Python wrapper around the Twitch's Helix and Websocket API. General
design inspired by the [discord.py](https://github.com/Rapptz/discord.py/) library.

## Key Features

- Modern user-friendly asynchronous API using [aiohttp](https://aiohttp.readthedocs.io/en/stable/) and [websockets](https://websockets.readthedocs.io/en/stable/)
- Proper rate limit handling
- 100% coverage of the supported **new** Twitch API (**v5 not supported**)
- PEP 8 Compliant

## Simple Example
### Client
```python
import twitch

client = twitch.Client()


@client.event()
async def on_connected(user):
    print('We connected yo!')
    print(f'Bot username: {user.login}')
    print(f'Bot id: {user.user_id}')
    print('---------------------\n')


@client.event(name=twitch.Event.SOCKET_SEND)
async def boop(raw_socket_msg):
    print(f'[Client] {raw_socket_msg}')


@client.event(name=twitch.Event.SOCKET_RECEIVE)
async def beep(raw_socket_msg):
    print(f'[Server] {raw_socket_msg}')

client.run('login_name', 'access_token')
```

## Useful Links

- [Documentation](https://twitchpi.readthedocs.io/en/latest/)
    - As you can see, there isn't much here yet :) I'm waiting until the library gets more complete/more mature as right now some major redesigns could potentially happen
- [Get an access token](https://twitchapps.com/tmi/)
