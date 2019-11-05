# twitch.py
Python wrapper around the Twitch's Helix and IRC API. General
design inspired by the [discord.py](https://github.com/Rapptz/discord.py/) library.


[Documentation](https://twitchpi.readthedocs.io/en/latest/)
    - As you can see, there isn't much here yet :) I'm waiting until the library gets more complete/more mature as right now some major redesigns could potentially happen

## Key Features

- Modern user-friendly asynchronous API using [aiohttp](https://aiohttp.readthedocs.io/en/stable/) and [websockets](https://websockets.readthedocs.io/en/stable/)
- Proper HTTP rate limit handling
- 100% coverage of the supported **new** Twitch API (**v5 not supported**)*
- 100% coverage of the supported Chatbot/IRC gateway*
- PEP 8 Compliant
- Built in commands plugin (with optional fuzzy matching)

\* The underlying HTTP and Websocket implementations support 100%, but it may not be exposed in the client or models yet (soon:tm:)

## Simple Examples
A glimpse into the library to get you started!
#### Base Client: Echoing a streamers chat
```python
import twitch

client = twitch.Client()

AN_AWESOME_STREAMER = '<streamer>'


@client.event()
async def on_connected(user):
    print('We connected yo!')
    print(f'Bot username: {user.login}')
    print(f'Bot id: {user.id}')
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
-----------

#### Commands Plugin: Ping-Pong
The commands plugin makes it possible to get a ping-pong bot running **under 10 lines of actual code!!**
```python
from twitch.plugins.commands import Bot

bot = Bot(command_prefix='>')

@bot.event()
async def on_connected(user):
    await bot.join_channel('channel_name')


@bot.command()
async def ping(ctx):
    await ctx.send('pong')

bot.run('login_name', 'access_token')
```
-----------

#### Commands Plugin: Fuzzy Matching command
The commands plugin also provides built in fuzzy matching. This is opt-in,
no fuzzy matching happens by default.

You can pass in a `commands.FuzzyMatch` object to your command definition. In this
example, we are using the simple ratio algorithm with a threshold of 85.

This means if a user types `?meadcount`, if it matches `headcount` by >= 85,
the command will still get invoked.
```python
from twitch.plugins.commands import Bot, FuzzyMatch, FuzzyRatio

bot = Bot(command_prefix='?')

fuzzy = FuzzyMatch(ratio=FuzzyRatio.SIMPLE, threshold=85)

@bot.event()
async def on_connected(user):
    await bot.join_channel('channel_name')

@bot.command(fuzzy_match=fuzzy)
async def headcount(ctx, val: int):
    await ctx.send(f'matched, double the user\'s value is {val * 2}')

bot.run('login_name', 'access_token')
```
-----------

``login_name``:
- The account name of your bot

``access_token``:
- Token received via one of the [authentication](#authentication) methods. The token can be prefixed with ``oauth:``, but **it doesn't have to be**, the library handles both cases.

## Authentication
You have two ways to get the access token required
1. Use an [existing service](https://twitchapps.com/tmi/) to easily get a token
2. Roll your own with [Twitch's OAuth 2.0 authorization flow](https://dev.twitch.tv/docs/authentication#getting-tokens)
