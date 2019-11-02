# twitch.py
Python wrapper around the Twitch's Helix and Websocket API. General
design inspired by the [discord.py](https://github.com/Rapptz/discord.py/) library.


[Documentation](https://twitchpi.readthedocs.io/en/latest/)
    - As you can see, there isn't much here yet :) I'm waiting until the library gets more complete/more mature as right now some major redesigns could potentially happen

## Key Features

- Modern user-friendly asynchronous API using [aiohttp](https://aiohttp.readthedocs.io/en/stable/) and [websockets](https://websockets.readthedocs.io/en/stable/)
- Proper rate limit handling
- 100% coverage of the supported **new** Twitch API (**v5 not supported**)
- PEP 8 Compliant

## Simple Example
#### Echoing a streamers chat
```python
import twitch

client = twitch.Client()

AN_AWESOME_STREAMER = '<streamer>'


@client.event()
async def on_connected(user):
    print('We connected yo!')
    print(f'Bot username: {user.login}')
    print(f'Bot id: {user.user_id}')
    print('---------------------\n')
    
    print(f'Joining {AN_AWESOME_STREAMER}s channel...')
    await client.join_channel(AN_AWESOME_STREAMER)


@client.event(name=twitch.Event.MESSAGE)
async def message_listener(message):
    content = message.content

    print(f'[#{message.channel.name}] {message.author.login}: {content}')
    await message.channel.send(content)

client.run('login_name', 'access_token')
```

``login_name``:
- The account name of your bot

``access_token``:
- Token received via one of the [authentication](#authentication) methods. The token can be prefixed with ``oauth:``, but **it doesn't have to be**, the library handles both cases.

## Authentication
You have two ways to get the access token required
1. Use an [existing service](https://twitchapps.com/tmi/) to easily get a token
2. Roll your own with [Twitch's OAuth 2.0 authorization flow](https://dev.twitch.tv/docs/authentication#getting-tokens)
